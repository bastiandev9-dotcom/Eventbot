"""
use_theme Hook
==============
Hook untuk manajemen tema UI (selalu dark mode) dan injeksi CSS.
"""

import streamlit as st
from pathlib import Path
from typing import Dict, Any

from utils.session_manager import SessionManager

_STYLES_DIR = Path(__file__).parent.parent / "styles"

# ── Tab CSS — di-inject inline agar selalu aktif ──────────
_TAB_CSS = (
    '.stTabs [data-baseweb="tab-list"]{'
    'background:rgba(255,255,255,0.05)!important;border-radius:10px!important;'
    'padding:4px!important;gap:6px!important;border-bottom:none!important;}'
    '.stTabs [data-baseweb="tab"]{'
    'border-radius:8px!important;color:#ADB5BD!important;font-weight:500!important;'
    'font-size:0.875rem!important;padding:0.4rem 1rem!important;'
    'transition:all 0.2s ease!important;border:none!important;'
    'background:transparent!important;margin:0 2px!important;}'
    '.stTabs [data-baseweb="tab"]:hover{'
    'color:#F8F9FA!important;background:rgba(255,255,255,0.07)!important;}'
    '.stTabs [aria-selected="true"]{'
    'background:#7C3AED!important;color:white!important;font-weight:600!important;}'
    '.stTabs [data-baseweb="tab-highlight"]{display:none!important;}'
    '.stTabs [data-baseweb="tab-border"]{display:none!important;}'
    '.stTabs [data-baseweb="tab-panel"]{padding-top:1.25rem!important;}'
)

_VARS_DARK = (
    ':root{'
    '--bg-primary:#0F0F1A;--bg-secondary:#1A1A2E;'
    '--bg-card:rgba(255,255,255,0.05);--bg-card-hover:rgba(255,255,255,0.08);'
    '--text-primary:#F8F9FA;--text-secondary:#ADB5BD;--text-muted:#6B7280;'
    '--accent-primary:#7C3AED;--accent-secondary:#4F46E5;'
    '--accent-glow:rgba(124,58,237,0.4);--accent-subtle:rgba(124,58,237,0.1);'
    '--success:#10B981;--warning:#F59E0B;--danger:#EF4444;--info:#3B82F6;'
    '--border-color:rgba(255,255,255,0.1);--border-accent:rgba(124,58,237,0.3);}'
)


def _load_css_file(filename: str) -> str:
    file_path = _STYLES_DIR / filename
    try:
        return file_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def inject_css(*filenames: str) -> None:
    css = "\n".join(_load_css_file(f) for f in filenames)
    if css.strip():
        st.markdown("<style>" + css + "</style>", unsafe_allow_html=True)


def inject_all_styles() -> None:
    inject_css("global.css", "glassmorphism.css", "animation.css")


def use_theme() -> Dict[str, Any]:
    """Hook untuk manajemen tema UI EventBot (selalu dark)."""
    SessionManager.init()

    def get_current_theme() -> str:
        return "dark"

    def apply_theme() -> None:
        """Inject CSS + variables + tab style ke halaman."""
        inject_css("global.css", "glassmorphism.css", "animation.css", "dark_theme.css")
        st.markdown(
            "<style>" + _VARS_DARK + _TAB_CSS + "</style>",
            unsafe_allow_html=True,
        )

    def get_colors() -> Dict[str, str]:
        """Kembalikan palet warna untuk chart/komponen Python."""
        return {
            "bg_primary":      "#0F0F1A",
            "bg_secondary":    "#1A1A2E",
            "bg_card":         "#1E1E35",
            "text_primary":    "#F8F9FA",
            "text_secondary":  "#ADB5BD",
            "text_muted":      "#6B7280",
            "accent_primary":  "#7C3AED",
            "accent_secondary":"#4F46E5",
            "success":         "#10B981",
            "warning":         "#F59E0B",
            "danger":          "#EF4444",
            "info":            "#3B82F6",
            "border":          "rgba(255,255,255,0.1)",
            "chart_bg":        "#1A1A2E",
            "chart_paper":     "#0F0F1A",
            "chart_grid":      "rgba(255,255,255,0.05)",
            "chart_font":      "#ADB5BD",
        }

    def restore_saved_theme() -> None:
        pass  # tidak digunakan lagi, tema selalu dark

    return {
        "current_theme":       "dark",
        "is_dark":             True,
        "apply_theme":         apply_theme,
        "get_colors":          get_colors,
        "restore_saved_theme": restore_saved_theme,
        "inject_css":          inject_css,
        "inject_all_styles":   inject_all_styles,
    }
