"""
EventBot Frontend — Main Entry Point
=====================================
Streamlit Single-Page Application dengan routing via session_state.

Menjalankan:
    cd frontend/
    streamlit run app.py
"""

import sys
import os

_FRONTEND_DIR = os.path.dirname(os.path.abspath(__file__))
if _FRONTEND_DIR not in sys.path:
    sys.path.insert(0, _FRONTEND_DIR)

import streamlit as st

st.set_page_config(
    page_title="EventBot — Chatbot Manajemen Event",
    page_icon="🎪",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help":     None,
        "Report a bug": None,
        "About":        "**EventBot v1.0.0** — Chatbot berbasis NLP untuk manajemen event 🎪",
    },
)

from utils.session_manager import SessionManager
from components.sidebar import render_sidebar
from views import PAGE_REGISTRY

_PROTECTED_PAGES = {"Profil_saya"}
_ADMIN_ONLY_PAGES = {
    "Dashboard_admin", "Manajemen_User", "Knowledge_Base", "Pengaturan",
    "Manajemen_Event", "Manajemen_Ticket",
}


def main() -> None:
    SessionManager.init()
    _sync_page_from_query_params()

    current_page = st.session_state.get("current_page", "Landing")
    render_sidebar(current_page=current_page)

    page_name = st.session_state.get("current_page", "Landing")

    # Bersihkan state detail event jika user navigasi ke halaman lain
    if page_name != "Event_Explorer":
        st.session_state.pop("detail_event_id", None)
        st.session_state.pop("_incoming_detail_id", None)
        st.session_state.pop("explorer_page", None)  # reset page ke 1 saat kembali
    else:
        # Tandai perlu refresh cache saat masuk Event_Explorer
        if not st.session_state.get("_explorer_active"):
            st.session_state["_explorer_needs_refresh"] = True
            st.session_state["_explorer_active"] = True

    if page_name == "Event_Explorer":
        st.session_state["_explorer_active"] = True
    else:
        st.session_state.pop("_explorer_active", None)

    if page_name in _ADMIN_ONLY_PAGES and not SessionManager.is_admin():
        _render_access_denied(page_name)
        return

    if page_name in _PROTECTED_PAGES and not SessionManager.is_logged_in():
        st.session_state["current_page"] = "Login_register"
        st.rerun()
        return

    page_module = PAGE_REGISTRY.get(page_name)
    if page_module and hasattr(page_module, "render"):
        try:
            page_module.render()
        except Exception as e:
            _render_page_error(page_name, e)
    else:
        st.session_state["current_page"] = "Landing"
        PAGE_REGISTRY["Landing"].render()


def _sync_page_from_query_params() -> None:
    try:
        page_param = st.query_params.get("page", "")
        if page_param and page_param in PAGE_REGISTRY:
            if st.session_state.get("current_page") != page_param:
                st.session_state["current_page"] = page_param
    except Exception:
        pass


def _render_access_denied(page_name: str) -> None:
    from styles.theme_manager import ThemeManager
    ThemeManager.apply(SessionManager.get_theme())

    st.markdown(
        '<div style="text-align:center;padding:4rem 2rem;">'
        '<div style="font-size:3.5rem;margin-bottom:1rem;">⛔</div>'
        '<h1 style="font-size:1.75rem;font-weight:800;color:#EF4444;margin:0 0 0.5rem;">Akses Ditolak</h1>'
        '<p style="color:#9CA3AF;font-size:0.95rem;max-width:400px;margin:0 auto 2rem;line-height:1.7;">'
        'Halaman <strong style="color:#F8F9FA;">' + page_name + '</strong> '
        'hanya dapat diakses oleh <strong style="color:#7C3AED;">admin</strong>.</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🏠 Ke Beranda", use_container_width=True, type="primary"):
                st.session_state["current_page"] = "Landing"
                st.rerun()
        with c2:
            if st.button("🔐 Login", use_container_width=True):
                st.session_state["current_page"] = "Login_register"
                st.rerun()


def _render_page_error(page_name: str, error: Exception) -> None:
    st.error("❌ Terjadi kesalahan saat memuat halaman **" + page_name + "**.")
    is_dev = os.getenv("APP_ENV", "development") == "development"
    if is_dev:
        with st.expander("🔍 Detail Error (Development Mode)", expanded=True):
            st.exception(error)
    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        if st.button("🔄 Refresh", key="err_refresh"):
            st.rerun()
    with col2:
        if st.button("🏠 Beranda", key="err_home"):
            st.session_state["current_page"] = "Landing"
            st.rerun()


if __name__ == "__main__":
    main()
