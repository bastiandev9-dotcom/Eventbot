"""
About & Contact Page — EventBot
"""

import streamlit as st
from components.footer import render_footer
from components.toast import render_toast, queue_toast
from hooks.use_theme import use_theme

_TECH_CSS = """<style>
.tech-card{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:1.25rem;display:flex;align-items:center;gap:0.875rem;margin-bottom:0.75rem;}
.tech-icon{font-size:1.5rem;width:44px;height:44px;border-radius:10px;background:rgba(255,255,255,0.05);display:flex;align-items:center;justify-content:center;flex-shrink:0;}
.tech-name{font-weight:700;color:#F8F9FA;font-size:0.95rem;}
.tech-desc{font-size:0.75rem;color:#6B7280;margin-top:0.1rem;}
</style>"""


def render() -> None:
    theme = use_theme()
    theme["apply_theme"]()
    render_toast()

    # Hero
    st.markdown(
        '<div style="text-align:center;padding:3rem 2rem 2rem;'
        'background:linear-gradient(135deg,rgba(124,58,237,0.1),rgba(16,185,129,0.05));'
        'border:1px solid rgba(255,255,255,0.07);border-radius:24px;margin-bottom:2.5rem;">'
        '<div style="font-size:3rem;margin-bottom:0.75rem;">🎪</div>'
        '<h1 style="font-size:2.25rem;font-weight:800;background:linear-gradient(135deg,#7C3AED,#4F46E5,#10B981);'
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin:0 0 0.5rem;">EventBot</h1>'
        '<p style="font-size:1rem;color:#9CA3AF;max-width:550px;margin:0 auto;line-height:1.7;">'
        'Platform chatbot cerdas berbasis NLP untuk membantu kamu menemukan, mendaftar, dan mengelola event favorit.</p>'
        '<div style="display:flex;justify-content:center;gap:0.75rem;flex-wrap:wrap;margin-top:1.5rem;">'
        '<span style="background:rgba(124,58,237,0.12);border:1px solid rgba(124,58,237,0.25);'
        'color:#8B5CF6;padding:0.3rem 0.875rem;border-radius:9999px;font-size:0.8rem;font-weight:600;">v1.0.0</span>'
        '<span style="background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.25);'
        'color:#10B981;padding:0.3rem 0.875rem;border-radius:9999px;font-size:0.8rem;font-weight:600;">Open Source</span>'
        '<span style="background:rgba(59,130,246,0.1);border:1px solid rgba(59,130,246,0.25);'
        'color:#3B82F6;padding:0.3rem 0.875rem;border-radius:9999px;font-size:0.8rem;font-weight:600;">NLP Powered</span>'
        '</div></div>',
        unsafe_allow_html=True,
    )

    # Tech Stack
    st.markdown('<h2 style="font-size:1.35rem;font-weight:700;color:#F8F9FA;margin-bottom:1.25rem;">🛠️ Tech Stack</h2>',
                unsafe_allow_html=True)
    st.markdown(_TECH_CSS, unsafe_allow_html=True)

    tech_stack = [
        ("⚡", "Streamlit",  "Frontend UI Framework"),
        ("🚀", "FastAPI",    "Backend REST API"),
        ("🐘", "PostgreSQL", "Relational Database"),
        ("🤖", "Regex NLP",  "Intent Recognition Engine"),
        ("🐍", "Python 3.12","Programming Language"),
        ("📦", "Psycopg2",   "PostgreSQL DB Adapter"),
    ]
    cols = st.columns(3)
    for i, (icon, name, desc) in enumerate(tech_stack):
        with cols[i % 3]:
            st.markdown(
                '<div class="tech-card">'
                '<div class="tech-icon">' + icon + '</div>'
                '<div><div class="tech-name">' + name + '</div>'
                '<div class="tech-desc">' + desc + '</div></div>'
                '</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # Fitur Utama
    st.markdown('<h2 style="font-size:1.35rem;font-weight:700;color:#F8F9FA;margin-bottom:1.25rem;">✨ Fitur Utama</h2>',
                unsafe_allow_html=True)
    features = [
        ("🤖 Chatbot NLP",     "Chatbot berbasis regex pattern matching yang mengenali intent dari bahasa natural Bahasa Indonesia."),
        ("📋 Event Explorer",  "Browse dan filter event berdasarkan kategori, lokasi, tanggal, dan harga secara real-time."),
        ("🎫 Booking Tiket",   "Proses pendaftaran dan pemesanan tiket event yang mudah dan cepat."),
        ("📊 Admin Dashboard", "Dashboard analytics dengan chart dan statistik penggunaan platform."),
        ("👥 User Management", "Manajemen akun user, role assignment, dan kontrol akses berbasis role."),
        ("📚 Knowledge Base",  "Editor FAQ dan training data chatbot yang dapat dikelola admin."),
    ]
    for ftitle, fdesc in features:
        with st.expander(ftitle):
            st.markdown('<p style="color:#ADB5BD;font-size:0.9rem;line-height:1.6;margin:0;">' + fdesc + '</p>',
                        unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Feedback
    st.markdown('<h2 style="font-size:1.35rem;font-weight:700;color:#F8F9FA;margin-bottom:1.25rem;">💌 Kirim Feedback</h2>',
                unsafe_allow_html=True)
    with st.form("feedback_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            fb_name  = st.text_input("Nama", placeholder="Nama kamu")
        with c2:
            fb_email = st.text_input("Email", placeholder="email@contoh.com")
        fb_type  = st.selectbox("Jenis Feedback", ["💡 Saran Fitur","🐛 Laporan Bug","👍 Pujian","❓ Pertanyaan","Lainnya"])
        fb_msg   = st.text_area("Pesan *", placeholder="Tulis feedback kamu di sini...", height=120)
        fb_rating = st.select_slider("Rating Kepuasan", options=["😞 1","😐 2","🙂 3","😊 4","🤩 5"], value="🙂 3")
        if st.form_submit_button("📨 Kirim Feedback", type="primary", use_container_width=True):
            if not fb_msg:
                st.error("Pesan tidak boleh kosong.")
            else:
                queue_toast("Terima kasih atas feedback-mu! 🙏", "success")
                st.rerun()

    render_footer()
