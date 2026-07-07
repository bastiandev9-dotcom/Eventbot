"""
Quick Reply Component
=====================
Tombol quick reply untuk chatbot.
"""

import streamlit as st
from typing import List, Optional, Callable


def render_quick_replies(
    replies: List[str],
    on_click: Optional[Callable[[str], None]] = None,
    key_prefix: str = "qr",
    max_per_row: int = 3,
) -> Optional[str]:
    """Render tombol quick reply horizontal."""
    if not replies:
        return None

    selected = None
    chunks = [replies[i:i + max_per_row] for i in range(0, len(replies), max_per_row)]

    for row_idx, chunk in enumerate(chunks):
        cols = st.columns(len(chunk))
        for col_idx, reply_text in enumerate(chunk):
            with cols[col_idx]:
                btn_key = key_prefix + "_r" + str(row_idx) + "c" + str(col_idx) + "_" + str(hash(reply_text) % 10000)
                if st.button(reply_text, key=btn_key, use_container_width=True):
                    selected = reply_text
                    if on_click:
                        on_click(reply_text)

    return selected


def render_quick_reply_chips(
    replies: List[str],
    key_prefix: str = "chip",
) -> Optional[str]:
    """Render quick replies sebagai chip buttons compact."""
    if not replies:
        return None

    selected = None
    n = len(replies)

    if n <= 4:
        cols = st.columns(n)
        for i, reply in enumerate(replies):
            with cols[i]:
                if st.button(reply, key=key_prefix + "_chip_" + str(i) + "_" + str(hash(reply) % 10000), use_container_width=True):
                    selected = reply
    else:
        half  = (n + 1) // 2
        row1  = replies[:half]
        row2  = replies[half:]
        cols1 = st.columns(len(row1))
        for i, reply in enumerate(row1):
            with cols1[i]:
                if st.button(reply, key=key_prefix + "_r1_" + str(i), use_container_width=True):
                    selected = reply
        cols2 = st.columns(len(row2))
        for i, reply in enumerate(row2):
            with cols2[i]:
                if st.button(reply, key=key_prefix + "_r2_" + str(i), use_container_width=True):
                    selected = reply

    return selected


def render_suggested_prompts(
    prompts: List[str],
    title: str = "💡 Coba tanya:",
    key_prefix: str = "suggest",
) -> Optional[str]:
    """Render suggested prompts di awal chat."""
    if not prompts:
        return None

    st.markdown(
        '<div style="margin:1rem 0;padding:1.25rem;background:rgba(255,255,255,0.03);'
        'border:1px solid rgba(255,255,255,0.07);border-radius:16px;">'
        '<div style="font-size:0.8rem;font-weight:600;color:#6B7280;margin-bottom:0.75rem;'
        'text-transform:uppercase;letter-spacing:0.05em;">' + title + '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    selected    = None
    cols_per_row = 2
    chunks      = [prompts[i:i + cols_per_row] for i in range(0, len(prompts), cols_per_row)]

    for row_idx, chunk in enumerate(chunks):
        cols = st.columns(len(chunk))
        for col_idx, prompt in enumerate(chunk):
            with cols[col_idx]:
                if st.button(prompt, key=key_prefix + "_p_" + str(row_idx) + "_" + str(col_idx), use_container_width=True):
                    selected = prompt

    return selected
