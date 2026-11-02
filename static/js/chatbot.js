const box=document.querySelector('#box'), input=document.querySelector('#message'), send=document.querySelector('#send');
function add(text,role){const x=document.createElement('div');x.className='message '+role;const b=document.createElement('div');b.textContent=text;x.appendChild(b);box.appendChild(x);box.scrollTop=box.scrollHeight;return x}
async function ask(){const message=input.value.trim();if(!message)return;add(message,'user');input.value='';send.disabled=true;const pending=add('NOVA is thinking…','assistant');try{const r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message,document_id:document.querySelector('#doc').value||null})});const d=await r.json();pending.remove();add(d.reply||d.error||'Unable to respond.','assistant')}catch(e){pending.remove();add('Network error. Please try again.','assistant')}finally{send.disabled=false;input.focus()}}
send.addEventListener('click',ask);input.addEventListener('keydown',e=>{if(e.key==='Enter')ask()});document.querySelector('#clear').addEventListener('click',async()=>{await fetch('/chat/clear',{method:'POST'});box.innerHTML='';add('Chat cleared. What would you like to study?','assistant')});

document.addEventListener("DOMContentLoaded", () => {
    const box = document.getElementById("box");
    const input = document.getElementById("message");
    const send = document.getElementById("send");
    const clear = document.getElementById("clear");
    const doc = document.getElementById("doc");

    if (!box || !input || !send || !clear) {
        console.error("NOVA chatbot elements are missing.");
        return;
    }

    let sending = false;

    function addMessage(role, content) {
        const message = document.createElement("div");
        message.className = `message ${role}`;

        const text = document.createElement("div");
        text.textContent = content;

        message.appendChild(text);
        box.appendChild(message);
        box.scrollTop = box.scrollHeight;

        return message;
    }

    function setLoading(loading) {
        sending = loading;
        send.disabled = loading;
        input.disabled = loading;
        send.textContent = loading ? "Thinking..." : "Send";
    }

    async function sendMessage() {
        const message = input.value.trim();

        if (!message || sending) return;

        addMessage("user", message);
        input.value = "";

        const loadingMessage = addMessage(
            "assistant",
            "NOVA is thinking..."
        );

        setLoading(true);

        try {
            const response = await fetch("/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                body: JSON.stringify({
                    message: message,
                    document_id: doc ? (doc.value || null) : null
                })
            });

            const data = await response.json();

            loadingMessage.remove();

            if (!response.ok) {
                addMessage(
                    "assistant",
                    data.error || "Something went wrong. Please try again."
                );
                return;
            }

            addMessage(
                "assistant",
                data.reply || "I couldn't generate a response. Please try again."
            );

        } catch (error) {
            loadingMessage.remove();

            addMessage(
                "assistant",
                "Connection error. Please check your internet connection and try again."
            );

            console.error("NOVA Chat Error:", error);

        } finally {
            setLoading(false);
            input.focus();
        }
    }

    send.addEventListener("click", sendMessage);

    input.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    });

    clear.addEventListener("click", async () => {
        if (sending) return;

        const confirmed = window.confirm(
            "Are you sure you want to clear your chat history?"
        );

        if (!confirmed) return;

        clear.disabled = true;

        try {
            const response = await fetch("/chat/clear", {
                method: "POST",
                headers: {
                    "Accept": "application/json"
                }
            });

            const data = await response.json();

            if (!response.ok || !data.ok) {
                throw new Error(data.error || "Unable to clear chat.");
            }

            box.replaceChildren();

            addMessage(
                "assistant",
                "Hi! I'm NOVA, your AI study tutor. Ask me anything about your studies!"
            );

        } catch (error) {
            alert(error.message || "Unable to clear chat. Please try again.");
            console.error("NOVA Clear Chat Error:", error);

        } finally {
            clear.disabled = false;
        }
    });

    box.scrollTop = box.scrollHeight;
    input.focus();
});
