"""
Sidebar Component
=================
Sidebar navigasi utama EventBot dengan menu berbasis role.
"""

import streamlit as st
from typing import Optional
from utils.session_manager import SessionManager
from utils.formatters import avatar_initials, format_status_badge

_MENU_GUEST = [
    {"icon": "🏠", "label": "Beranda",       "page": "Landing"},
    {"icon": "💬", "label": "Chatbot",        "page": "Chatbot"},
    {"icon": "📋", "label": "Jelajahi Event", "page": "Event_Explorer"},
    {"icon": "ℹ️", "label": "Tentang",        "page": "About"},
]

_MENU_PARTICIPANT = [
    {"icon": "🏠", "label": "Beranda",         "page": "Landing"},
    {"icon": "💬", "label": "Chatbot",          "page": "Chatbot"},
    {"icon": "📋", "label": "Jelajahi Event",   "page": "Event_Explorer"},
    {"icon": "👤", "label": "Profil Saya",      "page": "Profil_saya"},
    {"icon": "ℹ️", "label": "Tentang",          "page": "About"},
]

_MENU_ADMIN = [
    {"icon": "📊", "label": "Dashboard",      "page": "Dashboard_admin",  "div": False},
    {"icon": "💬", "label": "Chatbot",         "page": "Chatbot",          "div": False},
    {"icon": "📋", "label": "Jelajahi Event",  "page": "Event_Explorer",   "div": False},
    {"icon": "👥", "label": "Manajemen User",  "page": "Manajemen_User",   "div": True},
    {"icon": "🎪", "label": "Manajemen Event", "page": "Manajemen_Event",  "div": False},
    {"icon": "🎫", "label": "Manajemen Tiket", "page": "Manajemen_Ticket", "div": False},
    {"icon": "📚", "label": "Knowledge Base",  "page": "Knowledge_Base",   "div": True},
    {"icon": "⚙️", "label": "Pengaturan",      "page": "Pengaturan",       "div": False},
    {"icon": "👤", "label": "Profil Saya",     "page": "Profil_saya",      "div": True},
    {"icon": "ℹ️", "label": "Tentang",         "page": "About",            "div": False},
]


def render_sidebar(current_page: str = "") -> Optional[str]:
    """Render sidebar navigasi EventBot."""
    role         = SessionManager.get_role()
    user         = SessionManager.get_user()
    is_logged_in = SessionManager.is_logged_in()
    selected_page = None

    with st.sidebar:
        # ── Brand ─────────────────────────────────────────
        st.markdown(
            '<div style="text-align:center;padding:1rem 0 1.5rem;border-bottom:1px solid rgba(255,255,255,0.08);margin-bottom:1rem;">'
            '<div style="font-size:2.5rem;margin-bottom:0.25rem;">🎪</div>'
            '<div style="font-size:1.4rem;font-weight:800;background:linear-gradient(135deg,#7C3AED,#10B981);'
            '-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">EventBot</div>'
            '<div style="font-size:0.75rem;color:#6B7280;margin-top:0.2rem;">Chatbot Manajemen Event</div>'
            "</div>",
            unsafe_allow_html=True,
        )

        # ── User Profile Card ──────────────────────────────
        if is_logged_in and user:
            initials    = avatar_initials(user.get("name", ""))
            role_label  = format_status_badge(role, with_emoji=True)
            st.markdown(
                '<div style="background:rgba(124,58,237,0.08);border:1px solid rgba(124,58,237,0.2);'
                'border-radius:12px;padding:0.875rem;margin-bottom:1.25rem;display:flex;align-items:center;gap:0.75rem;">'
                '<div style="width:40px;height:40px;border-radius:50%;background:linear-gradient(135deg,#7C3AED,#4F46E5);'
                'display:flex;align-items:center;justify-content:center;font-weight:700;color:white;font-size:0.875rem;flex-shrink:0;">'
                + initials +
                '</div><div>'
                '<div style="font-weight:600;color:#F8F9FA;font-size:0.9rem;line-height:1.3;">'
                + user.get("name", "User") +
                '</div><div style="font-size:0.75rem;color:#ADB5BD;margin-top:0.1rem;">'
                + role_label +
                "</div></div></div>",
                unsafe_allow_html=True,
            )

        # ── Pilih menu ──────────────────────────────────────
        if role == "admin":
            menu = _MENU_ADMIN
        elif is_logged_in:
            menu = _MENU_PARTICIPANT
        else:
            menu = _MENU_GUEST

        st.markdown("**Menu**")
        for item in menu:
            if item.get("div"):
                st.markdown("---")
            is_active = item["page"] == current_page
            label     = item["icon"] + " " + item["label"]
            if st.button(
                label,
                key="sidebar_" + item["page"],
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                selected_page = item["page"]
                st.session_state["current_page"] = item["page"]
                st.rerun()

        # ── Auth Button ───────────────────────────────────
        if is_logged_in:
            if st.button("🚪 Keluar", key="sidebar_logout", use_container_width=True):
                SessionManager.logout()
                st.session_state["current_page"] = "Landing"
                st.rerun()
        else:
            st.markdown("---")
            if st.button("🔐 Login / Daftar", key="sidebar_login", use_container_width=True, type="primary"):
                st.session_state["current_page"] = "Login_register"
                st.rerun()

        # ── Footer kecil ──────────────────────────────────
        st.markdown(
            '<div style="margin-top:2rem;text-align:center;font-size:0.7rem;color:#374151;">EventBot v1.0.0</div>',
            unsafe_allow_html=True,
        )

    return selected_page
