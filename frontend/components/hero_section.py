"""
Hero Section Component
======================
Hero / landing section dengan gradient animation, CTA buttons,
dan showcase event unggulan.
"""

import streamlit as st
from typing import Optional, List, Dict


# ── CSS dipisah dari HTML agar tidak ada konflik f-string {{}} ──
_HERO_CSS = """
<style>
.hero-section {
    background: linear-gradient(135deg,
        rgba(124, 58, 237, 0.12) 0%,
        rgba(79, 70, 229, 0.06) 40%,
        rgba(16, 185, 129, 0.06) 100%
    );
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 24px;
    padding: 4rem 3rem;
    text-align: center;
    position: relative;
    overflow: hidden;
    margin-bottom: 2rem;
    animation: fadeInUp 0.6s ease forwards;
}
.hero-section::before {
    content: '';
    position: absolute;
    top: -40%;
    left: -20%;
    width: 60%;
    height: 200%;
    background: radial-gradient(ellipse, rgba(124,58,237,0.07) 0%, transparent 70%);
    pointer-events: none;
}
.hero-section::after {
    content: '';
    position: absolute;
    bottom: -40%;
    right: -20%;
    width: 60%;
    height: 200%;
    background: radial-gradient(ellipse, rgba(16,185,129,0.05) 0%, transparent 70%);
    pointer-events: none;
}
.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: rgba(124,58,237,0.12);
    border: 1px solid rgba(124,58,237,0.25);
    color: #8B5CF6;
    padding: 0.3rem 0.875rem;
    border-radius: 9999px;
    font-size: 0.8rem;
    font-weight: 600;
    margin-bottom: 1.5rem;
}
.hero-title {
    font-size: clamp(2rem, 5vw, 3.5rem);
    font-weight: 800;
    line-height: 1.15;
    color: #F8F9FA;
    margin-bottom: 1.25rem;
}
.hero-title .highlight {
    background: linear-gradient(135deg, #7C3AED, #4F46E5, #10B981);
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hero-subtitle {
    font-size: 1.1rem;
    color: #9CA3AF;
    max-width: 600px;
    margin: 0 auto 2.5rem;
    line-height: 1.7;
}
.hero-stats {
    display: flex;
    justify-content: center;
    gap: 2rem;
    flex-wrap: wrap;
    margin-top: 2.5rem;
    padding-top: 2rem;
    border-top: 1px solid rgba(255,255,255,0.06);
}
.hero-stat {
    text-align: center;
}
.hero-stat-value {
    font-size: 1.75rem;
    font-weight: 800;
    background: linear-gradient(135deg, #7C3AED, #10B981);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.2;
}
.hero-stat-label {
    font-size: 0.8rem;
    color: #6B7280;
    margin-top: 0.2rem;
}
.hero-particle {
    position: absolute;
    border-radius: 50%;
    pointer-events: none;
    opacity: 0.4;
}
</style>
"""

_SECTION_HEADER_CSS = """
<style>
.section-hdr { margin-bottom: 1.5rem; }
.section-hdr h2 {
    font-size: 1.5rem;
    font-weight: 700;
    color: #F8F9FA;
    margin: 0 0 0.25rem;
    line-height: 1.3;
}
.section-hdr p {
    color: #6B7280;
    font-size: 0.9rem;
    margin: 0;
}
</style>
"""


def render_hero(
    title: str = "Temukan Event Seru\ndi Sekitarmu 🎪",
    subtitle: str = (
        "EventBot — asisten cerdas berbasis NLP yang membantu kamu "
        "menemukan, mendaftar, dan mengelola event favorit. "
        "Cukup ketik, dan biarkan bot mengurusnya!"
    ),
    show_cta: bool = True,
    stats: Optional[List[Dict]] = None,
) -> None:
    """
    Render hero section halaman utama.

    Args:
        title: Judul utama hero (bisa multi-line dengan \\n)
        subtitle: Teks deskripsi di bawah judul
        show_cta: Tampilkan tombol CTA
        stats: List dict {'label': str, 'value': str} untuk statistik
    """
    if stats is None:
        stats = [
            {"value": "500+", "label": "Event Aktif"},
            {"value": "10K+", "label": "Peserta"},
            {"value": "50+",  "label": "Kategori"},
            {"value": "99%",  "label": "Kepuasan"},
        ]

    # ── 1. Inject CSS (terpisah, tidak ada f-string) ──────
    st.markdown(_HERO_CSS, unsafe_allow_html=True)

    # ── 2. Build HTML strings secara Python biasa ─────────
    title_html = title.replace("\n", "<br>").replace(
        "Event", '<span class="highlight">Event</span>', 1
    )

    stats_parts = []
    for s in stats:
        stats_parts.append(
            '<div class="hero-stat">'
            '<div class="hero-stat-value">' + s["value"] + "</div>"
            '<div class="hero-stat-label">' + s["label"] + "</div>"
            "</div>"
        )
    stats_html = "\n".join(stats_parts)

    hero_html = (
        '<div class="hero-section">'
        '<div class="hero-particle" style="width:120px;height:120px;'
        "background:radial-gradient(circle,rgba(124,58,237,0.15),transparent);"
        'top:10%;left:5%;animation:float 6s ease-in-out infinite;"></div>'
        '<div class="hero-particle" style="width:80px;height:80px;'
        "background:radial-gradient(circle,rgba(16,185,129,0.12),transparent);"
        'top:20%;right:8%;animation:float 8s ease-in-out infinite 1s;"></div>'
        '<div class="hero-badge">✨ Bertenaga NLP · Regex Intelligence</div>'
        '<h1 class="hero-title">' + title_html + "</h1>"
        '<p class="hero-subtitle">' + subtitle + "</p>"
        '<div class="hero-stats">' + stats_html + "</div>"
        "</div>"
    )

    # ── 3. Render HTML (tanpa f-string) ───────────────────
    st.markdown(hero_html, unsafe_allow_html=True)

    # ── 4. CTA Buttons via Streamlit native ───────────────
    if show_cta:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            cta_col1, cta_col2 = st.columns(2)
            with cta_col1:
                if st.button(
                    "💬 Chat dengan Bot",
                    key="hero_cta_chat",
                    use_container_width=True,
                    type="primary",
                ):
                    st.session_state["current_page"] = "Chatbot"
                    st.rerun()
            with cta_col2:
                if st.button(
                    "📋 Jelajahi Event",
                    key="hero_cta_explore",
                    use_container_width=True,
                ):
                    st.session_state["current_page"] = "Event_Explorer"
                    st.rerun()


def render_section_header(
    title: str,
    subtitle: str = "",
    emoji: str = "",
    align: str = "left",
) -> None:
    """
    Render section header dengan styling konsisten.
    """
    st.markdown(_SECTION_HEADER_CSS, unsafe_allow_html=True)

    prefix = (emoji + " ") if emoji else ""
    subtitle_part = (
        '<p style="color:#6B7280;font-size:0.9rem;margin-top:0.25rem;">'
        + subtitle + "</p>"
    ) if subtitle else ""

    html = (
        '<div class="section-hdr" style="text-align:' + align + ';">'
        "<h2>" + prefix + title + "</h2>"
        + subtitle_part +
        "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)
