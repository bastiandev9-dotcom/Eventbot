"""
Chatbot Page
============
Interface chat utama EventBot dengan glassmorphism UI.
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.services import ChatbotService
from backend.models import ChatSessionModel

st.set_page_config(page_title="Chat - EventBot", page_icon="💬", layout="wide")

# ── CUSTOM CSS ────────────────────────────────────────────
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0F0F0F 0%, #1A1A2E 50%, #16213E 100%);
}

.chat-container {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
}

.chat-header {
    text-align: center;
    padding: 20px;
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(16px);
    border-radius: 16px;
    margin-bottom: 20px;
    border: 1px solid rgba(255,255,255,0.1);
}

.chat-header h2 {
    margin: 0;
    background: linear-gradient(135deg, #3B82F6, #8B5CF6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.message-user {
    background: rgba(59, 130, 246, 0.2);
    border: 1px solid rgba(59, 130, 246, 0.3);
    border-radius: 16px 16px 4px 16px;
    padding: 12px 16px;
    margin: 8px 0 8px auto;
    max-width: 75%;
    color: #E0E0E0;
    word-wrap: break-word;
}

.message-bot {
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px 16px 16px 4px;
    padding: 12px 16px;
    margin: 8px auto 8px 0;
    max-width: 75%;
    color: #E0E0E0;
    word-wrap: break-word;
}

.quick-reply-btn {
    display: inline-block;
    background: rgba(59, 130, 246, 0.15);
    border: 1px solid rgba(59, 130, 246, 0.3);
    border-radius: 20px;
    padding: 8px 16px;
    margin: 4px;
    color: #3B82F6;
    cursor: pointer;
    transition: all 0.3s;
}

.quick-reply-btn:hover {
    background: rgba(59, 130, 246, 0.3);
}

.chat-input-container {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    padding: 20px;
    background: rgba(15, 15, 15, 0.9);
    backdrop-filter: blur(20px);
    border-top: 1px solid rgba(255,255,255,0.1);
}

.typing-indicator {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 12px 16px;
    color: rgba(224,224,224,0.6);
    font-style: italic;
}

.dot {
    width: 8px;
    height: 8px;
    background: #3B82F6;
    border-radius: 50%;
    animation: bounce 1.4s infinite ease-in-out;
}

.dot:nth-child(1) { animation-delay: -0.32s; }
.dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
    0%, 80%, 100% { transform: scale(0); }
    40% { transform: scale(1); }
}
</style>
""", unsafe_allow_html=True)

# ── INIT SESSION ──────────────────────────────────────────
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []

if 'chat_session_token' not in st.session_state:
    st.session_state.chat_session_token = None

if 'chatbot' not in st.session_state:
    st.session_state.chatbot = ChatbotService()

# ── HEADER ────────────────────────────────────────────────
st.markdown("""
<div class="chat-header">
    <h2>🤖 EventBot</h2>
    <p style="color:rgba(224,224,224,0.6); margin:0;">Asisten virtual untuk event & konferensi</p>
</div>
""", unsafe_allow_html=True)

# ── CHAT HISTORY ──────────────────────────────────────────
chat_container = st.container()

with chat_container:
    for msg in st.session_state.chat_messages:
        if msg['role'] == 'user':
            st.markdown(f'<div class="message-user">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="message-bot">{msg["content"]}</div>', unsafe_allow_html=True)

            # Quick replies
            if msg.get('quick_replies'):
                cols = st.columns(len(msg['quick_replies']))
                for i, reply in enumerate(msg['quick_replies']):
                    with cols[i]:
                        if st.button(reply, key=f"qr_{msg['timestamp']}_{i}", use_container_width=True):
                            process_message(reply)
                            st.rerun()

# ── INPUT ────────────────────────────────────────────────
def process_message(message: str):
    """Process user message."""
    if not message.strip():
        return

    # Add user message
    import time
    timestamp = int(time.time() * 1000)
    st.session_state.chat_messages.append({
        'role': 'user',
        'content': message,
        'timestamp': timestamp
    })

    # Get bot response
    user_id = st.session_state.get('user', {}).get('id') if st.session_state.get('user') else None

    result = st.session_state.chatbot.process_message(
        message,
        session_token=st.session_state.chat_session_token,
        user_id=user_id
    )

    # Update session token
    st.session_state.chat_session_token = result['session_token']

    # Add bot response
    st.session_state.chat_messages.append({
        'role': 'assistant',
        'content': result['response'],
        'quick_replies': result.get('quick_replies', []),
        'timestamp': timestamp + 1
    })

# Input area
st.markdown('<div style="height:100px;"></div>', unsafe_allow_html=True)  # Spacer

with st.container():
    col1, col2 = st.columns([6, 1])
    with col1:
        user_input = st.chat_input("Ketik pesan Anda...", key="chat_input")

    if user_input:
        process_message(user_input)
        st.rerun()

# ── SIDEBAR ───────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 💬 Chat Menu")

    if st.button("🆕 Chat Baru", use_container_width=True):
        st.session_state.chat_messages = []
        st.session_state.chat_session_token = None
        st.rerun()

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.chat_messages = []
        st.rerun()

    st.markdown("---")
    st.markdown("### 📋 Quick Actions")

    quick_actions = [
        "🔍 Cari Event",
        "📅 Event Saya",
        "❓ Bantuan"
    ]

    for action in quick_actions:
        if st.button(action, use_container_width=True, key=f"qa_{action}"):
            process_message(action)
            st.rerun()

    st.markdown("---")
    st.markdown("### 👤 User")

    user = st.session_state.get('user')
    if user:
        st.write(f"**{user['name']}**")
        st.write(f"_{user['role']}_")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.user = None
            st.session_state.is_authenticated = False
            st.rerun()
    else:
        st.write("Belum login")
        if st.button("🔐 Login", use_container_width=True):
            st.switch_page("pages/4_🔐_Login.py")