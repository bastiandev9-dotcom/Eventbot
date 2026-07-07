"""
Metric Card Component
=====================
Kartu metrik untuk dashboard admin dengan animasi dan trend indicator.
"""

import streamlit as st
from typing import Optional, List, Dict, Any

_COLOR_MAP = {
    "purple": ("#7C3AED", "rgba(124,58,237,0.12)", "rgba(124,58,237,0.25)"),
    "green":  ("#10B981", "rgba(16,185,129,0.12)",  "rgba(16,185,129,0.25)"),
    "blue":   ("#3B82F6", "rgba(59,130,246,0.12)",  "rgba(59,130,246,0.25)"),
    "orange": ("#F59E0B", "rgba(245,158,11,0.12)",  "rgba(245,158,11,0.25)"),
    "red":    ("#EF4444", "rgba(239,68,68,0.12)",   "rgba(239,68,68,0.25)"),
    "teal":   ("#06B6D4", "rgba(6,182,212,0.12)",   "rgba(6,182,212,0.25)"),
}


def render_metric_card(
    label: str,
    value: Any,
    icon: str = "📊",
    delta: Optional[str] = None,
    delta_positive: Optional[bool] = None,
    color: str = "purple",
    sub_text: Optional[str] = None,
    key: str = "",
) -> None:
    """Render satu metric card dengan glass effect."""
    accent, bg_color, border_color = _COLOR_MAP.get(color, _COLOR_MAP["purple"])

    # Delta HTML
    if delta is not None:
        if delta_positive is True:
            delta_html = '<span style="color:#10B981;font-size:0.75rem;font-weight:600;">▲ ' + str(delta) + "</span>"
        elif delta_positive is False:
            delta_html = '<span style="color:#EF4444;font-size:0.75rem;font-weight:600;">▼ ' + str(delta) + "</span>"
        else:
            delta_html = '<span style="color:#6B7280;font-size:0.75rem;font-weight:600;">— ' + str(delta) + "</span>"
    else:
        delta_html = ""

    sub_html = (
        '<div style="font-size:0.75rem;color:#6B7280;margin-top:0.2rem;">' + str(sub_text) + "</div>"
    ) if sub_text else ""

    card = (
        '<div style="background:' + bg_color + ';border:1px solid ' + border_color + ';'
        'border-radius:16px;padding:1.25rem 1.5rem;animation:fadeInUp 0.4s ease forwards;height:100%;">'
        '<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:0.75rem;">'
        '<span style="font-size:0.8rem;color:#9CA3AF;font-weight:500;text-transform:uppercase;letter-spacing:0.05em;">'
        + label +
        '</span><span style="font-size:1.5rem;">' + icon + "</span></div>"
        '<div style="font-size:2rem;font-weight:800;color:' + accent + ';line-height:1.2;margin-bottom:0.25rem;">'
        + str(value) + "</div>"
        + sub_html + delta_html +
        "</div>"
    )
    st.markdown(card, unsafe_allow_html=True)


def render_metric_row(metrics: List[Dict[str, Any]]) -> None:
    """Render satu baris metric cards."""
    if not metrics:
        return
    cols = st.columns(len(metrics))
    for i, metric in enumerate(metrics):
        with cols[i]:
            render_metric_card(
                label=metric.get("label", ""),
                value=metric.get("value", "-"),
                icon=metric.get("icon", "📊"),
                delta=metric.get("delta"),
                delta_positive=metric.get("delta_positive"),
                color=metric.get("color", "purple"),
                sub_text=metric.get("sub_text"),
                key="metric_" + str(i) + "_" + str(metric.get("label", "")),
            )


def render_stat_mini(label: str, value: Any, icon: str = "•", color: str = "#7C3AED") -> None:
    """Render mini stat inline."""
    html = (
        '<div style="display:inline-flex;flex-direction:column;align-items:center;'
        'padding:0.875rem 1.25rem;background:rgba(255,255,255,0.04);'
        'border:1px solid rgba(255,255,255,0.08);border-radius:12px;min-width:100px;">'
        '<div style="font-size:1.25rem;margin-bottom:0.2rem;">' + icon + "</div>"
        '<div style="font-size:1.5rem;font-weight:800;color:' + color + ';line-height:1.2;">' + str(value) + "</div>"
        '<div style="font-size:0.75rem;color:#6B7280;margin-top:0.15rem;">' + label + "</div>"
        "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)


def render_progress_metric(
    label: str,
    current: int,
    total: int,
    icon: str = "📊",
    color: str = "#7C3AED",
) -> None:
    """Render metric card dengan progress bar."""
    pct = (current / total * 100) if total > 0 else 0
    pct_display = f"{pct:.0f}%"

    if pct >= 90:
        bar_color = "#EF4444"
    elif pct >= 70:
        bar_color = "#F59E0B"
    else:
        bar_color = color

    bar_width = min(pct, 100)
    html = (
        '<div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);'
        'border-radius:14px;padding:1.25rem;margin-bottom:0.5rem;">'
        '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.75rem;">'
        '<span style="font-size:0.8rem;color:#9CA3AF;font-weight:500;">' + label + "</span>"
        '<span style="font-size:1rem;">' + icon + "</span></div>"
        '<div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:0.5rem;">'
        '<span style="font-size:1.5rem;font-weight:800;color:#F8F9FA;">' + f"{current:,}" + "</span>"
        '<span style="font-size:0.875rem;color:#6B7280;">/ ' + f"{total:,}" + "</span></div>"
        '<div style="background:rgba(255,255,255,0.06);border-radius:9999px;height:6px;overflow:hidden;">'
        '<div style="width:' + f"{bar_width:.1f}" + '%;height:100%;background:' + bar_color + ';border-radius:9999px;"></div>'
        "</div>"
        '<div style="text-align:right;font-size:0.75rem;color:#6B7280;margin-top:0.25rem;">' + pct_display + " terisi</div>"
        "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)
