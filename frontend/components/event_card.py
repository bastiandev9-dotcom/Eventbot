"""
Event Card Component
====================
Komponen card untuk menampilkan informasi event.
"""

import streamlit as st
from typing import Dict, Any, List, Optional, Callable
from utils.formatters import (
    format_date, format_price, format_status_badge,
    get_status_color, truncate_text, format_capacity, get_capacity_color,
)

_EVENT_CARD_CSS = """<style>
.ev-card{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:16px;overflow:hidden;transition:all 0.3s ease;margin-bottom:0.5rem;}
.ev-card:hover{background:rgba(255,255,255,0.07);border-color:rgba(124,58,237,0.3);transform:translateY(-2px);box-shadow:0 8px 30px rgba(0,0,0,0.3);}
.ev-card-img{width:100%;height:140px;object-fit:cover;}
.ev-img-ph{width:100%;height:140px;background:linear-gradient(135deg,rgba(124,58,237,0.25),rgba(79,70,229,0.15));display:flex;align-items:center;justify-content:center;font-size:2.5rem;}
.ev-card-body{padding:1rem;}
.ev-price{background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.2);color:#10B981;padding:0.15rem 0.5rem;border-radius:6px;font-size:0.75rem;font-weight:600;}
</style>"""


def render_event_card(
    event: Dict[str, Any],
    on_detail: Optional[Callable] = None,
    on_register: Optional[Callable] = None,
    compact: bool = False,
    key_suffix: str = "",
) -> None:
    """
    Render satu event card.
    PENTING: Jangan panggil ini dari dalam st.columns() yang sudah nested,
    karena card ini membuat tombol yang membutuhkan context kolom bebas.
    Gunakan render_event_grid() yang sudah menangani layout kolom.
    """
    event_id    = str(event.get("id", ""))
    title       = event.get("title", "Untitled Event")
    location    = event.get("location", "-")
    start_date  = event.get("start_date", "")
    status      = event.get("status", "upcoming")
    image_url   = event.get("image_url", "")
    description = event.get("short_description") or event.get("description", "")
    tickets     = event.get("tickets", [])

    # ── Kapasitas: total kuota semua tiket ─────────────────
    # Prioritas:
    # 1. total_quota / total_sold dari response list events (sudah di-SUM di backend)
    # 2. Hitung manual dari list tiket jika tersedia (halaman detail)
    # 3. Fallback ke field capacity event (lama)
    if event.get("total_quota") is not None:
        capacity   = int(event.get("total_quota") or 0)
        registered = int(event.get("total_sold") or 0)
    elif tickets:
        capacity   = sum(int(t.get("quota", 0) or 0) for t in tickets)
        registered = sum(int(t.get("sold_count", 0) or t.get("sold", 0) or 0) for t in tickets)
    else:
        capacity   = int(event.get("capacity", 0) or 0)
        registered = int(event.get("registered_count", 0) or 0)

    # Ambil harga minimum:
    # 1. Dari list tiket jika tersedia (halaman detail)
    # 2. Dari field min_price langsung (response list events)
    # 3. Default 0 (gratis)
    if tickets:
        min_price = min((float(t.get("price", 0) or 0) for t in tickets), default=0)
    elif event.get("min_price") is not None:
        min_price = float(event.get("min_price") or 0)
    else:
        min_price = 0

    price_text   = format_price(min_price)
    status_label = format_status_badge(status)
    date_label   = format_date(start_date)

    if compact:
        _render_compact_card(event, event_id, title, location, date_label,
                             price_text, on_detail, on_register, key_suffix)
        return

    st.markdown(_EVENT_CARD_CSS, unsafe_allow_html=True)

    # Image
    if image_url:
        img_html = '<img class="ev-card-img" src="' + image_url + '" />'
    else:
        img_html = '<div class="ev-img-ph">🎪</div>'

    cap_color = get_capacity_color(registered, capacity)
    cap_text  = format_capacity(registered, capacity) if capacity > 0 else str(registered) + " peserta"

    st.markdown(
        '<div class="ev-card">'
        + img_html +
        '<div class="ev-card-body">'
        '<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:0.4rem;">'
        '<span style="font-size:0.72rem;font-weight:600;">' + status_label + '</span>'
        '<span class="ev-price">' + price_text + '</span>'
        '</div>'
        '<div style="font-size:0.95rem;font-weight:700;color:#F8F9FA;margin:0 0 0.35rem;line-height:1.3;">'
        + truncate_text(title, 55) +
        '</div>'
        '<div style="font-size:0.78rem;color:#6B7280;margin-bottom:0.6rem;line-height:1.4;">'
        + truncate_text(description, 70) +
        '</div>'
        '<div style="font-size:0.78rem;color:#9CA3AF;display:flex;flex-direction:column;gap:0.2rem;">'
        '<span>📅 ' + date_label + '</span>'
        '<span>📍 ' + truncate_text(location, 30) + '</span>'
        '<span style="color:' + cap_color + ';">👥 ' + cap_text + '</span>'
        '</div>'
        '</div></div>',
        unsafe_allow_html=True,
    )

    # Tombol aksi — dua tombol terpisah: Detail dan Beli Tiket
    disabled = status in ("completed", "cancelled")
    btn_col1, btn_col2 = st.columns([1, 1])
    with btn_col1:
        if st.button(
            "📄 Detail",
            key="ev_detail_" + event_id + "_" + key_suffix,
            use_container_width=True,
            disabled=False,
            help="Lihat detail event",
        ):
            if on_detail:
                on_detail(event_id)
            else:
                st.session_state["detail_event_id"] = event_id
                st.session_state["current_page"]    = "Event_Explorer"
                st.rerun()
    with btn_col2:
        if st.button(
            "🎫 Beli Tiket",
            key="ev_buy_" + event_id + "_" + key_suffix,
            use_container_width=True,
            type="primary",
            disabled=disabled,
            help="Beli tiket event ini",
        ):
            if on_register:
                on_register(event_id)
            else:
                st.session_state["detail_event_id"]           = event_id
                st.session_state["show_buy_modal_" + event_id] = True
                st.session_state["current_page"]              = "Event_Explorer"
                st.rerun()


