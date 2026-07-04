"""
Dashboard Admin Page
====================
Overview, statistik, dan quick actions untuk admin/organizer.
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.config import execute_query
from backend.models import EventModel, UserModel, RegistrationModel, TicketModel

st.set_page_config(page_title="Dashboard - EventBot", page_icon="📊", layout="wide")

# ── AUTH CHECK ────────────────────────────────────────────
user = st.session_state.get('user')
if not user or user.get('role') not in ['admin', 'organizer']:
    st.error("🚫 Akses ditolak. Halaman ini hanya untuk Admin/Organizer.")
    if st.button("🔐 Login", use_container_width=True):
        st.switch_page("pages/4_🔐_Login.py")
    st.stop()

# ── CSS ───────────────────────────────────────────────────
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0F0F0F 0%, #1A1A2E 50%, #16213E 100%);
}

.metric-card {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 24px;
    text-align: center;
    transition: all 0.3s;
}

.metric-card:hover {
    transform: translateY(-4px);
    border-color: rgba(59, 130, 246, 0.3);
}

.metric-value {
    font-size: 36px;
    font-weight: 800;
    background: linear-gradient(135deg, #E0E0E0, #3B82F6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.metric-label {
    font-size: 14px;
    color: rgba(224, 224, 224, 0.6);
    margin-top: 4px;
}

.metric-icon {
    font-size: 28px;
    margin-bottom: 8px;
}

.bento-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin: 24px 0;
}

.chart-container {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 24px;
    margin: 16px 0;
}

.action-btn {
    background: rgba(59, 130, 246, 0.15);
    border: 1px solid rgba(59, 130, 246, 0.3);
    border-radius: 12px;
    padding: 16px;
    text-align: center;
    cursor: pointer;
    transition: all 0.3s;
}

.action-btn:hover {
    background: rgba(59, 130, 246, 0.3);
    transform: translateY(-2px);
}

.status-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
}

.table-row:hover {
    background: rgba(255, 255, 255, 0.03);
}
</style>
""", unsafe_allow_html=True)

# ── HEADER ────────────────────────────────────────────────
st.markdown(f"""
<div style="padding: 20px 0;">
    <h1 style="font-size: 32px; font-weight: 800; color: #E0E0E0; margin: 0;">
        📊 Dashboard
    </h1>
    <p style="color: rgba(224,224,224,0.6); margin: 4px 0 0 0;">
        Selamat datang, <strong>{user['name']}</strong> ({user['role']})
    </p>
</div>
""", unsafe_allow_html=True)

# ── GET STATS ─────────────────────────────────────────────
stats = execute_query("SELECT * FROM get_admin_dashboard_stats()", fetch_one=True)

# ── METRICS ROW ─────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-icon">👥</div>
        <div class="metric-value">{stats.get('total_users', 0) if stats else 0}</div>
        <div class="metric-label">Total Users</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-icon">🎪</div>
        <div class="metric-value">{stats.get('total_events', 0) if stats else 0}</div>
        <div class="metric-label">Total Events</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-icon">🎫</div>
        <div class="metric-value">{stats.get('total_registrations', 0) if stats else 0}</div>
        <div class="metric-label">Total Registrations</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    revenue = stats.get('total_revenue', 0) if stats else 0
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-icon">💰</div>
        <div class="metric-value">Rp {revenue:,.0f}</div>
        <div class="metric-label">Total Revenue</div>
    </div>
    """, unsafe_allow_html=True)

# ── QUICK ACTIONS ───────────────────────────────────────
st.markdown("<h3 style='margin: 32px 0 16px; color: #E0E0E0;'>⚡ Quick Actions</h3>", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("➕ Buat Event", use_container_width=True):
        st.switch_page("pages/6_🎪_Manajemen_Event.py")

with col2:
    if st.button("👥 Kelola User", use_container_width=True):
        st.switch_page("pages/7_👥_Manajemen_User.py")

with col3:
    if st.button("🎫 Kelola Tiket", use_container_width=True):
        st.switch_page("pages/8_🎫_Manajemen_Tiket.py")

with col4:
    if st.button("📚 Knowledge Base", use_container_width=True):
        st.switch_page("pages/9_📚_Knowledge_Base.py")

# ── EVENT STATUS CHART ────────────────────────────────────
st.markdown("<h3 style='margin: 32px 0 16px; color: #E0E0E0;'>📈 Event Status</h3>", unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    # Simple bar chart using Streamlit
    status_data = {
        'Upcoming': stats.get('upcoming_events', 0) if stats else 0,
        'Ongoing': stats.get('ongoing_events', 0) if stats else 0,
        'Completed': stats.get('completed_events', 0) if stats else 0,
    }

    st.bar_chart(status_data, use_container_width=True, color=["#3B82F6", "#10B981", "#8B5CF6"])

with col2:
    st.markdown("""
    <div class="chart-container">
        <h4 style="color: #E0E0E0; margin: 0 0 16px;">Status Registrasi</h4>
    """, unsafe_allow_html=True)

    pending = stats.get('pending_registrations', 0) if stats else 0
    confirmed = stats.get('confirmed_registrations', 0) if stats else 0

    st.markdown(f"""
        <div style="display: flex; justify-content: space-between; margin: 8px 0;">
            <span style="color: rgba(224,224,224,0.7);">⏳ Pending</span>
            <span style="color: #F59E0B; font-weight: 600;">{pending}</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin: 8px 0;">
            <span style="color: rgba(224,224,224,0.7);">✅ Confirmed</span>
            <span style="color: #10B981; font-weight: 600;">{confirmed}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── RECENT EVENTS TABLE ───────────────────────────────────
st.markdown("<h3 style='margin: 32px 0 16px; color: #E0E0E0;'>🎪 Event Terbaru</h3>", unsafe_allow_html=True)

recent_events = EventModel.search(limit=5)

if recent_events:
    for event in recent_events:
        status_colors = {
            'upcoming': '#3B82F6',
            'ongoing': '#10B981',
            'completed': '#8B5CF6',
            'cancelled': '#EF4444'
        }
        status_color = status_colors.get(event.get('status', 'upcoming'), '#3B82F6')

        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

        with col1:
            st.write(f"**{event['title']}**")
        with col2:
            st.write(f"📍 {event.get('location', 'TBA')}")
        with col3:
            st.write(f"📅 {event.get('start_date', 'TBA')}")
        with col4:
            st.markdown(f"""
            <span style="color: {status_color}; font-weight: 600; font-size: 12px;">
                ● {event.get('status', 'upcoming').upper()}
            </span>
            """, unsafe_allow_html=True)

        st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin: 8px 0;'>", unsafe_allow_html=True)
else:
    st.info("Belum ada event. Buat event pertama Anda!")