import sys
import os

# Setup paths
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")

if FRONTEND_DIR not in sys.path:
    sys.path.insert(0, FRONTEND_DIR)

# Inject secrets ke environment SEBELUM import streamlit apapun
try:
    import streamlit as st
    for key, value in st.secrets.items():
        if isinstance(value, str):
            os.environ[key] = value
except Exception:
    pass

# Pindah working directory ke frontend
os.chdir(FRONTEND_DIR)

# Jalankan app
import app  # noqa: E402
