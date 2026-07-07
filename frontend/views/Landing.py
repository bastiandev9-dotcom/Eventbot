"""
Landing Page — EventBot
"""

import streamlit as st
from components.hero_section import render_hero, render_section_header
from components.event_card import render_event_grid
from components.footer import render_footer
from components.toast import render_toast
from hooks.use_events import use_events
from hooks.use_theme import use_theme

_CSS = """<style>
.feat-card{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:16px;padding:1.5rem 1.25rem;text-align:center;height:100%;}
.feat-icon{font-size:2rem;margin-bottom:0.875rem;}
.feat-title{font-weight:700;color:#F8F9FA;font-size:1rem;margin-bottom:0.5rem;}
.feat-desc{font-size:0.825rem;color:#6B7280;line-height:1.6;}
.step-num{width:48px;height:48px;border-radius:50%;background:linear-gradient(135deg,#7C3AED,#4F46E5);display:flex;align-items:center;justify-content:center;font-size:1.25rem;font-weight:800;color:white;margin:0 auto 0.875rem;box-shadow:0 4px 15px rgba(124,58,237,0.4);}
.step-title{font-weight:700;color:#F8F9FA;font-size:0.95rem;margin-bottom:0.4rem;}
.step-desc{font-size:0.8rem;color:#6B7280;line-height:1.5;text-align:center;}
</style>"""


def render() -> None:
    theme = use_theme()
    theme["apply_theme"]()
    render_toast()

    render_hero(
        title="Temukan Event Seru\ndi Sekitarmu 🎪",
        subtitle=(
            "EventBot — asisten cerdas berbasis NLP yang membantu kamu "
            "menemukan, mendaftar, dan mengelola event favorit. "
            "Cukup ketik, dan biarkan bot mengurusnya!"
        ),
        show_cta=True,
    )

    events_hook = use_events()

    # Trending
    render_section_header("Event Trending 🔥", subtitle="Event paling banyak diminati")
    with st.spinner("Memuat..."):
        trending, err = events_hook["fetch_trending"](limit=6)
    if err or not trending:
        _render_placeholder_events()
        if err:
            st.caption("⚠️ Backend belum terhubung — data demo")
    else:
        render_event_grid(events=trending, columns=3, grid_key="trending")

    st.markdown("<br>", unsafe_allow_html=True)

    # Upcoming
    render_section_header("Event Akan Datang 📅", subtitle="Jangan sampai ketinggalan!")
    with st.spinner("Memuat..."):
        upcoming, err2 = events_hook["fetch_upcoming"](limit=3)
    if not err2 and upcoming:
        render_event_grid(events=upcoming, columns=3, grid_key="upcoming")
    else:
        st.markdown(
            '<div style="text-align:center;padding:2rem;background:rgba(255,255,255,0.03);'
            'border:1px solid rgba(255,255,255,0.07);border-radius:16px;color:#6B7280;margin-bottom:1.5rem;">'
            '<div style="font-size:2rem;margin-bottom:0.5rem;">📅</div>'
            '<div>Belum ada event mendatang.</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    render_section_header("Kenapa EventBot? 💡", align="center")
    _render_features()

    st.markdown("<br>", unsafe_allow_html=True)
    render_section_header("Cara Pakai 🚀", align="center")
    _render_steps()

    render_footer()


def _render_placeholder_events() -> None:
    demo = [
        {"id": "p_" + str(i), "title": "Demo Event " + str(i+1),
         "short_description": "Event seru yang wajib dihadiri.",
         "location": ["Jakarta", "Bandung", "Online"][i % 3],
         "start_date": "2026-08-15", "status": "upcoming",
         "tickets": [{"price": [0, 150000, 250000][i % 3]}],
         "registered_count": 50 + i * 30, "capacity": 200}
        for i in range(3)
    ]
    render_event_grid(events=demo, columns=3, grid_key="placeholder")


def _render_features() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
    features = [
        ("🤖", "AI Chatbot",      "Tanya apapun tentang event. Bot mengerti bahasa natural."),
        ("🔍", "Cari & Filter",   "Filter event berdasarkan kategori, lokasi, tanggal, harga."),
        ("🎫", "Booking Mudah",   "Daftar dan pesan tiket hanya dalam beberapa klik."),
        ("📊", "Dashboard Admin", "Kelola event, peserta, dan tiket dari satu dashboard."),
    ]
    cols = st.columns(4)
    for i, (icon, title, desc) in enumerate(features):
        with cols[i]:
            st.markdown(
                '<div class="feat-card"><div class="feat-icon">' + icon + '</div>'
                '<div class="feat-title">' + title + '</div>'
                '<div class="feat-desc">' + desc + '</div></div>',
                unsafe_allow_html=True,
            )


def _render_steps() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
    steps = [
        ("1", "Buka Chatbot",    "Klik tombol Chat, mulai percakapan."),
        ("2", "Tanya EventBot",  "Ketik 'cari event teknologi' atau 'event gratis'."),
        ("3", "Pilih Event",     "Bot menampilkan rekomendasi event untukmu."),
        ("4", "Daftar & Nikmati","Klik Daftar, selesaikan pemesanan, dan hadir!"),
    ]
    cols = st.columns(4)
    for i, (num, title, desc) in enumerate(steps):
        with cols[i]:
            st.markdown(
                '<div style="text-align:center;">'
                '<div class="step-num">' + num + '</div>'
                '<div class="step-title">' + title + '</div>'
                '<div class="step-desc">' + desc + '</div></div>',
                unsafe_allow_html=True,
            )
