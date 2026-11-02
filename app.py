import os, sqlite3, uuid
from datetime import date
from functools import wraps
from io import BytesIO
from flask import Flask, abort, flash, jsonify, redirect, render_template, request, send_file, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from config import GEMINI_API_KEY, GEMINI_MODEL, MAX_UPLOAD_BYTES, SECRET_KEY
from database import DB_PATH, init_db
from utils.priority import calculate_priorities
from utils.scheduler import generate_timetable
from utils.pdf_export import export_timetable_pdf
try:
    from google import genai
except ImportError: genai = None
# pypdf is the actively maintained PDF reader.  PyPDF2 remains a compatible
# fallback for installations that were created before the package rename.
try:
    from pypdf import PdfReader
    PDF_READER_PACKAGE = "pypdf"
except ImportError:
    try:
        from PyPDF2 import PdfReader
        PDF_READER_PACKAGE = "PyPDF2"
    except ImportError:
        PdfReader = None
        PDF_READER_PACKAGE = None

app = Flask(__name__)
app.config.update(SECRET_KEY=SECRET_KEY or os.urandom(32), MAX_CONTENT_LENGTH=MAX_UPLOAD_BYTES, UPLOAD_FOLDER=os.path.join(app.root_path,"uploads"), SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")
os.makedirs(app.config["UPLOAD_FOLDER"],exist_ok=True); init_db()
ai_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY and genai else None


def ai_configuration_error():
    if not genai:
        return "Google GenAI SDK is unavailable. Run: python -m pip install -r requirements.txt, then restart."
    if not GEMINI_API_KEY:
        return "AI is not configured. Add GEMINI_API_KEY=your_key to the project .env file, then restart the server."
    return None


def generate_ai(prompt):
    """Call Gemini only from the server; callers receive no key details."""
    problem = ai_configuration_error()
    if problem:
        return None, problem, 503
    try:
        response = ai_client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
        text = (response.text or "").strip()
        if not text:
            return None, "Gemini returned no text for this request. Please try again.", 502
        return text, None, 200
    except Exception:
        return None, "AI provider request failed. Verify your Gemini API key, model access, and internet connection.", 502

def db():
    conn=sqlite3.connect(DB_PATH); conn.row_factory=sqlite3.Row; conn.execute("PRAGMA foreign_keys=ON"); return conn
def login_required(view):
    @wraps(view)
    def wrapped(*args,**kwargs):
        if not session.get("user_id"): flash("Please sign in to continue.","warning"); return redirect(url_for("login"))
        return view(*args,**kwargs)
    return wrapped
def uid(): return int(session["user_id"])
def subjects_for(conn,user_id): return [dict(r) for r in conn.execute("SELECT * FROM subjects WHERE user_id=? ORDER BY exam_date",(user_id,))]
@app.context_processor
def inject_user(): return {"current_user":{"id":session.get("user_id"),"name":session.get("username")}}

@app.route("/")
def home(): return redirect(url_for("dashboard")) if session.get("user_id") else render_template("index.html")
@app.route("/register",methods=["GET","POST"])
def register():
    if request.method=="POST":
        email=request.form.get("email","").strip().lower(); name=request.form.get("username","").strip(); password=request.form.get("password","")
        if not name or "@" not in email or len(password)<8: flash("Use a name, valid email, and a password of at least 8 characters.","danger")
        else:
            conn=db()
            try:
                cur=conn.execute("INSERT INTO users(email,username,password_hash) VALUES(?,?,?)",(email,name,generate_password_hash(password))); conn.execute("INSERT INTO preferences(user_id) VALUES(?)",(cur.lastrowid,));conn.commit();flash("Account created. Please sign in.","success");return redirect(url_for("login"))
            except sqlite3.IntegrityError: flash("That email is already registered.","danger")
            finally: conn.close()
    return render_template("auth.html",mode="register")
@app.route("/login",methods=["GET","POST"])
def login():
    if request.method=="POST":
        conn=db(); user=conn.execute("SELECT * FROM users WHERE email=?",(request.form.get("email","").strip().lower(),)).fetchone();conn.close()
        if user and check_password_hash(user["password_hash"],request.form.get("password","")):
            session.clear();session.update(user_id=user["id"],username=user["username"]);return redirect(url_for("dashboard"))
        flash("Invalid email or password.","danger")
    return render_template("auth.html",mode="login")
@app.post("/logout")
@login_required
def logout(): session.clear();return redirect(url_for("home"))
@app.route("/dashboard")
@login_required
def dashboard():
    conn=db(); subs=subjects_for(conn,uid()); counts=conn.execute("SELECT COUNT(*) total,COALESCE(SUM(completed),0) done FROM tasks WHERE user_id=?",(uid(),)).fetchone(); weekly=conn.execute("SELECT COALESCE(SUM(hours),0) FROM study_sessions WHERE user_id=? AND session_date>=date('now','-6 days')",(uid(),)).fetchone()[0]; docs=conn.execute("SELECT * FROM documents WHERE user_id=? ORDER BY created_at DESC LIMIT 5",(uid(),)).fetchall(); tasks=conn.execute("SELECT t.*,s.subject FROM tasks t LEFT JOIN subjects s ON s.id=t.subject_id WHERE t.user_id=? ORDER BY completed,due_date LIMIT 8",(uid(),)).fetchall();conn.close(); total=counts["total"];done=counts["done"]
    return render_template("dashboard.html",subjects=subs,tasks=tasks,documents=docs,priorities=calculate_priorities(subs),total_tasks=total,completed_tasks=done,pending_tasks=total-done,weekly_hours=weekly,progress=round(done/total*100) if total else 0,upcoming=[s for s in subs if s["exam_date"]>=str(date.today())][:5])
@app.route("/subjects")
@login_required
def subjects():
    conn=db();subs=subjects_for(conn,uid());conn.close();return render_template("subjects.html",subjects=subs)
@app.route("/subjects/new",methods=["GET","POST"])
@login_required
def add_subject():
    if request.method=="POST":
        name=request.form.get("subject","").strip(); exam=request.form.get("exam_date",""); diff=request.form.get("difficulty","Medium")
        try: hours=max(1,int(request.form.get("study_hours",1)))
        except ValueError: hours=0
        if not name or not exam or not hours: flash("Complete every field.","danger")
        else:
            conn=db();conn.execute("INSERT INTO subjects(user_id,subject,exam_date,difficulty,study_hours) VALUES(?,?,?,?,?)",(uid(),name,exam,diff,hours));conn.commit();conn.close();flash("Subject added.","success");return redirect(url_for("subjects"))
    return render_template("subject_form.html")
@app.post("/subjects/<int:subject_id>/delete")
@login_required
def delete_subject(subject_id):
    conn=db();cur=conn.execute("DELETE FROM subjects WHERE id=? AND user_id=?",(subject_id,uid()));conn.commit();conn.close()
    if not cur.rowcount: abort(404)
    flash("Subject deleted.","success");return redirect(url_for("subjects"))
@app.route("/tasks",methods=["GET","POST"])
@login_required
def tasks():
    conn=db()
    if request.method=="POST":
        title=request.form.get("title","").strip(); sid=request.form.get("subject_id") or None
        if title:
            if sid and not conn.execute("SELECT 1 FROM subjects WHERE id=? AND user_id=?",(sid,uid())).fetchone(): abort(403)
            conn.execute("INSERT INTO tasks(user_id,subject_id,title,topic,due_date,priority) VALUES(?,?,?,?,?,?)",(uid(),sid,title,request.form.get("topic",""),request.form.get("due_date") or None,request.form.get("priority","Medium")));conn.commit();flash("Task added.","success")
        conn.close();return redirect(url_for("tasks"))
    rows=conn.execute("SELECT t.*,s.subject FROM tasks t LEFT JOIN subjects s ON s.id=t.subject_id WHERE t.user_id=? ORDER BY completed,due_date",(uid(),)).fetchall();subs=subjects_for(conn,uid());conn.close();return render_template("tasks.html",tasks=rows,subjects=subs)
@app.post("/tasks/<int:task_id>/toggle")
@login_required
def toggle_task(task_id):
    conn=db();cur=conn.execute("UPDATE tasks SET completed=1-completed WHERE id=? AND user_id=?",(task_id,uid()));conn.commit();conn.close()
    if not cur.rowcount: abort(404)
    return redirect(url_for("tasks"))
@app.route("/planner",methods=["GET","POST"])
@login_required
def planner():
    try: hours=max(1,min(12,int(request.values.get("available_hours",4))));days=max(3,min(30,int(request.values.get("days",7))))
    except ValueError: hours,days=4,7
    conn=db();subs=subjects_for(conn,uid());conn.close();return render_template("timetable.html",timetable=generate_timetable(subs,hours,days),priorities=calculate_priorities(subs),available_hours=hours,days=days)
@app.post("/progress")
@login_required
def log_progress():
    sid=request.form.get("subject_id");
    try: hours=float(request.form.get("hours",0))
    except ValueError: abort(400)
    conn=db()
    if hours<=0 or not conn.execute("SELECT 1 FROM subjects WHERE id=? AND user_id=?",(sid,uid())).fetchone():conn.close();abort(403)
    conn.execute("INSERT INTO study_sessions(user_id,subject_id,session_date,hours,note) VALUES(?,?,date('now'),?,?)",(uid(),sid,hours,request.form.get("note","")));conn.commit();conn.close();flash("Study session saved.","success");return redirect(url_for("dashboard"))
@app.route("/assistant")
@login_required
def assistant():
    conn=db();hist=conn.execute("SELECT role,content FROM chat_messages WHERE user_id=? ORDER BY id DESC LIMIT 30",(uid(),)).fetchall()[::-1];docs=conn.execute("SELECT id,original_name FROM documents WHERE user_id=?",(uid(),)).fetchall();conn.close();return render_template("chatbot.html",history=hist,documents=docs,ai_ready=not ai_configuration_error())
@app.post("/chat")
@login_required
def chat():
    data=request.get_json(silent=True) or {};msg=str(data.get("message","")).strip();doc_id=data.get("document_id")
    if not msg:return jsonify(error="Message is required."),400
    conn=db();context=""
    if doc_id:
        doc=conn.execute("SELECT text_content,original_name FROM documents WHERE id=? AND user_id=?",(doc_id,uid())).fetchone()
        if not doc:conn.close();return jsonify(error="Document not found."),404
        context=f"\nDocument {doc['original_name']} excerpt:\n{(doc['text_content'] or '')[:12000]}\n"
    old=conn.execute("SELECT role,content FROM chat_messages WHERE user_id=? ORDER BY id DESC LIMIT 10",(uid(),)).fetchall()[::-1];prompt="You are NOVA, a concise and encouraging academic tutor. Explain simply and make exam advice actionable."+context+"\n"+"\n".join(f"{r['role']}: {r['content']}" for r in old)+f"\nuser: {msg}\nassistant:"
    reply,error,status=generate_ai(prompt)
    if error:conn.close();return jsonify(error=error),status
    conn.execute("INSERT INTO chat_messages(user_id,role,content) VALUES(?,?,?)",(uid(),"user",msg));conn.execute("INSERT INTO chat_messages(user_id,role,content) VALUES(?,?,?)",(uid(),"assistant",reply));conn.commit();conn.close();return jsonify(reply=reply)
@app.post("/ai/study-plan")
@login_required
def ai_study_plan():
    conn=db(); subs=subjects_for(conn,uid()); tasks=conn.execute("SELECT title,due_date,priority,completed FROM tasks WHERE user_id=? ORDER BY completed,due_date",(uid(),)).fetchall();conn.close()
    prompt=("Create a practical 7-day personalised study plan. Use a concise daily checklist, balance difficult and urgent work, and include revision. "
            f"Subjects: {subs}. Tasks: {[dict(row) for row in tasks]}. Student request: {str((request.get_json(silent=True) or {}).get('goal','')).strip()}")
    reply,error,status=generate_ai(prompt)
    return (jsonify(error=error),status) if error else jsonify(reply=reply)
@app.post("/ai/question-paper")
@login_required
def ai_question_paper():
    data=request.get_json(silent=True) or {}; subject=str(data.get("subject","")).strip(); document_id=data.get("document_id"); context=""
    conn=db()
    if document_id:
        doc=conn.execute("SELECT text_content,original_name FROM documents WHERE id=? AND user_id=?",(document_id,uid())).fetchone()
        if not doc:conn.close();return jsonify(error="Document not found."),404
        context=f" Use only this material where applicable ({doc['original_name']}): {(doc['text_content'] or '')[:12000]}"
    conn.close()
    if not subject:return jsonify(error="A subject is required."),400
    reply,error,status=generate_ai(f"Create an exam-oriented question paper for {subject}. Include a mix of short, long, and application questions plus a compact answer key.{context}")
    return (jsonify(error=error),status) if error else jsonify(reply=reply)
@app.post("/chat/clear")
@login_required
def clear_chat():
    conn=db();conn.execute("DELETE FROM chat_messages WHERE user_id=?",(uid(),));conn.commit();conn.close();return jsonify(ok=True)
@app.route("/documents",methods=["GET","POST"])
@login_required
def documents():
    if request.method=="POST":
        file=request.files.get("pdf")
        if not file or not file.filename or not file.filename.lower().endswith(".pdf"):flash("Upload a PDF file.","danger");return redirect(url_for("documents"))
        data=file.read()
        if len(data)>MAX_UPLOAD_BYTES or not data.startswith(b"%PDF"):flash("Invalid PDF or file exceeds the size limit.","danger");return redirect(url_for("documents"))
        if not PdfReader:flash("PDF processing is unavailable. Install pypdf with: python -m pip install -r requirements.txt, then restart the server.","danger");return redirect(url_for("documents"))
        try:
            reader=PdfReader(BytesIO(data))
            text="\n".join((page.extract_text() or "") for page in reader.pages).strip()[:200000]
            if not text: flash("This PDF contains no selectable text (it may be scanned). Upload a text-based PDF or add OCR support.","warning"); return redirect(url_for("documents"))
        except Exception:
            flash("That PDF is damaged, encrypted, or could not be read.","danger");return redirect(url_for("documents"))
        storage=uuid.uuid4().hex+".pdf";open(os.path.join(app.config["UPLOAD_FOLDER"],storage),"wb").write(data);conn=db();conn.execute("INSERT INTO documents(user_id,original_name,storage_name,text_content,size_bytes) VALUES(?,?,?,?,?)",(uid(),secure_filename(file.filename),storage,text,len(data)));conn.commit();conn.close();flash("PDF uploaded and indexed for NOVA.","success");return redirect(url_for("documents"))
    conn=db();docs=conn.execute("SELECT * FROM documents WHERE user_id=? ORDER BY created_at DESC",(uid(),)).fetchall();conn.close();return render_template("documents.html",documents=docs,max_mb=MAX_UPLOAD_BYTES//1024//1024)
def owned_document(did):
    conn=db();doc=conn.execute("SELECT * FROM documents WHERE id=? AND user_id=?",(did,uid())).fetchone();conn.close()
    if not doc:abort(404)
    return doc
@app.get("/documents/<int:did>/download")
@login_required
def download_document(did):
    doc=owned_document(did);return send_file(os.path.join(app.config["UPLOAD_FOLDER"],doc["storage_name"]),as_attachment=True,download_name=doc["original_name"])
@app.post("/documents/<int:did>/delete")
@login_required
def delete_document(did):
    doc=owned_document(did);path=os.path.join(app.config["UPLOAD_FOLDER"],doc["storage_name"]);conn=db();conn.execute("DELETE FROM documents WHERE id=? AND user_id=?",(did,uid()));conn.commit();conn.close()
    if os.path.isfile(path):os.remove(path)
    flash("Document deleted.","success");return redirect(url_for("documents"))
@app.get("/export_pdf")
@login_required
def export_pdf():
    conn=db();subs=subjects_for(conn,uid());conn.close();tt=generate_timetable(subs,int(request.args.get("available_hours",4)),int(request.args.get("days",7)));pdf=export_timetable_pdf(tt,subs);return send_file(BytesIO(pdf.getvalue()),as_attachment=True,download_name="NOVA_Study_Timetable.pdf",mimetype="application/pdf")
@app.errorhandler(413)
def too_large(e):flash("File is too large.","danger");return redirect(url_for("documents"))
if __name__=="__main__":app.run(debug=os.getenv("FLASK_DEBUG")=="1")
