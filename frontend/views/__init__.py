"""
Views Package
=============
Semua halaman/page EventBot Streamlit.
Setiap modul memiliki fungsi render() sebagai entry point.
"""

# Import semua view modules agar bisa di-load dinamis dari app.py
from . import (
    Landing,
    Chatbot,
    Login_register,
    Event_Explorer,
    Dashboard_admin,
    Manajemen_User,
    Manajemen_Event,
    Manajemen_Ticket,
    Knowledge_Base,
    Profil_saya,
    Pengaturan,
    About,
)

# Registry: nama halaman → modul
PAGE_REGISTRY = {
    "Landing":          Landing,
    "Chatbot":          Chatbot,
    "Login_register":   Login_register,
    "Event_Explorer":   Event_Explorer,
    "Dashboard_admin":  Dashboard_admin,
    "Manajemen_User":   Manajemen_User,
    "Manajemen_Event":  Manajemen_Event,
    "Manajemen_Ticket": Manajemen_Ticket,
    "Knowledge_Base":   Knowledge_Base,
    "Profil_saya":      Profil_saya,
    "Pengaturan":       Pengaturan,
    "About":            About,
}

__all__ = list(PAGE_REGISTRY.keys()) + ["PAGE_REGISTRY"]
