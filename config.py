import os
from pathlib import Path
from dotenv import load_dotenv

# Always load this project's .env before reading configuration, regardless of
# the directory from which Flask/Python was launched.
load_dotenv(Path(__file__).resolve().parent / ".env")
SECRET_KEY = os.getenv("SECRET_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Current Gemini API default; can be overridden in .env when a deployment
# intentionally uses another model available to its API key/project.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))
