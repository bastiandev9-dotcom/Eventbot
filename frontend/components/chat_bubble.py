"""
Chat Bubble Component
=====================
Komponen gelembung chat untuk tampilan percakapan EventBot.
"""

import streamlit as st
from typing import Dict, Any, List, Optional
from utils.formatters import truncate_text

_TYPING_CSS = """<style>
@keyframes typing-dot{0%,80%,100%{transform:scale(0.6);opacity:0.4;}40%{transform:scale(1);opacity:1;}}
.t-dots{display:flex;align-items:center;gap:4px;padding:0.5rem 0;}
.t-dot{width:8px;height:8px;border-radius:50%;background:#ADB5BD;animation:typing-dot 1.4s ease-in-out infinite;}
.t-dot:nth-child(1){animation-delay:0s;}
.t-dot:nth-child(2){animation-delay:0.2s;}
.t-dot:nth-child(3){animation-delay:0.4s;}
</style>"""

_BUBBLE_CSS = """<style>
.bubble-user{display:flex;justify-content:flex-end;margin:0.5rem 0;}
.bubble-user-inner{background:linear-gradient(135deg,rgba(124,58,237,0.85),rgba(79,70,229,0.85));border:1px solid rgba(124,58,237,0.3);border-radius:16px 4px 16px 16px;padding:0.75rem 1rem;max-width:75%;color:white;font-size:0.9rem;line-height:1.5;word-wrap:break-word;}
.bubble-bot{display:flex;align-items:flex-start;gap:0.625rem;margin:0.5rem 0;}
.bot-av{width:32px;height:32px;border-radius:50%;background:linear-gradient(135deg,#7C3AED,#10B981);display:flex;align-items:center;justify-content:center;font-size:1rem;flex-shrink:0;}
.bubble-bot-inner{background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);border-radius:4px 16px 16px 16px;padding:0.75rem 1rem;max-width:75%;color:#F8F9FA;font-size:0.9rem;line-height:1.6;word-wrap:break-word;}
</style>"""


def render_chat_bubble(message: Dict[str, Any], key_suffix: str = "") -> None:
    """Render satu bubble chat (user atau bot)."""
    role        = message.get("role", "user")
    content     = message.get("content", "")
    event_cards = message.get("event_cards", [])

    st.markdown(_BUBBLE_CSS, unsafe_allow_html=True)

    if role == "user":
        st.markdown(
            '<div class="bubble-user">'
            '<div class="bubble-user-inner">' + content.replace("\n", "<br>") + '</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        import re
        fmt = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
        fmt = re.sub(r'\*(.+?)\*',     r'<em>\1</em>',         fmt)
        fmt = fmt.replace("\n", "<br>")
        st.markdown(
            '<div class="bubble-bot">'
            '<div class="bot-av">🤖</div>'
            '<div class="bubble-bot-inner">' + fmt + '</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        if event_cards:
            _render_event_cards_in_chat(event_cards, key_suffix)


def _render_event_cards_in_chat(event_cards: List[Dict], key_suffix: str) -> None:
    """Render event mini cards di dalam chat (tanpa nested columns)."""
    from utils.formatters import format_date, format_price

    for i, event in enumerate(event_cards[:3]):
        event_id   = str(event.get("id", ""))
        title      = event.get("title", "Event")
        location   = event.get("location", "-")
        start_date = event.get("start_date", "")
        tickets    = event.get("tickets", [])
        min_price  = min((t.get("price", 0) for t in tickets), default=0) if tickets else 0

        date_str  = format_date(start_date)
        price_str = format_price(min_price)

        st.markdown(
            '<div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);'
            'border-radius:10px;padding:0.75rem;margin:0.4rem 0 0.4rem 2.5rem;">'
            '<div style="font-weight:700;color:#F8F9FA;font-size:0.875rem;margin-bottom:0.25rem;">🎪 '
            + truncate_text(title, 40) +
            '</div>'
            '<div style="font-size:0.75rem;color:#9CA3AF;">📅 ' + date_str +
            ' · 📍 ' + truncate_text(location, 22) +
            ' · <span style="color:#10B981;font-weight:600;">' + price_str + '</span></div>'
            '</div>',
            unsafe_allow_html=True,
        )
        if st.button(
            "📄 Detail  |  ✅ Daftar",
            key="chat_ev_" + event_id + "_" + key_suffix + "_" + str(i),
            use_container_width=True,
            type="primary",
        ):
            st.session_state["detail_event_id"] = event_id
            st.session_state["current_page"]    = "Event_Explorer"
            st.rerun()


def render_typing_indicator() -> None:
    """Render animasi typing indicator."""
    st.markdown(_TYPING_CSS, unsafe_allow_html=True)
    st.markdown(
        '<div style="display:flex;align-items:center;gap:0.625rem;margin:0.5rem 0;">'
        '<div style="width:32px;height:32px;border-radius:50%;'
        'background:linear-gradient(135deg,#7C3AED,#10B981);display:flex;align-items:center;'
        'justify-content:center;font-size:1rem;flex-shrink:0;">🤖</div>'
        '<div style="background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);'
        'border-radius:4px 16px 16px 16px;padding:0.5rem 1rem;">'
        '<div class="t-dots">'
        '<div class="t-dot"></div>'
        '<div class="t-dot"></div>'
        '<div class="t-dot"></div>'
        '</div></div></div>',
        unsafe_allow_html=True,
    )


def render_chat_history(messages: list) -> None:
    """Render seluruh history percakapan."""
    if not messages:
        st.markdown(
            '<div style="text-align:center;padding:2rem;color:#4B5563;">'
            '<div style="font-size:2rem;margin-bottom:0.5rem;">💬</div>'
            '<div>Mulai percakapan dengan EventBot!</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        return
    for i, msg in enumerate(messages):
        render_chat_bubble(msg, key_suffix=str(i))


def render_chat_input_area(
    placeholder: str = "Ketik pesan...",
    key: str = "chat_input",
) -> Optional[str]:
    """Render area input chat."""
    with st.form(key="chat_form_" + key, clear_on_submit=True):
        col_input, col_send = st.columns([10, 1])
        with col_input:
            user_input = st.text_input(
                "pesan", label_visibility="collapsed",
                placeholder=placeholder, key="input_" + key,
            )
        with col_send:
            submitted = st.form_submit_button("📤", use_container_width=True)
    if submitted and user_input and user_input.strip():
        return user_input.strip()
    return None
