"""
Navbar Component
================
Top navigation bar dengan logo, menu, auth status, dan notifikasi.
"""

import streamlit as st
from typing import Optional
from utils.session_manager import SessionManager
from utils.formatters import avatar_initials

_NAVBAR_CSS = """
<style>
.eventbot-navbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem 2rem;
    background: rgba(15, 15, 26, 0.85);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-bottom: 1px solid rgba(255,255,255,0.08);
    position: sticky;
    top: 0;
    z-index: 999;
    margin: -1rem -1rem 1.5rem -1rem;
}
.nav-brand {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 1.25rem;
    font-weight: 800;
    color: #F8F9FA;
    text-decoration: none;
}
.nav-brand-name {
    background: linear-gradient(135deg, #7C3AED, #10B981);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.nav-links { display: flex; align-items: center; gap: 0.25rem; }
.nav-link {
    padding: 0.4rem 0.875rem;
    border-radius: 8px;
    color: #ADB5BD;
    text-decoration: none;
    font-size: 0.9rem;
    font-weight: 500;
    transition: all 0.2s ease;
}
.nav-link:hover { color: #F8F9FA; background: rgba(255,255,255,0.05); }
.nav-link.active { color: #7C3AED; background: rgba(124,58,237,0.1); }
.nav-user { display: flex; align-items: center; gap: 0.75rem; }
.nav-notif { position: relative; font-size: 1.1rem; cursor: pointer; }
.notif-badge {
    position: absolute; top: -6px; right: -6px;
    background: #EF4444; color: white;
    font-size: 0.65rem; font-weight: 700;
    width: 16px; height: 16px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
}
.nav-username { color: #F8F9FA; font-weight: 600; font-size: 0.875rem; }
.nav-auth-btns { display: flex; gap: 0.5rem; align-items: center; }
.nav-btn-ghost {
    padding: 0.375rem 0.875rem; border-radius: 8px;
    border: 1px solid rgba(255,255,255,0.15);
    color: #ADB5BD; text-decoration: none;
    font-size: 0.875rem; font-weight: 500; transition: all 0.2s ease;
}
.nav-btn-ghost:hover { color: #F8F9FA; border-color: rgba(255,255,255,0.3); }
.nav-btn-primary {
    padding: 0.375rem 0.875rem; border-radius: 8px;
    background: linear-gradient(135deg, #7C3AED, #4F46E5);
    color: white; text-decoration: none;
    font-size: 0.875rem; font-weight: 600; transition: all 0.2s ease;
}
.nav-btn-primary:hover { opacity: 0.85; transform: translateY(-1px); }
.nav-avatar {
    width: 32px; height: 32px; border-radius: 50%;
    background: linear-gradient(135deg, #7C3AED, #4F46E5);
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; color: white; font-size: 0.75rem;
}
</style>
"""


def render_navbar(current_page: str = "") -> None:
    """Render top navigation bar EventBot."""
    is_logged_in = SessionManager.is_logged_in()
    user = SessionManager.get_user()
    role = SessionManager.get_role()
    unread = SessionManager.get_unread_count()

    nav_items = [
        {"label": "🏠 Home",    "page": "Landing"},
        {"label": "💬 Chatbot", "page": "Chatbot"},
        {"label": "📋 Event",   "page": "Event_Explorer"},
    ]
    if is_logged_in:
        nav_items.append({"label": "👤 Profil", "page": "Profil_saya"})
    if role == "admin":
        nav_items.append({"label": "📊 Dashboard", "page": "Dashboard_admin"})

    user_name = user.get("name", "User") if user else ""
    initials  = avatar_initials(user_name) if user_name else "?"

    # Build nav links HTML
    links_html = ""
    for item in nav_items:
        active = ' active' if item["page"] == current_page else ""
        links_html += (
            '<a class="nav-link' + active + '" href="?page=' + item["page"] + '">'
            + item["label"] + "</a>"
        )

    # Build auth section HTML
    if is_logged_in:
        badge = '<span class="notif-badge">' + str(unread) + "</span>" if unread > 0 else ""
        auth_html = (
            '<div class="nav-user">'
            '<div class="nav-notif">🔔' + badge + "</div>"
            '<div class="nav-avatar">' + initials + "</div>"
            '<span class="nav-username">' + user_name.split()[0] + "</span>"
            "</div>"
        )
    else:
        auth_html = (
            '<div class="nav-auth-btns">'
            '<a class="nav-btn-ghost" href="?page=Login_register">Masuk</a>'
            '<a class="nav-btn-primary" href="?page=Login_register">Daftar</a>'
            "</div>"
        )

    # Inject CSS first, then render HTML
    st.markdown(_NAVBAR_CSS, unsafe_allow_html=True)
    navbar_html = (
        '<nav class="eventbot-navbar">'
        '<a class="nav-brand" href="?page=Landing">'
        '🎪 <span class="nav-brand-name">EventBot</span>'
        "</a>"
        '<div class="nav-links">' + links_html + "</div>"
        + auth_html +
        "</nav>"
    )
    st.markdown(navbar_html, unsafe_allow_html=True)

    # Streamlit button fallback for navigation
    _render_nav_buttons_hidden(nav_items, current_page)


def _render_nav_buttons_hidden(nav_items: list, current_page: str) -> None:
    """Render tombol navigasi Streamlit (fungsional)."""
    cols = st.columns(len(nav_items) + 2)
    for i, item in enumerate(nav_items):
        with cols[i]:
            if st.button(item["label"], key=f"nav_btn_{item['page']}", use_container_width=True):
                st.session_state["current_page"] = item["page"]
                st.rerun()

    if SessionManager.is_logged_in():
        with cols[-1]:
            if st.button("🚪 Keluar", key="nav_btn_logout"):
                SessionManager.logout()
                st.session_state["current_page"] = "Landing"
                st.rerun()

    # Hide these fallback buttons visually — navigasi real pakai sidebar
    st.markdown(
        "<style>[data-testid='stHorizontalBlock']:last-of-type{display:none!important}</style>",
        unsafe_allow_html=True,
    )