def _render_compact_card(event, event_id, title, location, date_label,
                          price_text, on_detail, on_register, key_suffix):
    """Card compact untuk chatbot (tidak ada nested columns)."""
    st.markdown(
        '<div style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);'
        'border-radius:12px;padding:0.75rem;margin-bottom:0.5rem;">'
        '<div style="font-weight:700;color:#F8F9FA;font-size:0.875rem;margin-bottom:0.25rem;">🎪 '
        + truncate_text(title, 40) +
        '</div>'
        '<div style="font-size:0.75rem;color:#9CA3AF;">📅 ' + date_label +
        ' · 📍 ' + truncate_text(location, 22) +
        ' · <span style="color:#10B981;font-weight:600;">' + price_text + '</span></div>'
        '</div>',
        unsafe_allow_html=True,
    )
    if st.button(
        "📄 Detail",
        key="compact_d_" + event_id + "_" + key_suffix,
        use_container_width=True,
    ):
        if on_detail:
            on_detail(event_id)
        else:
            st.session_state["detail_event_id"] = event_id
            st.session_state["current_page"]    = "Event_Explorer"
            st.rerun()


def render_event_grid(
    events: List[Dict[str, Any]],
    columns: int = 3,
    on_detail: Optional[Callable] = None,
    on_register: Optional[Callable] = None,
    compact: bool = False,
    grid_key: str = "grid",
) -> None:
    """
    Render grid event cards.
    Aman dipanggil dari mana saja — kolom dibuat di sini, bukan di dalam card.

    Args:
        grid_key: Prefix unik agar key widget tidak bentrok saat dipanggil berkali-kali.
    """
    if not events:
        st.markdown(
            '<div style="text-align:center;padding:3rem;color:#6B7280;">'
            '<div style="font-size:2.5rem;margin-bottom:0.75rem;">🔍</div>'
            '<div style="font-size:1rem;font-weight:600;color:#ADB5BD;">Tidak ada event ditemukan</div>'
            '<div style="font-size:0.85rem;margin-top:0.25rem;">Coba ubah filter atau kata kunci.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    n_cols = min(columns, len(events))

    # Render dalam baris, setiap baris = satu set kolom
    # Ini menghindari nesting karena setiap kolom hanya berisi konten card
    for row_start in range(0, len(events), n_cols):
        row_events = events[row_start:row_start + n_cols]
        cols       = st.columns(len(row_events))
        for col_idx, event in enumerate(row_events):
            global_idx = row_start + col_idx
            with cols[col_idx]:
                render_event_card(
                    event=event,
                    on_detail=on_detail,
                    on_register=on_register,
                    compact=compact,
                    key_suffix=grid_key + "_" + str(global_idx),
                )


def render_event_detail(event: Dict[str, Any]) -> None:
    """Render tampilan detail lengkap sebuah event."""
    title      = event.get("title", "Untitled")
    description= event.get("description", "")
    location   = event.get("location", "-")
    start_date = event.get("start_date", "")
    status     = event.get("status", "upcoming")
    image_url  = event.get("image_url", "")
    tickets    = event.get("tickets", [])

    # Kapasitas dari total kuota tiket
    if tickets:
        capacity   = sum(int(t.get("quota", 0) or 0) for t in tickets)
        registered = sum(int(t.get("sold_count", 0) or t.get("sold", 0) or 0) for t in tickets)
    elif event.get("total_quota") is not None:
        capacity   = int(event.get("total_quota") or 0)
        registered = int(event.get("total_sold") or 0)
    else:
        capacity   = int(event.get("capacity", 0) or 0)
        registered = int(event.get("registered_count", 0) or 0)

    if image_url:
        st.image(image_url, use_column_width=True)

    st.markdown(
        '<div style="margin-bottom:1.5rem;">'
        '<div style="margin-bottom:0.5rem;">' + format_status_badge(status) + '</div>'
        '<h1 style="font-size:1.75rem;font-weight:800;color:#F8F9FA;margin:0 0 0.5rem;">' + title + '</h1>'
        '<div style="display:flex;flex-wrap:wrap;gap:1rem;font-size:0.875rem;color:#9CA3AF;">'
        '<span>📅 ' + format_date(start_date) + '</span>'
        '<span>📍 ' + location + '</span>'
        '<span style="color:' + get_capacity_color(registered, capacity) + ';">👥 '
        + format_capacity(registered, capacity) + '</span>'
        '</div></div>',
        unsafe_allow_html=True,
    )

    st.markdown("**Deskripsi**")
    st.markdown(description)

    if tickets:
        st.markdown("**🎫 Tiket Tersedia**")
        for ticket in tickets:
            price     = ticket.get("price", 0)
            name      = ticket.get("name", "Tiket")
            quota     = int(ticket.get("quota", 0) or 0)
            sold      = int(ticket.get("sold_count", 0) or ticket.get("sold", 0) or 0)
            remaining = int(ticket.get("remaining", quota - sold) or (quota - sold))

            if quota > 0:
                if remaining <= 0:
                    avail_text  = "Kuota: " + str(quota) + " · Habis"
                    avail_color = "#EF4444"
                elif remaining <= 10:
                    avail_text  = "Kuota: " + str(quota) + " · " + str(remaining) + " tersisa"
                    avail_color = "#F59E0B"
                else:
                    avail_text  = "Kuota: " + str(quota) + " · " + str(remaining) + " tersisa"
                    avail_color = "#10B981"
            else:
                avail_text  = "Kuota: Tak terbatas"
                avail_color = "#10B981"

            st.markdown(
                '<div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);'
                'border-radius:10px;padding:0.875rem;display:flex;justify-content:space-between;'
                'align-items:center;margin-bottom:0.5rem;">'
                '<div>'
                '<div style="font-weight:600;color:#F8F9FA;">' + name + '</div>'
                '<div style="font-size:0.8rem;color:' + avail_color + ';">🪑 ' + avail_text + '</div>'
                '</div>'
                '<div style="font-size:1.1rem;font-weight:700;color:#10B981;">' + format_price(price) + '</div>'
                '</div>',
                unsafe_allow_html=True,
            )
