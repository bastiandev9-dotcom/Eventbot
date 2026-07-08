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

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")

if FRONTEND_DIR not in sys.path:
    sys.path.insert(0, FRONTEND_DIR)

try:
    import streamlit as st
    for key, value in st.secrets.items():
        if isinstance(value, str):
            os.environ[key] = value
except Exception:
    pass

os.chdir(FRONTEND_DIR)

import app  # noqa: E402
