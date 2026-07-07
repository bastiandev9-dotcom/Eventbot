"""
Theme Manager
=============
Modul Python untuk manajemen tema dan injeksi CSS ke Streamlit.
Tema selalu dark mode.
"""

import streamlit as st
from pathlib import Path
from typing import Dict, List

# ── Paths ─────────────────────────────────────────────────
_STYLES_DIR = Path(__file__).parent


class ThemeManager:
    """
    Singleton-style manager untuk tema UI EventBot.
    Mengelola loading, caching, dan injeksi CSS dark mode.
    """

    _BASE_CSS_FILES = [
        "global.css",
        "glassmorphism.css",
        "animation.css",
        "dark_theme.css",
    ]

    # Cache CSS agar tidak baca file berulang kali
    _css_cache: Dict[str, str] = {}

    @classmethod
    def _read_css(cls, filename: str) -> str:
        """Baca file CSS dengan caching."""
        if filename in cls._css_cache:
            return cls._css_cache[filename]
        file_path = _STYLES_DIR / filename
        try:
            content = file_path.read_text(encoding="utf-8")
            cls._css_cache[filename] = content
            return content
        except FileNotFoundError:
            return ""

    @classmethod
    def inject_css(cls, *filenames: str) -> None:
        """Inject satu atau lebih file CSS ke halaman Streamlit."""
        css_parts = [cls._read_css(f) for f in filenames]
        combined = "\n".join(css_parts)
        if combined.strip():
            st.markdown(f"<style>\n{combined}\n</style>", unsafe_allow_html=True)

    @classmethod
    def apply(cls, theme: str = "dark") -> None:
        """Terapkan semua CSS (selalu dark mode)."""
        cls.inject_css(*cls._BASE_CSS_FILES)
        cls._inject_theme_variables()

    @classmethod
    def _inject_theme_variables(cls) -> None:
        """Inject CSS custom properties dark mode."""
        variables = """
        :root {
            --bg-primary:       #0F0F1A;
            --bg-secondary:     #1A1A2E;
            --bg-card:          rgba(255, 255, 255, 0.05);
            --bg-card-hover:    rgba(255, 255, 255, 0.08);
            --text-primary:     #F8F9FA;
            --text-secondary:   #ADB5BD;
            --text-muted:       #6B7280;
            --accent-primary:   #7C3AED;
            --accent-secondary: #4F46E5;
            --accent-glow:      rgba(124, 58, 237, 0.4);
            --accent-subtle:    rgba(124, 58, 237, 0.1);
            --success:          #10B981;
            --warning:          #F59E0B;
            --danger:           #EF4444;
            --info:             #3B82F6;
            --border-color:     rgba(255, 255, 255, 0.1);
            --border-accent:    rgba(124, 58, 237, 0.3);
        }
        """
        st.markdown(f"<style>{variables}</style>", unsafe_allow_html=True)

    @classmethod
    def get_color_palette(cls, theme: str = "dark") -> Dict[str, str]:
        """Kembalikan palet warna Python untuk digunakan di chart."""
        return {
            "bg_primary":     "#0F0F1A",
            "bg_secondary":   "#1A1A2E",
            "bg_card":        "#1E1E35",
            "text_primary":   "#F8F9FA",
            "text_secondary": "#ADB5BD",
            "text_muted":     "#6B7280",
            "accent":         "#7C3AED",
            "accent_2":       "#4F46E5",
            "success":        "#10B981",
            "warning":        "#F59E0B",
            "danger":         "#EF4444",
            "info":           "#3B82F6",
            "border":         "rgba(255,255,255,0.1)",
            "chart_bg":       "#1A1A2E",
            "chart_paper":    "#0F0F1A",
            "chart_grid":     "rgba(255,255,255,0.05)",
            "chart_font":     "#ADB5BD",
            "palette": ["#7C3AED", "#4F46E5", "#10B981", "#3B82F6",
                        "#F59E0B", "#EF4444", "#8B5CF6", "#06B6D4"],
        }

    @classmethod
    def get_plotly_layout(cls, theme: str = "dark") -> Dict:
        """Kembalikan layout config Plotly yang sesuai dengan tema EventBot."""
        colors = cls.get_color_palette()
        return {
            "paper_bgcolor": colors["chart_paper"],
            "plot_bgcolor":  colors["chart_bg"],
            "font": {
                "family": "Inter, sans-serif",
                "color":  colors["chart_font"],
                "size":   13,
            },
            "xaxis": {
                "gridcolor": colors["chart_grid"],
                "linecolor": colors["border"],
                "tickfont":  {"color": colors["chart_font"]},
            },
            "yaxis": {
                "gridcolor": colors["chart_grid"],
                "linecolor": colors["border"],
                "tickfont":  {"color": colors["chart_font"]},
            },
            "legend": {
                "bgcolor":     "rgba(0,0,0,0)",
                "bordercolor": colors["border"],
                "font":        {"color": colors["chart_font"]},
            },
            "margin":   {"l": 40, "r": 20, "t": 40, "b": 40},
            "colorway": colors["palette"],
        }

    @classmethod
    def apply_page_config(
        cls,
        page_title: str = "EventBot",
        page_icon: str = "🎪",
        layout: str = "wide",
        sidebar_state: str = "auto",
    ) -> None:
        """
        Set konfigurasi halaman Streamlit.
        Harus dipanggil sekali di awal sebelum konten lain.
        """
        try:
            st.set_page_config(
                page_title=page_title,
                page_icon=page_icon,
                layout=layout,
                initial_sidebar_state=sidebar_state,
                menu_items={
                    "Get Help": None,
                    "Report a bug": None,
                    "About": "**EventBot** — Chatbot manajemen event berbasis NLP 🎪",
                },
            )
        except st.errors.StreamlitAPIException:
            pass

    @classmethod
    def clear_cache(cls) -> None:
        """Kosongkan cache CSS (berguna saat development)."""
        cls._css_cache.clear()

    @classmethod
    def render_html(cls, html: str) -> None:
        """Shortcut untuk render HTML yang aman."""
        st.markdown(html, unsafe_allow_html=True)

    @classmethod
    def render_card(
        cls,
        content: str,
        card_class: str = "glass-card",
        extra_style: str = "",
    ) -> None:
        """Render konten dalam glass card container."""
        style = f' style="{extra_style}"' if extra_style else ""
        cls.render_html(f'<div class="{card_class}"{style}>{content}</div>')


# ── Module-level convenience functions ───────────────────

def apply_theme(theme: str = "dark") -> None:
    """Shortcut untuk ThemeManager.apply()"""
    ThemeManager.apply()


def get_colors(theme: str = "dark") -> Dict[str, str]:
    """Shortcut untuk ThemeManager.get_color_palette()"""
    return ThemeManager.get_color_palette()


def get_plotly_layout(theme: str = "dark") -> Dict:
    """Shortcut untuk ThemeManager.get_plotly_layout()"""
    return ThemeManager.get_plotly_layout()
