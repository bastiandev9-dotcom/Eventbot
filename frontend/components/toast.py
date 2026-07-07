"""
Toast Notification Component
=============================
Notifikasi toast untuk EventBot.
"""

import streamlit as st
from typing import Optional
from utils.session_manager import SessionManager

_TOAST_CONFIG = {
    "success": {"icon": "✅", "bg": "rgba(16,185,129,0.12)",  "border": "rgba(16,185,129,0.35)",  "color": "#10B981", "title": "Berhasil!"},
    "error":   {"icon": "❌", "bg": "rgba(239,68,68,0.12)",   "border": "rgba(239,68,68,0.35)",   "color": "#EF4444", "title": "Gagal!"},
    "warning": {"icon": "⚠️", "bg": "rgba(245,158,11,0.12)",  "border": "rgba(245,158,11,0.35)",  "color": "#F59E0B", "title": "Perhatian!"},
    "info":    {"icon": "ℹ️", "bg": "rgba(59,130,246,0.12)",  "border": "rgba(59,130,246,0.35)",  "color": "#3B82F6", "title": "Info"},
}


def render_toast(message: Optional[str] = None, toast_type: str = "success", auto_check_session: bool = True) -> None:
    """Render toast notification."""
    if auto_check_session and not message:
        toast_data = SessionManager.pop_toast()
        if toast_data:
            message    = toast_data.get("message", "")
            toast_type = toast_data.get("type", "success")

    if not message:
        return

    cfg = _TOAST_CONFIG.get(toast_type, _TOAST_CONFIG["info"])
    html = (
        '<div style="background:' + cfg["bg"] + ';border:1px solid ' + cfg["border"] + ';'
        'border-left:4px solid ' + cfg["color"] + ';border-radius:12px;padding:0.875rem 1.25rem;'
        'margin-bottom:1rem;display:flex;align-items:center;gap:0.75rem;'
        'animation:fadeInDown 0.35s ease forwards;box-shadow:0 4px 20px rgba(0,0,0,0.2);">'
        '<span style="font-size:1.1rem;flex-shrink:0;">' + cfg["icon"] + "</span>"
        '<div><div style="font-weight:700;color:' + cfg["color"] + ';font-size:0.875rem;line-height:1.3;">'
        + cfg["title"] + "</div>"
        '<div style="color:#D1D5DB;font-size:0.85rem;margin-top:0.1rem;line-height:1.4;">' + message + "</div>"
        "</div></div>"
    )
    st.markdown(html, unsafe_allow_html=True)


def show_success(message: str, rerun: bool = False) -> None:
    render_toast(message=message, toast_type="success", auto_check_session=False)
    if rerun:
        st.rerun()


def show_error(message: str, rerun: bool = False) -> None:
    render_toast(message=message, toast_type="error", auto_check_session=False)
    if rerun:
        st.rerun()


def show_warning(message: str, rerun: bool = False) -> None:
    render_toast(message=message, toast_type="warning", auto_check_session=False)


def show_info(message: str, rerun: bool = False) -> None:
    render_toast(message=message, toast_type="info", auto_check_session=False)


def queue_toast(message: str, toast_type: str = "success") -> None:
    """Antri toast untuk rerun berikutnya."""
    SessionManager.show_toast(message=message, toast_type=toast_type)


def render_banner(message: str, banner_type: str = "info", dismissible: bool = True, key: str = "banner") -> None:
    """Render banner alert permanen."""
    if st.session_state.get("dismiss_" + key):
        return
    cfg = _TOAST_CONFIG.get(banner_type, _TOAST_CONFIG["info"])
    if dismissible:
        col_msg, col_close = st.columns([10, 1])
        with col_msg:
            html = (
                '<div style="background:' + cfg["bg"] + ';border:1px solid ' + cfg["border"] + ';'
                'border-left:4px solid ' + cfg["color"] + ';border-radius:10px;padding:0.75rem 1rem;'
                'display:flex;align-items:center;gap:0.625rem;">'
                "<span>" + cfg["icon"] + "</span>"
                '<span style="color:#D1D5DB;font-size:0.875rem;">' + message + "</span>"
                "</div>"
            )
            st.markdown(html, unsafe_allow_html=True)
        with col_close:
            if st.button("✕", key="dismiss_" + key, help="Tutup"):
                st.session_state["dismiss_" + key] = True
                st.rerun()
    else:
        render_toast(message=message, toast_type=banner_type, auto_check_session=False)
