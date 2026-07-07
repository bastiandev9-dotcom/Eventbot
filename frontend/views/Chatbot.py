"""
Chatbot Page
============
Interface chat utama EventBot — percakapan NLP dengan bot.
Tema: Frost UI / Glassmorphism Soft
"""

import streamlit as st
from components.chat_bubble import render_chat_bubble, render_typing_indicator
from components.quick_reply import render_quick_replies, render_suggested_prompts
from components.toast import render_toast
from hooks.use_chat import use_chat
from hooks.use_theme import use_theme


def render() -> None:
    """Entry point halaman Chatbot."""
    theme = use_theme()
    theme["apply_theme"]()
    render_toast()

    chat = use_chat()

    # Pastikan ada welcome message di awal
    chat["ensure_welcome_message"]()

    # ── Header ────────────────────────────────────────────
    st.markdown("""
    <div style="
        display:flex; align-items:center; gap:0.75rem;
        margin-bottom:1.5rem;
        padding-bottom:1rem;
        border-bottom:1px solid rgba(255,255,255,0.07);
    ">
        <div style="
            width:44px; height:44px; border-radius:50%;
            background:linear-gradient(135deg,#7C3AED,#10B981);
            display:flex; align-items:center; justify-content:center;
            font-size:1.25rem;
            box-shadow:0 4px 15px rgba(124,58,237,0.35);
        ">🤖</div>
        <div>
            <div style="font-weight:800; color:#F8F9FA; font-size:1.1rem; line-height:1.2;">
                EventBot
            </div>
            <div style="display:flex; align-items:center; gap:0.35rem; font-size:0.75rem; color:#10B981;">
                <span style="
                    width:7px; height:7px; border-radius:50%;
                    background:#10B981;
                    box-shadow:0 0 6px #10B981;
                    display:inline-block;
                "></span>
                Online · Siap membantu
            </div>
        </div>
        <div style="margin-left:auto;">
    """, unsafe_allow_html=True)

    # Tombol hapus chat
    col_clear, col_gap = st.columns([1, 4])
    with col_clear:
        if st.button("🗑️", key="btn_clear_chat", help="Hapus riwayat chat"):
            chat["clear_history"]()
            st.rerun()

    st.markdown("</div></div>", unsafe_allow_html=True)

    # ── Area Chat ─────────────────────────────────────────
    messages = chat["messages"]

    # Container scroll area chat
    chat_container = st.container()
    with chat_container:
        if not messages:
            # Tampilkan suggested prompts saat chat kosong
            st.markdown("""
            <div style="text-align:center; padding:2rem 0 1rem; color:#6B7280;">
                <div style="font-size:2.5rem; margin-bottom:0.5rem;">💬</div>
                <div style="font-size:0.95rem; color:#ADB5BD;">Mulai percakapan dengan EventBot</div>
            </div>
            """, unsafe_allow_html=True)

            suggested = chat["get_suggested_questions"]()
            selected = render_suggested_prompts(suggested, key_prefix="welcome_suggest")
            if selected:
                _send_and_rerun(chat, selected)
        else:
            # Render semua pesan
            for i, msg in enumerate(messages):
                render_chat_bubble(msg, key_suffix=str(i))

                # Render quick replies hanya untuk pesan bot terakhir
                if (
                    msg.get("role") == "bot"
                    and i == len(messages) - 1
                    and msg.get("quick_replies")
                ):
                    selected_qr = render_quick_replies(
                        replies=msg["quick_replies"],
                        key_prefix=f"qr_{i}",
                        max_per_row=4,
                    )
                    if selected_qr:
                        _send_and_rerun(chat, selected_qr)

            # Typing indicator
            if chat["is_typing"]:
                render_typing_indicator()

    # ── Input Area ────────────────────────────────────────
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    _render_input_area(chat)

    # ── Info Bar ──────────────────────────────────────────
    st.markdown("""
    <div style="
        text-align:center; margin-top:0.75rem;
        font-size:0.72rem; color:#374151;
    ">
        💡 Tips: Coba ketik "event teknologi Jakarta" atau "event gratis minggu ini"
    </div>
    """, unsafe_allow_html=True)


def _render_input_area(chat: dict) -> None:
    """Render area input pesan chat."""
    st.markdown("""
    <style>
    .chat-input-wrapper {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 0.75rem;
    }
    </style>
    """, unsafe_allow_html=True)

    with st.form("chat_input_form", clear_on_submit=True):
        col_input, col_send = st.columns([11, 1])
        with col_input:
            user_text = st.text_input(
                "pesan",
                label_visibility="collapsed",
                placeholder="Ketik pesan kamu... (contoh: cari event teknologi)",
                key="chat_text_input",
            )
        with col_send:
            submitted = st.form_submit_button(
                "📤",
                use_container_width=True,
                help="Kirim pesan",
            )

        if submitted and user_text and user_text.strip():
            _send_and_rerun(chat, user_text.strip())


def _send_and_rerun(chat: dict, text: str) -> None:
    """Kirim pesan dan rerun halaman."""
    # Set typing sebelum kirim agar UI update duluan
    st.session_state["chat_is_typing"] = True
    success, response = chat["send_message"](text)
    st.rerun()
