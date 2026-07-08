"""
EventBot - Streamlit Cloud Entry Point
=======================================
File ini dibutuhkan Streamlit Cloud sebagai entry point utama.
Letaknya di root folder, bukan di dalam frontend/.

Cara deploy:
    - Main file path: streamlit_app.py
    - Secrets: BACKEND_URL = "https://your-backend.railway.app"
"""

import sys
import os

# ── Setup paths ──────────────────────────────────────────
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")

# Add frontend directory to Python path agar semua import dari frontend/ bekerja
if FRONTEND_DIR not in sys.path:
    sys.path.insert(0, FRONTEND_DIR)

# ── Baca Streamlit Secrets ───────────────────────────────
# Inject secrets ke os.environ SEBELUM komponen lain di-import
# Ini diperlukan agar api_client.py bisa baca os.getenv("BACKEND_URL")
try:
    import streamlit as st
    for key, value in st.secrets.items():
        if isinstance(value, str):
            os.environ[key] = value
except Exception:
    # Lokal tanpa secrets.toml — gunakan nilai default dari api_client.py
    pass

# ── Pindah working directory ke frontend ─────────────────
# Agar path relative (styles/, assets/) tetap berfungsi
os.chdir(FRONTEND_DIR)

# ── Jalankan aplikasi frontend utama ─────────────────────
# Import komponen streamlit setelah path & env sudah di-setup
import app  # noqa: E402 — ini mengimport frontend/app.py
