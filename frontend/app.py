"""
EventBot - Main Entry Point
============================
Streamlit multi-page app dengan routing, auth, dan glassmorphism theme.
"""

import streamlit as st
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import test_connection
from backend.models import UserModel

# ── PAGE CONFIG ───────────────────────────────────────────
st.set_page_config(
    page_title="EventBot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── CUSTOM CSS (Glassmorphism + Dark) ──────────────────────
def load_css():
    st.markdown("""
    <style>
    /* Global Reset */
    .stApp {
        background: linear-gradient(135deg, #0F0F0F 0%, #1A1A2E 50%, #16213E 100%);
        background-attachment: fixed;
    }

    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* Glassmorphism Card */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 24px;
        margin: 12px 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }

    /* Glass Button */
    .glass-button {
        background: rgba(59, 130, 246, 0.2);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-radius: 12px;
        color: #E0E0E0;
        padding: 12px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
        cursor: pointer;
    }

    .glass-button:hover {
        background: rgba(59, 130, 246, 0.4);
        border-color: rgba(59, 130, 246, 0.6);
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(59, 130, 246, 0.3);
    }

    /* Input Fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        color: #E0E0E0 !important;
    }

    /* Sidebar */
    .css-1d391kg, .css-163ttbj {
        background: rgba(15, 15, 15, 0.8) !important;
        backdrop-filter: blur(20px) !important;
    }

    /* Chat bubbles */
    .chat-user {
        background: rgba(59, 130, 246, 0.2);
        border-radius: 16px 16px 4px 16px;
        padding: 12px 16px;
        margin: 8px 0 8px auto;
        max-width: 80%;
        color: #E0E0E0;
    }

    .chat-bot {
        background: rgba(255, 255, 255, 0.08);
        border-radius: 16px 16px 16px 4px;
        padding: 12px 16px;
        margin: 8px auto 8px 0;
        max-width: 80%;
        color: #E0E0E0;
    }

    /* Navbar */
    .navbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px 32px;
        background: rgba(15, 15, 15, 0.6);
        backdrop-filter: blur(20px);
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        position: sticky;
        top: 0;
        z-index: 100;
    }

    .nav-logo {
        font-size: 24px;
        font-weight: 800;
        background: linear-gradient(135deg, #3B82F6, #8B5CF6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .nav-links {
        display: flex;
        gap: 24px;
    }

    .nav-link {
        color: rgba(224, 224, 224, 0.7);
        text-decoration: none;
        font-weight: 500;
        transition: color 0.3s;
    }

    .nav-link:hover {
        color: #3B82F6;
    }

    /* Hero Section */
    .hero {
        text-align: center;
        padding: 80px 20px;
        position: relative;
        overflow: hidden;
    }

    .hero h1 {
        font-size: 56px;
        font-weight: 800;
        background: linear-gradient(135deg, #E0E0E0, #3B82F6, #8B5CF6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 16px;
    }

    .hero p {
        font-size: 20px;
        color: rgba(224, 224, 224, 0.7);
        max-width: 600px;
        margin: 0 auto 32px;
    }

    /* Gradient orbs for background */
    .orb {
        position: fixed;
        border-radius: 50%;
        filter: blur(80px);
        opacity: 0.15;
        pointer-events: none;
        z-index: 0;
    }

    .orb-1 {
        width: 400px;
        height: 400px;
        background: #3B82F6;
        top: -100px;
        right: -100px;
    }

    .orb-2 {
        width: 300px;
        height: 300px;
        background: #8B5CF6;
        bottom: -50px;
        left: -50px;
    }

    .orb-3 {
        width: 200px;
        height: 200px;
        background: #EC4899;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
    }
    </style>

    <!-- Gradient Orbs -->
    <div class="orb orb-1"></div>
    <div class="orb orb-2"></div>
    <div class="orb orb-3"></div>
    """, unsafe_allow_html=True)

# ── SESSION STATE INIT ─────────────────────────────────────
def init_session():
    """Initialize session state variables."""
    defaults = {
        'user': None,
        'is_authenticated': False,
        'chat_session_token': None,
        'current_page': 'landing',
        'theme': 'dark',
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# ── AUTH FUNCTIONS ─────────────────────────────────────────
def login_user(email: str, password: str) -> bool:
    """Login user dan simpan ke session."""
    from backend.services import AuthService

    result = AuthService.login(email, password)
    if result.get('success'):
        st.session_state['user'] = result['user']
        st.session_state['is_authenticated'] = True
        return True
    return False


def logout_user():
    """Logout user."""
    st.session_state['user'] = None
    st.session_state['is_authenticated'] = False
    st.session_state['chat_session_token'] = None


# ── NAVBAR ────────────────────────────────────────────────
def render_navbar():
    """Render top navigation bar."""
    user = st.session_state.get('user')

    nav_html = """
    <div class="navbar">
        <div class="nav-logo">🤖 EventBot</div>
        <div class="nav-links">
    """

    if user:
        role = user.get('role', 'participant')
        nav_html += f"""
            <a href="/?page=chatbot" class="nav-link">💬 Chat</a>
            <a href="/?page=events" class="nav-link">📋 Events</a>
            <a href="/?page=profile" class="nav-link">👤 {user['name']}</a>
        """
        if role in ['admin', 'organizer']:
            nav_html += """
            <a href="/?page=dashboard" class="nav-link">📊 Dashboard</a>
            """
    else:
        nav_html += """
            <a href="/?page=landing" class="nav-link">🏠 Home</a>
            <a href="/?page=chatbot" class="nav-link">💬 Chat</a>
            <a href="/?page=events" class="nav-link">📋 Events</a>
            <a href="/?page=login" class="nav-link">🔐 Login</a>
        """

    nav_html += "</div></div>"
    st.markdown(nav_html, unsafe_allow_html=True)


# ── HERO SECTION ──────────────────────────────────────────
def render_hero():
    """Render landing page hero section."""
    st.markdown("""
    <div class="hero">
        <h1>Temukan Event Terbaikmu</h1>
        <p>Chatbot pintar untuk eksplorasi event, konferensi, dan workshop. 
        Cari, daftar, dan kelola event favoritmu dalam satu platform.</p>
    </div>
    """, unsafe_allow_html=True)

    # CTA Buttons
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("💬 Mulai Chat", use_container_width=True, type="primary"):
                st.session_state['current_page'] = 'chatbot'
                st.rerun()
        with c2:
            if st.button("📋 Jelajahi Event", use_container_width=True):
                st.session_state['current_page'] = 'events'
                st.rerun()


# ── FEATURED EVENTS ───────────────────────────────────────
def render_featured_events():
    """Render featured events section."""
    from backend.models import EventModel

    st.markdown("<h2 style='text-align: center; margin: 40px 0 20px;'>🎪 Event Unggulan</h2>", unsafe_allow_html=True)

    events = EventModel.search(limit=3)

    cols = st.columns(3)
    for i, event in enumerate(events):
        with cols[i]:
            st.markdown(f"""
            <div class="glass-card">
                <img src="{event.get('image_url', '')}" style="width:100%; border-radius:12px; margin-bottom:12px;" />
                <h3 style="color:#E0E0E0; margin:0;">{event['title']}</h3>
                <p style="color:rgba(224,224,224,0.6); font-size:14px;">
                    📅 {event.get('start_date', 'TBA')}<br>
                    📍 {event.get('location', 'TBA')}
                </p>
                <p style="color:#3B82F6; font-weight:600;">
                    💰 Rp {event.get('min_price', 0):,.0f}
                </p>
            </div>
            """, unsafe_allow_html=True)

            if st.button("Lihat Detail", key=f"event_{event['id']}", use_container_width=True):
                st.session_state['selected_event'] = event['id']
                st.session_state['current_page'] = 'event_detail'
                st.rerun()


# ── MAIN APP ──────────────────────────────────────────────
def main():
    """Main application entry point."""

    # Load CSS
    load_css()

    # Init session
    init_session()

    # Check DB connection
    try:
        test_connection()
    except Exception as e:
        st.error(f"❌ Database connection failed: {e}")
        st.info("Pastikan PostgreSQL running dan .env sudah dikonfigurasi.")
        return

    # Render navbar
    render_navbar()

    # Page routing
    page = st.query_params.get('page', st.session_state.get('current_page', 'landing'))

    if page == 'landing':
        render_hero()
        render_featured_events()

    elif page == 'chatbot':
        # Redirect ke page chatbot
        st.switch_page("pages/Chatbot.py")

    elif page == 'events':
        st.switch_page("pages/Event_Explorer.py")

    elif page == 'login':
        st.switch_page("pages/Login.py")

    elif page == 'profile':
        st.switch_page("pages/Profil_Saya.py")

    elif page == 'dashboard':
        st.switch_page("pages/Dashboard_Admin.py")

    else:
        render_hero()
        render_featured_events()


if __name__ == "__main__":
    main()