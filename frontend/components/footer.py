"""
Footer Component
================
Footer halaman EventBot.
"""

import streamlit as st

_FOOTER_CSS = """<style>
.eventbot-footer{margin-top:4rem;padding:2rem 0 1rem;border-top:1px solid rgba(255,255,255,0.06);text-align:center;}
.footer-brand{font-size:1.1rem;font-weight:700;background:linear-gradient(135deg,#7C3AED,#10B981);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:0.5rem;}
.footer-tagline{font-size:0.8rem;color:#4B5563;margin-bottom:1rem;}
.footer-links{display:flex;justify-content:center;align-items:center;gap:0.5rem;margin-bottom:1rem;}
.footer-links a{color:#6B7280;text-decoration:none;font-size:0.8rem;transition:color 0.2s ease;}
.footer-links a:hover{color:#7C3AED;}
.footer-links span{color:#374151;}
.footer-copy{font-size:0.75rem;color:#374151;}
</style>"""


def render_footer(show_links: bool = True) -> None:
    """Render footer halaman EventBot."""
    st.markdown(_FOOTER_CSS, unsafe_allow_html=True)

    links_html = ""
    if show_links:
        links_html = (
            '<div class="footer-links">'
            '<a href="?page=Landing">Beranda</a>'
            '<span>·</span>'
            '<a href="?page=Chatbot">Chatbot</a>'
            '<span>·</span>'
            '<a href="?page=Event_Explorer">Event</a>'
            '<span>·</span>'
            '<a href="?page=About">Tentang</a>'
            "</div>"
        )

    html = (
        '<div class="eventbot-footer">'
        '<div class="footer-brand">🎪 EventBot</div>'
        '<div class="footer-tagline">Chatbot Cerdas untuk Manajemen Event</div>'
        + links_html +
        '<div class="footer-copy">© 2026 EventBot · Dibangun dengan ❤️ menggunakan Streamlit & FastAPI</div>'
        "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)
