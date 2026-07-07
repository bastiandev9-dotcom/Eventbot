"""
Ticket Card Component
=====================
Komponen untuk menampilkan tiket event milik user (gaya e-ticket).
"""

import streamlit as st
from typing import Dict, Any, Optional, Callable
from utils.formatters import (
    format_date, format_datetime, format_price,
    format_status_badge, get_status_color, truncate_text,
)


def render_ticket_card(
    ticket: Dict[str, Any],
    on_cancel: Optional[Callable[[str], None]] = None,
    show_qr: bool = True,
    key_suffix: str = "",
) -> None:
    """Render satu ticket card bergaya e-ticket."""
    ticket_id     = str(ticket.get("id", ""))
    event_title   = ticket.get("event_title") or ticket.get("event", {}).get("title", "Event")
    # Backend returns start_date & location (not event_date / event_location)
    event_date    = (ticket.get("event_date")
                     or ticket.get("start_date")
                     or ticket.get("event", {}).get("start_date", ""))
    event_loc     = (ticket.get("event_location")
                     or ticket.get("location")
                     or ticket.get("event", {}).get("location", "-"))
    ticket_name   = (ticket.get("ticket_name")
                     or ticket.get("ticket", {}).get("name", "Tiket"))
    ticket_code   = ticket.get("ticket_code") or ticket.get("code") or "EVT-" + ticket_id[:8].upper()
    status        = ticket.get("status", "pending")
    # Harga: total_price (yang dibayar user), fallback ke ticket_price atau price
    price         = (ticket.get("total_price")
                     or ticket.get("ticket_price")
                     or ticket.get("price")
                     or ticket.get("ticket", {}).get("price", 0))
    registered_at = ticket.get("registered_at") or ticket.get("created_at", "")

    status_label = format_status_badge(status, with_emoji=True)
    status_color = get_status_color(status)
    date_str     = format_date(event_date)
    price_str    = format_price(price)
    reg_str      = format_datetime(registered_at)
    is_active    = status in ("registered", "confirmed", "pending")
    is_cancelled = status in ("cancelled", "cancelled_reg")
    opacity      = "0.5" if is_cancelled else "1"

    qr_html = ""
    if show_qr:
        qr_html = (
            '<div style="width:70px;height:70px;border-radius:8px;'
            'background:rgba(124,58,237,0.08);border:1px solid rgba(124,58,237,0.2);'
            'display:flex;align-items:center;justify-content:center;'
            'font-size:2rem;flex-shrink:0;">🎫</div>'
        )

    html = (
        '<div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);'
        'border-radius:16px;overflow:hidden;margin-bottom:1rem;opacity:' + opacity + ';">'
        '<div style="height:4px;background:' + status_color + ';"></div>'
        '<div style="display:flex;padding:1.25rem;gap:1.25rem;">'
        + qr_html +
        '<div style="flex:1;min-width:0;">'
        '<div style="font-size:0.7rem;font-weight:700;color:#6B7280;'
        'text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.3rem;">'
        + ticket_name +
        '</div><h3 style="font-size:1.1rem;font-weight:700;color:#F8F9FA;margin:0 0 0.5rem;line-height:1.3;">'
        + truncate_text(event_title, 50) +
        '</h3><div style="display:flex;flex-direction:column;gap:0.3rem;font-size:0.8rem;color:#9CA3AF;">'
        '<span>📅 ' + date_str + '</span>'
        '<span>📍 ' + truncate_text(event_loc, 35) + '</span>'
        '<span>💰 ' + price_str + '</span>'
        '</div></div>'
        '<div style="text-align:right;display:flex;flex-direction:column;'
        'align-items:flex-end;justify-content:space-between;min-width:100px;">'
        '<div style="font-size:0.8rem;">' + status_label + '</div>'
        '<div><div style="font-size:0.65rem;color:#4B5563;margin-bottom:0.15rem;'
        'text-transform:uppercase;letter-spacing:0.05em;">Kode Tiket</div>'
        '<div style="font-family:monospace;font-size:0.8rem;font-weight:700;color:#7C3AED;'
        'background:rgba(124,58,237,0.08);border:1px solid rgba(124,58,237,0.2);'
        'padding:0.2rem 0.5rem;border-radius:6px;">' + ticket_code + '</div>'
        '<div style="font-size:0.7rem;color:#374151;margin-top:0.3rem;">Dipesan: ' + reg_str + '</div>'
        '</div></div></div>'
        '<div style="margin:0 1.25rem;border-top:2px dashed rgba(255,255,255,0.07);"></div>'
        '<div style="padding:0.75rem 1.25rem;display:flex;justify-content:space-between;align-items:center;">'
        '<span style="font-size:0.75rem;color:#4B5563;">ID: ' + ticket_id[:8].upper() + '</span>'
        '<span style="font-size:0.75rem;color:#4B5563;">🎪 EventBot</span>'
        '</div></div>'
    )
    st.markdown(html, unsafe_allow_html=True)

    if is_active and on_cancel:
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("📄 Lihat Detail Event",
                         key="tkt_view_" + ticket_id + "_" + key_suffix,
                         use_container_width=True):
                st.session_state["detail_event_id"] = ticket.get("event_id", "")
                st.session_state["current_page"] = "Event_Explorer"
                st.rerun()
        with col2:
            if st.button("❌ Batalkan",
                         key="tkt_cancel_" + ticket_id + "_" + key_suffix,
                         use_container_width=True):
                st.session_state["confirm_cancel_" + ticket_id] = True
                st.rerun()

    if st.session_state.get("confirm_cancel_" + ticket_id):
        st.warning("⚠️ Yakin ingin membatalkan pendaftaran ini?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Ya, Batalkan",
                         key="confirm_yes_" + ticket_id,
                         type="primary",
                         use_container_width=True):
                del st.session_state["confirm_cancel_" + ticket_id]
                if on_cancel:
                    on_cancel(ticket_id)
        with c2:
            if st.button("Tidak",
                         key="confirm_no_" + ticket_id,
                         use_container_width=True):
                del st.session_state["confirm_cancel_" + ticket_id]
                st.rerun()


def render_ticket_list(
    tickets: list,
    on_cancel: Optional[Callable] = None,
    empty_message: str = "Kamu belum memiliki tiket.",
) -> None:
    """Render daftar ticket cards."""
    if not tickets:
        st.markdown(
            '<div style="text-align:center;padding:3rem;background:rgba(255,255,255,0.03);'
            'border:1px solid rgba(255,255,255,0.07);border-radius:16px;color:#6B7280;">'
            '<div style="font-size:2.5rem;margin-bottom:0.75rem;">🎫</div>'
            '<div style="font-size:1rem;font-weight:600;color:#ADB5BD;">' + empty_message + '</div>'
            '<div style="font-size:0.85rem;margin-top:0.25rem;">Temukan event menarik dan daftar sekarang!</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        if st.button("📋 Jelajahi Event", key="ticket_empty_explore", type="primary"):
            st.session_state["current_page"] = "Event_Explorer"
            st.rerun()
        return

    for i, ticket in enumerate(tickets):
        render_ticket_card(ticket=ticket, on_cancel=on_cancel, key_suffix=str(i))
