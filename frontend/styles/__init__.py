"""
Styles Package
==============
CSS files dan ThemeManager untuk EventBot frontend.
"""

from .theme_manager import ThemeManager, apply_theme, get_colors, get_plotly_layout

__all__ = [
    "ThemeManager",
    "apply_theme",
    "get_colors",
    "get_plotly_layout",
]
