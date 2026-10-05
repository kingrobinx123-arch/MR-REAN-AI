import os
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = os.getenv("DATA_DIR", "/app/data")
WORKSPACE_DIR = os.path.join(DATA_DIR, "workspace")
DB_PATH = os.path.join(DATA_DIR, "mr_rean_v3.sqlite3")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
MANUS_API_KEY = os.getenv("MANUS_API_KEY", "").strip()

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "").strip()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
AI_PROVIDER = os.getenv("AI_PROVIDER", "auto").strip().lower()
DAILY_CREDITS = int(os.getenv("DAILY_CREDITS", "20"))
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "25"))
