"""
EventBot Application Settings
=============================
Konfigurasi aplikasi yang bisa diakses dari mana saja.
"""

import os
from dotenv import load_dotenv

# Load .env dari folder backend (berlaku di semua working directory)
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_BASE_DIR, ".env"))

# ── Database ──────────────────────────────────────────────
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "eventbot")

# ── Security ──────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "eventbot-dev-secret-key-change-in-production-32x")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# ── App Settings ──────────────────────────────────────────
APP_NAME = "EventBot"
APP_VERSION = "1.0.0"
APP_ENV = os.getenv("APP_ENV", "development")
DEBUG = APP_ENV == "development"

# ── Chatbot Settings ──────────────────────────────────────
CHATBOT_NAME = "EventBot"
CHATBOT_MAX_HISTORY = 50
CHATBOT_FALLBACK_MESSAGE = "Maaf, saya tidak mengerti. Coba ketik 'bantuan' untuk melihat fitur yang tersedia."

# ── File Upload ───────────────────────────────────────────
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/gif", "image/webp"]

# ── Pagination ────────────────────────────────────────────
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# ── Paths ─────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOGS_DIR = os.path.join(BASE_DIR, "logs")