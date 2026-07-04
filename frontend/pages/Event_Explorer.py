"""
Event Explorer Page
===================
Browse, search, dan filter event dengan card grid.
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.models import EventModel, CategoryModel

st.set_page_config(page_title="Events - EventBot", page_icon="📋", layout="wide")

# ── CUSTOM CSS ────────────────────────────────────────────
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0F0F0F 0%, #1A1A2E 50%, #16213E 100%);
}

.event-card {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    overflow: hidden;
    transition: all 0.3s ease;
    height: 100%;
}

.event-card:hover {
    transform: translateY(-8px);
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
    border-color: rgba(59, 130, 246, 0.3);
}

.event-image {
    width: 100%;
    height: 180px;
    object-fit: cover;
    border-radius: 16px 16px 0 0;
}

.event-content {
    padding: 16px;
}

.event-title {
    font-size: 18px;
    font-weight: 700;
    color: #E0E0E0;
    margin: 0 0 8px 0;
    line-height: 1.3;
}

.event-meta {
    font-size: 13px;
    color: rgba(224, 224, 224, 0.6);
    margin: 4px 0;
}

.event-price {
    font-size: 16px;
    font-weight: 700;
    color: #3B82F6;
    margin: 8px 0;
}

.event-status {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
}

.status-upcoming {
    background: rgba(59, 130, 246, 0.2);
    color: #3B82F6;
}

.status-ongoing {
    background: rgba(16, 185, 129, 0.2);
    color: #10B981;
}

.filter-sidebar {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 20px;
}

.search-box {
    background: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 12px !important;
}
</style>
""", unsafe_allow_html=True)

# ── HEADER ────────────────────────────────────────────────
st.markdown("""
<div style="text-align: center; padding: 40px 20px;">
    <h1 style="font-size: 42px; font-weight: 800; background: linear-gradient(135deg, #E0E0E0, #3B82F6); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        📋 Event Explorer
    </h1>
    <p style="color: rgba(224,224,224,0.6); font-size: 18px;">
        Temukan event menarik sesuai minatmu
    </p>
</div>
""", unsafe_allow_html=True)

# ── SIDEBAR FILTERS ───────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="filter-sidebar">', unsafe_allow_html=True)
    st.markdown("### 🔍 Filter")

    # Search
    search_query = st.text_input("Cari event...", placeholder="Nama event, lokasi...")

    # Categories
    categories = CategoryModel.list_all()
    category_options = ["Semua"] + [c['name'] for c in categories]
    selected_category = st.selectbox("Kategori", category_options)

    # Location
    location_filter = st.text_input("Lokasi", placeholder="Jakarta, Bandung...")

    # Price range
    price_range = st.select_slider(
        "Rentang Harga",
        options=["Gratis", "< 100K", "100K - 500K", "500K - 1Jt", "> 1Jt"],
        value="Gratis"
    )

    # Date
    date_filter = st.date_input("Tanggal", value=None)

    # Status
    status_filter = st.multiselect(
        "Status",
        ["upcoming", "ongoing", "completed"],
        default=["upcoming"]
    )

    if st.button("🔄 Reset Filter", use_container_width=True):
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# ── BUILD FILTERS ─────────────────────────────────────────
filters = {
    'limit': 24,
    'offset': 0
}

if search_query:
    filters['query'] = search_query

if selected_category != "Semua":
    cat_slug = next((c['slug'] for c in categories if c['name'] == selected_category), None)
    if cat_slug:
        filters['category_slug'] = cat_slug

if location_filter:
    filters['location'] = location_filter

if date_filter:
    filters['start_date'] = date_filter.strftime('%Y-%m-%d')

if status_filter:
    filters['status'] = status_filter[0] if len(status_filter) == 1 else None

# ── FETCH EVENTS ──────────────────────────────────────────
events = EventModel.search(**filters)

# ── RESULTS HEADER ────────────────────────────────────────
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown(f"<p style='color: rgba(224,224,224,0.6);'>Menampilkan <strong>{len(events)}</strong> event</p>", unsafe_allow_html=True)

with col2:
    sort_by = st.selectbox("Urutkan", ["Tanggal ↑", "Tanggal ↓", "Harga ↑", "Harga ↓", "Populer"])

# ── EVENT GRID ────────────────────────────────────────────
if not events:
    st.info("🔍 Tidak ada event yang sesuai filter. Coba ubah filter atau cari dengan kata kunci lain.")
else:
    cols_per_row = 3
    for i in range(0, len(events), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, event in enumerate(events[i:i+cols_per_row]):
            with cols[j]:
                status_class = f"status-{event.get('status', 'upcoming')}"
                price = event.get('min_price', 0)
                price_text = f"Rp {price:,.0f}" if price else "Gratis"

                st.markdown(f"""
                <div class="event-card">
                    <img src="{event.get('image_url', 'https://via.placeholder.com/400x180')}" class="event-image" />
                    <div class="event-content">
                        <span class="event-status {status_class}">{event.get('status', 'upcoming').upper()}</span>
                        <h3 class="event-title">{event['title']}</h3>
                        <p class="event-meta">📅 {event.get('start_date', 'TBA')}</p>
                        <p class="event-meta">📍 {event.get('location', 'TBA')}</p>
                        <p class="event-meta">👤 {event.get('organizer_name', 'TBA')}</p>
                        <p class="event-price">💰 {price_text}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if st.button("Lihat Detail", key=f"detail_{event['id']}", use_container_width=True):
                    st.session_state.selected_event_id = event['id']
                    st.switch_page("pages/6_🎪_Event_Detail.py")

# ── PAGINATION ────────────────────────────────────────────
if len(events) >= filters['limit']:
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button("📥 Muat Lebih Banyak", use_container_width=True):
            filters['limit'] += 12
            st.rerun()