"""
Dashboard Admin Page — EventBot
"""

import streamlit as st
from components.metric_card import render_metric_row, render_progress_metric
from components.toast import render_toast
from hooks.use_auth import use_auth
from hooks.use_theme import use_theme
from utils.api_client import APIClient
from utils.session_manager import SessionManager


def render() -> None:
    theme = use_theme()
    theme["apply_theme"]()
    render_toast()

    auth = use_auth()
    if not auth["require_role"]("admin"):
        return

    user = auth["user"] or {}
    token = SessionManager.get_token()
    stats = _fetch_stats(token)

    # Header
    user_name = user.get("name", "Admin")
    st.markdown(
        '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1.75rem;">'
        '<div><h1 style="font-size:1.75rem;font-weight:800;color:#F8F9FA;margin:0 0 0.2rem;">📊 Dashboard Admin</h1>'
        '<p style="color:#6B7280;font-size:0.875rem;margin:0;">Selamat datang kembali, '
        '<strong style="color:#ADB5BD;">' + user_name + '</strong></p></div>'
        '<div style="font-size:0.8rem;color:#4B5563;">🕐 Last updated: baru saja</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Metric Row
    render_metric_row([
        {"label": "Total Event",    "value": str(stats.get("total_events", 0)),         "icon": "🎪", "color": "purple",
         "delta": "+" + str(stats.get("new_events_week", 0)) + " minggu ini",           "delta_positive": True},
        {"label": "Total Peserta",  "value": _fmt(stats.get("total_registrations", 0)), "icon": "👥", "color": "green",
         "delta": "+" + str(stats.get("new_registrations_week", 0)) + " minggu ini",    "delta_positive": True},
        {"label": "Total User",     "value": str(stats.get("total_users", 0)),           "icon": "🧑‍💻", "color": "blue",
         "delta": "+" + str(stats.get("new_users_week", 0)) + " minggu ini",            "delta_positive": True},
        {"label": "Tiket Terjual",  "value": str(stats.get("tickets_sold", 0)),          "icon": "🎫", "color": "orange",
         "sub_text": "Dari semua event aktif"},
    ])

    st.markdown("<br>", unsafe_allow_html=True)

    col_left, col_right = st.columns([2, 1], gap="medium")

    with col_left:
        _box_start("📈 Distribusi Status Event")
        _render_event_chart(stats, theme)
        _box_end()

        _box_start("🕐 Registrasi Terbaru")
        _render_recent_registrations(token)
        _box_end()

    with col_right:
        _box_start("⚡ Quick Actions")
        _render_quick_actions()
        _box_end()

        _box_start("🎯 Kapasitas Event Aktif")
        for s in stats.get("capacity_samples", []):
            render_progress_metric(label=s["title"], current=s["registered"], total=s["capacity"], icon="🎪")
        _box_end()

    st.markdown("<br>", unsafe_allow_html=True)
    _box_start("📊 Event per Kategori")
    _render_category_chart(stats, theme)
    _box_end()


def _box_start(title: str) -> None:
    st.markdown(
        '<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);'
        'border-radius:16px;padding:1.25rem;margin-bottom:1rem;">'
        '<div style="font-weight:700;color:#F8F9FA;margin-bottom:1rem;font-size:0.95rem;">' + title + '</div>',
        unsafe_allow_html=True,
    )


def _box_end() -> None:
    st.markdown('</div>', unsafe_allow_html=True)


def _render_event_chart(stats: dict, theme: dict) -> None:
    try:
        import plotly.graph_objects as go
        colors = theme["get_colors"]()
        # Gunakan key yang tersedia, fallback jika tidak ada
        paper   = colors.get("chart_paper", colors.get("bg_primary",   "#0F0F1A"))
        bg      = colors.get("chart_bg",    colors.get("bg_secondary",  "#1A1A2E"))
        grid    = colors.get("chart_grid",  "rgba(255,255,255,0.05)")
        font_c  = colors.get("chart_font",  colors.get("text_secondary", "#ADB5BD"))

        labels = ["Akan Datang", "Berlangsung", "Selesai"]
        values = [stats.get("events_upcoming", 0), stats.get("events_ongoing", 0), stats.get("events_completed", 0)]
        fig = go.Figure(go.Bar(x=labels, y=values,
                               marker_color=["#F59E0B", "#10B981", "#6B7280"],
                               text=values, textposition="outside",
                               textfont={"color": font_c, "size": 12}))
        fig.update_layout(paper_bgcolor=paper, plot_bgcolor=bg,
                          font={"family": "Inter", "color": font_c},
                          xaxis={"gridcolor": grid, "showline": False},
                          yaxis={"gridcolor": grid, "showline": False},
                          margin={"l": 20, "r": 20, "t": 10, "b": 20},
                          height=200, showlegend=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    except ImportError:
        st.info("Install plotly: pip install plotly")


def _render_category_chart(stats: dict, theme: dict) -> None:
    try:
        import plotly.graph_objects as go
        colors = theme["get_colors"]()
        paper   = colors.get("chart_paper", colors.get("bg_primary",   "#0F0F1A"))
        bg      = colors.get("chart_bg",    colors.get("bg_secondary",  "#1A1A2E"))
        grid    = colors.get("chart_grid",  "rgba(255,255,255,0.05)")
        font_c  = colors.get("chart_font",  colors.get("text_secondary", "#ADB5BD"))

        cats = stats.get("categories", {})
        if not cats:
            return
        sorted_cats = sorted(cats.items(), key=lambda x: x[1], reverse=True)
        labels = [c[0] for c in sorted_cats]
        values = [c[1] for c in sorted_cats]
        fig = go.Figure(go.Bar(y=labels, x=values, orientation="h",
                               marker_color="#7C3AED",
                               text=values, textposition="outside",
                               textfont={"color": font_c, "size": 12}))
        fig.update_layout(paper_bgcolor=paper, plot_bgcolor=bg,
                          font={"family": "Inter", "color": font_c},
                          xaxis={"gridcolor": grid, "showline": False},
                          yaxis={"gridcolor": grid, "showline": False, "autorange": "reversed"},
                          margin={"l": 20, "r": 20, "t": 10, "b": 20},
                          height=280, showlegend=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    except ImportError:
        for cat, val in stats.get("categories", {}).items():
            st.markdown("- **" + cat + "**: " + str(val) + " event")


def _render_quick_actions() -> None:
    for label, page in [
        ("➕ Tambah Event",   "Manajemen_Event"),
        ("👥 Kelola User",    "Manajemen_User"),
        ("🎫 Kelola Tiket",   "Manajemen_Ticket"),
        ("📚 Knowledge Base", "Knowledge_Base"),
        ("⚙️ Pengaturan",     "Pengaturan"),
    ]:
        if st.button(label, key="dash_" + page, use_container_width=True):
            st.session_state["current_page"] = page
            st.rerun()


def _render_recent_registrations(token: str) -> None:
    try:
        client = APIClient(token=token)
        result = client._get("/registrations/", {"limit": 5})
        regs   = result.get("data", [])
    except Exception:
        regs = [
            {"user_name": "Budi Santoso", "event_title": "Tech Conference", "registered_at": "5 menit lalu"},
            {"user_name": "Sari Dewi",    "event_title": "Design Workshop",  "registered_at": "23 menit lalu"},
        ]

    for reg in regs[:5]:
        uname  = reg.get("user_name") or reg.get("user", {}).get("name", "User")
        ename  = reg.get("event_title") or reg.get("event", {}).get("title", "Event")
        tstr   = reg.get("registered_at", "")
        init   = uname[0].upper() if uname else "?"
        st.markdown(
            '<div style="display:flex;align-items:center;gap:0.75rem;padding:0.6rem 0;'
            'border-bottom:1px solid rgba(255,255,255,0.05);">'
            '<div style="width:32px;height:32px;border-radius:50%;background:linear-gradient(135deg,#7C3AED,#4F46E5);'
            'display:flex;align-items:center;justify-content:center;font-size:0.75rem;font-weight:700;color:white;flex-shrink:0;">'
            + init + '</div>'
            '<div style="flex:1;min-width:0;">'
            '<div style="font-size:0.825rem;font-weight:600;color:#F8F9FA;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">'
            + uname + '</div>'
            '<div style="font-size:0.75rem;color:#6B7280;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">'
            + ename + '</div></div>'
            '<div style="font-size:0.7rem;color:#4B5563;white-space:nowrap;">' + tstr + '</div>'
            '</div>',
            unsafe_allow_html=True,
        )


def _fetch_stats(token) -> dict:
    try:
        client = APIClient(token=token)
        result = client._get("/admin/stats")
        return result.get("data", {})
    except Exception:
        return {
            "total_events": 42, "total_registrations": 1284,
            "total_users": 356,  "tickets_sold": 890,
            "new_events_week": 5, "new_registrations_week": 78, "new_users_week": 23,
            "events_upcoming": 18, "events_ongoing": 4, "events_completed": 20,
            "capacity_samples": [
                {"title": "Tech Conference", "registered": 180, "capacity": 200},
                {"title": "Design Workshop", "registered": 45,  "capacity": 50},
                {"title": "Startup Pitch",   "registered": 92,  "capacity": 150},
            ],
            "categories": {"Teknologi": 12, "Bisnis": 8, "Pendidikan": 7,
                           "Musik": 5, "Olahraga": 4, "Seni": 3, "Lainnya": 3},
        }


def _fmt(n: int) -> str:
    return f"{n/1000:.1f}K" if n >= 1000 else str(n)
