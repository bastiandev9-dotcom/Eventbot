"""
Filter Panel Component
======================
Panel filter untuk Event Explorer.
"""

import streamlit as st
from typing import Dict, Any, List, Optional
from datetime import date

_DEFAULT_CATEGORIES = [
    "Semua", "Teknologi", "Bisnis", "Pendidikan", "Musik", "Olahraga",
    "Seni & Budaya", "Kesehatan", "Gaming", "Komunitas", "Workshop",
]
_DEFAULT_LOCATIONS = [
    "Semua Lokasi", "Jakarta", "Bandung", "Surabaya", "Yogyakarta",
    "Bali", "Medan", "Makassar", "Semarang", "Malang", "Online",
]
_STATUS_OPTIONS = {
    "Semua":       "",
    "Akan Datang": "upcoming",
    "Berlangsung": "ongoing",
    "Selesai":     "completed",
}


def render_filter_panel(
    key_prefix: str = "filter",
    categories: Optional[List[str]] = None,
    locations: Optional[List[str]] = None,
    show_price_range: bool = True,
    show_date_range: bool = True,
    show_status: bool = True,
    show_free_only: bool = True,
) -> Dict[str, Any]:
    """Render panel filter event."""
    cats = categories or _DEFAULT_CATEGORIES
    locs = locations  or _DEFAULT_LOCATIONS

    st.markdown(
        '<div style="margin-bottom:1.5rem;font-size:0.8rem;font-weight:700;color:#6B7280;'
        'text-transform:uppercase;letter-spacing:0.08em;">🎛️ Filter Event</div>',
        unsafe_allow_html=True,
    )

    q = st.text_input("Cari Event", placeholder="🔍 Nama event, topik...",
                      key=key_prefix + "_q", label_visibility="collapsed")
    st.markdown("---")

    st.markdown("**Kategori**")
    category_raw = st.selectbox("Kategori", options=cats,
                                key=key_prefix + "_category", label_visibility="collapsed")
    category = None if category_raw == "Semua" else category_raw.lower().replace(" & ", "-").replace(" ", "-")

    st.markdown("**Lokasi**")
    location_raw = st.selectbox("Lokasi", options=locs,
                                key=key_prefix + "_location", label_visibility="collapsed")
    location = None if location_raw == "Semua Lokasi" else location_raw

    status = ""
    if show_status:
        st.markdown("**Status Event**")
        status_label = st.selectbox(
            "Status",
            options=list(_STATUS_OPTIONS.keys()),
            index=0,  # Default: "Semua" → tampilkan semua event
            key=key_prefix + "_status",
            label_visibility="collapsed",
        )
        status = _STATUS_OPTIONS.get(status_label, "")

    start_date_val = end_date_val = None
    if show_date_range:
        st.markdown("**Tanggal**")
        today = date.today()
        dc1, dc2 = st.columns(2)
        with dc1:
            start_dt = st.date_input("Dari", value=None, min_value=today,
                                     key=key_prefix + "_start_date", format="DD/MM/YYYY")
        with dc2:
            end_dt = st.date_input("Sampai", value=None, min_value=today,
                                   key=key_prefix + "_end_date", format="DD/MM/YYYY")
        if start_dt:
            start_date_val = start_dt.strftime("%Y-%m-%d")
        if end_dt:
            end_date_val = end_dt.strftime("%Y-%m-%d")

    min_price_val = max_price_val = None
    free_only = False
    if show_price_range:
        st.markdown("**Harga Tiket**")
        if show_free_only:
            free_only = st.checkbox("🆓 Gratis saja", key=key_prefix + "_free_only")
        if not free_only:
            price_range = st.slider("Rentang harga (Rp)", min_value=0, max_value=2_000_000,
                                    value=(0, 2_000_000), step=25_000,
                                    key=key_prefix + "_price_range", format="Rp %d")
            if price_range[0] > 0:
                min_price_val = price_range[0]
            if price_range[1] < 2_000_000:
                max_price_val = price_range[1]

    st.markdown("---")
    if st.button("🔄 Reset Filter", key=key_prefix + "_reset", use_container_width=True):
        for k in [key_prefix + s for s in ("_q", "_category", "_location", "_status",
                                             "_start_date", "_end_date", "_price_range", "_free_only")]:
            st.session_state.pop(k, None)
        st.rerun()

    return {
        "q":          q.strip() if q else None,
        "category":   category,
        "location":   location,
        "status":     status,
        "start_date": start_date_val,
        "end_date":   end_date_val,
        "min_price":  0.0 if free_only else min_price_val,
        "max_price":  0.0 if free_only else max_price_val,
        "free_only":  free_only,
    }


def render_active_filters(filters: Dict[str, Any]) -> None:
    """Render chips filter yang aktif."""
    from utils.formatters import format_price
    active = []
    if filters.get("q"):
        active.append('🔍 "' + filters["q"] + '"')
    if filters.get("category"):
        active.append("📂 " + filters["category"])
    if filters.get("location"):
        active.append("📍 " + filters["location"])
    if filters.get("status"):  # Hanya tampilkan jika bukan "Semua" (string kosong)
        active.append("🏷️ " + filters["status"])
    if filters.get("start_date"):
        active.append("📅 Dari " + filters["start_date"])
    if filters.get("free_only"):
        active.append("🆓 Gratis")
    if filters.get("min_price"):
        active.append("💰 Min " + format_price(filters["min_price"]))

    if not active:
        return

    chips = "".join([
        '<span style="background:rgba(124,58,237,0.1);border:1px solid rgba(124,58,237,0.2);'
        'color:#8B5CF6;padding:0.2rem 0.6rem;border-radius:9999px;font-size:0.75rem;font-weight:600;'
        'margin-right:0.25rem;">' + chip + '</span>'
        for chip in active
    ])
    st.markdown(
        '<div style="margin-bottom:1rem;display:flex;flex-wrap:wrap;gap:0.25rem;align-items:center;">'
        '<span style="font-size:0.75rem;color:#6B7280;margin-right:0.25rem;">Filter aktif:</span>'
        + chips + '</div>',
        unsafe_allow_html=True,
    )
