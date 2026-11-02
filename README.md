#  NOVA AI - AI Study Planner

An intelligent, AI-powered study planning platform designed to help students organize their academic activities, manage study schedules, track progress, and learn smarter with an AI tutor.

##  Overview

NOVA AI is a web-based study management application developed using Python Flask and SQLite. It combines academic planning tools with Google's Gemini AI to provide students with a more organized and interactive learning experience.

##  Features

* **User Authentication** - Secure registration and login.
* **Personalized Dashboard** - View subjects, tasks, documents, and study progress.
* **Subject Management** - Add and manage academic subjects.
* **Task Management** - Organize assignments and academic tasks.
* **Smart Study Timetable** - Generate study schedules based on available hours and subject priorities.
* **AI Study Assistant** - Interact with Gemini AI for academic explanations and learning support.
* **PDF Document Management** - Upload, extract, and manage study materials.
* **PDF-Based AI Assistance** - Ask questions using uploaded study documents as context.
* **Progress Tracking** - Monitor completed tasks and study activity.

## ðŸ› ï¸ Technology Stack

| Category                | Technologies                     |
| ----------------------- | -------------------------------- |
| Backend                 | Python, Flask                    |
| Frontend                | HTML, CSS, JavaScript, Bootstrap |
| Database                | SQLite                           |
| Artificial Intelligence | Google Gemini API                |
| PDF Processing          | PyPDF                            |
| PDF Generation          | ReportLab                        |
| Testing                 | Pytest                           |

#Project Structure
AI_Study_Planner/
|
|-- app.py
|-- config.py
|-- database.py
|-- requirements.txt
|-- requirements.production.txt
|-- .env.example
|-- .gitignore
|
|-- templates/
|   |-- index.html
|   |-- auth.html
|   |-- base.html
|   |-- dashboard.html
|   |-- subjects.html
|   |-- subject_form.html
|   |-- tasks.html
|   |-- timetable.html
|   |-- documents.html
|   |-- chatbot.html
|
|-- static/
|   |-- css/
|   |-- js/
|
|-- utils/
|   |-- pdf_export.py
|   |-- priority.py
|   |-- scheduler.py
|
|-- tests/
    |-- test_scheduler.py
## âš™ï¸ Installation and Setup

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd AI_Study_Planner
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the environment

Windows:

```powershell
venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

Create a `.env` file using `.env.example` as a template.

Configure the following:

```env
SECRET_KEY=your_secret_key
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=your_gemini_model
MAX_UPLOAD_BYTES=10485760
FLASK_DEBUG=1
```

Replace the placeholder values with your own configuration.

**Important:** Never upload your `.env` file or expose your API keys publicly.

### 6. Run the application

```bash
python app.py
```

Open your browser:

```text
http://127.0.0.1:5000
```

## ðŸ§ª Run Tests

Execute the test suite:

```bash
python -m pytest -q
```

## ðŸ” Security and Privacy

* Environment variables are used for sensitive configuration.
* User-specific academic records are associated with authenticated accounts.
* Uploaded documents are stored outside the public static directory.
* Local databases, environment files, and uploaded files are excluded from Git tracking.

## ðŸ“¸ Screenshots

Screenshots of the NOVA AI application will be added here.

## ðŸŽ¯ Project Objective

The objective of NOVA AI is to combine intelligent academic assistance with structured study planning, helping students manage their learning activities more effectively.

## ðŸ‘©â€ðŸ’» Developer

Developed as an AI-powered academic productivity project.

---

**NOVA AI - Plan Smarter. Learn Better. Achieve More.** 


