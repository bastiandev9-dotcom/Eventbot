"""
Buy Ticket Modal Component
==========================
Form pembelian tiket: pilih tiket, kuantitas, metode bayar, konfirmasi.
Dipanggil dari halaman detail event di Event_Explorer.
"""

import streamlit as st
from typing import List, Dict, Any, Optional
from utils.api_client import APIClient, APIError
from utils.session_manager import SessionManager
from utils.formatters import format_price
from components.toast import queue_toast

_PAYMENT_METHODS = {
    "💳 Transfer Bank":  "transfer_bank",
    "📱 E-Wallet":       "e_wallet",
    "🆓 Gratis":         "free",
}

_CSS = """<style>
.buy-modal{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:16px;padding:1.5rem;margin-top:1rem;}
.buy-modal-title{font-size:1.1rem;font-weight:700;color:#F8F9FA;margin-bottom:1.25rem;display:flex;align-items:center;gap:0.5rem;}
.ticket-option{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:0.875rem;margin-bottom:0.5rem;cursor:pointer;transition:all 0.2s;}
.ticket-option:hover,.ticket-option.selected{border-color:rgba(124,58,237,0.5);background:rgba(124,58,237,0.08);}
.ticket-name{font-weight:600;color:#F8F9FA;font-size:0.9rem;}
.ticket-desc{font-size:0.75rem;color:#6B7280;margin-top:0.2rem;}
.ticket-price{font-size:1rem;font-weight:700;color:#10B981;}
.order-summary{background:rgba(124,58,237,0.08);border:1px solid rgba(124,58,237,0.2);border-radius:10px;padding:1rem;margin:1rem 0;}
.summary-row{display:flex;justify-content:space-between;font-size:0.875rem;color:#ADB5BD;margin-bottom:0.4rem;}
.summary-total{display:flex;justify-content:space-between;font-size:1rem;font-weight:700;color:#F8F9FA;border-top:1px solid rgba(255,255,255,0.08);padding-top:0.75rem;margin-top:0.5rem;}
</style>"""


def render_buy_ticket_modal(
    event: Dict[str, Any],
    on_success: Optional[callable] = None,
    on_cancel: Optional[callable] = None,
) -> None:
    """
    Render form beli tiket untuk sebuah event.

    Args:
        event: Dict data event lengkap (harus punya field 'tickets')
        on_success: Callback setelah booking berhasil
        on_cancel: Callback saat user klik batal
    """
    tickets = event.get("tickets", [])
    event_id = str(event.get("id", ""))
    event_title = event.get("title", "Event")

    st.markdown(_CSS, unsafe_allow_html=True)
    st.markdown(
        '<div class="buy-modal">'
        '<div class="buy-modal-title">🎫 Beli Tiket — ' + event_title + '</div>',
        unsafe_allow_html=True,
    )

    if not tickets:
        st.warning("Belum ada tiket tersedia untuk event ini.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # ── Step tracking ─────────────────────────────────────
    step_key = "buy_step_" + event_id
    if step_key not in st.session_state:
        st.session_state[step_key] = "select"  # select → confirm → done

    step = st.session_state[step_key]

    if step == "select":
        _render_select_step(event_id, tickets)
    elif step == "confirm":
        _render_confirm_step(event_id, event_title, tickets, on_success)

    # Tombol batal
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("❌ Batal", key="buy_cancel_" + event_id, use_container_width=True):
        _reset_state(event_id)
        if on_cancel:
            on_cancel()
        else:
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


def _render_select_step(event_id: str, tickets: List[Dict]) -> None:
    """Step 1: Pilih tiket, kuantitas, dan metode bayar."""
    st.markdown(
        '<div style="font-size:0.8rem;font-weight:600;color:#6B7280;'
        'text-transform:uppercase;letter-spacing:0.05em;margin-bottom:0.75rem;">'
        'Langkah 1 dari 2 — Pilih Tiket</div>',
        unsafe_allow_html=True,
    )

    # Pilih tiket
    ticket_labels = {}
    for t in tickets:
        price_str = "GRATIS" if not t.get("price") else format_price(t["price"])
        quota     = t.get("quota", 0)
        sold      = t.get("sold_count", 0)
        remaining = quota - sold if quota > 0 else 999
        avail_str = str(remaining) + " tersisa" if quota > 0 else "Tak terbatas"
        label     = t.get("name", "Tiket") + "  —  " + price_str + "  (" + avail_str + ")"
        ticket_labels[label] = t

    selected_label = st.radio(
        "Pilih jenis tiket",
        options=list(ticket_labels.keys()),
        key="buy_ticket_label_" + event_id,
        label_visibility="collapsed",
    )
    selected_ticket = ticket_labels.get(selected_label, tickets[0])
    ticket_id       = str(selected_ticket.get("id", ""))
    ticket_price    = float(selected_ticket.get("price", 0) or 0)
    max_per_order   = int(selected_ticket.get("max_per_order", 5) or 5)
    quota           = int(selected_ticket.get("quota", 0) or 0)
    sold            = int(selected_ticket.get("sold_count", 0) or 0)
    remaining       = quota - sold if quota > 0 else max_per_order
    max_qty         = min(max_per_order, remaining) if remaining > 0 else max_per_order

    # Detail tiket terpilih
    if selected_ticket.get("description"):
        st.markdown(
            '<div style="font-size:0.8rem;color:#6B7280;margin:0.25rem 0 0.75rem;">'
            + selected_ticket["description"] + '</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Kuantitas
    quantity = st.number_input(
        "Jumlah Tiket",
        min_value=1,
        max_value=max(1, max_qty),
        value=1,
        step=1,
        key="buy_qty_" + event_id,
        help="Maksimal " + str(max_qty) + " tiket per pemesanan",
    )

    # Metode bayar (sembunyikan jika gratis)
    if ticket_price > 0:
        payment_label = st.selectbox(
            "Metode Pembayaran",
            options=[k for k in _PAYMENT_METHODS if k != "🆓 Gratis"],
            key="buy_payment_" + event_id,
        )
        payment_method = _PAYMENT_METHODS[payment_label]
    else:
        st.info("🆓 Tiket ini gratis — tidak perlu pembayaran.")
        payment_method = "free"
        payment_label  = "🆓 Gratis"

    # Simpan pilihan ke session state
    st.session_state["buy_ticket_id_"     + event_id] = ticket_id
    st.session_state["buy_ticket_name_"   + event_id] = selected_ticket.get("name", "Tiket")
    st.session_state["buy_ticket_price_"  + event_id] = ticket_price
    st.session_state["buy_qty_val_"       + event_id] = int(quantity)
    st.session_state["buy_payment_val_"   + event_id] = payment_method
    st.session_state["buy_payment_lbl_"   + event_id] = payment_label

    # Preview total
    total = ticket_price * int(quantity)
    st.markdown(
        '<div class="order-summary">'
        '<div class="summary-row"><span>' + selected_ticket.get("name","Tiket") + ' × ' + str(int(quantity)) + '</span>'
        '<span>' + format_price(ticket_price) + ' × ' + str(int(quantity)) + '</span></div>'
        '<div class="summary-row"><span>Metode Bayar</span><span>' + payment_label + '</span></div>'
        '<div class="summary-total"><span>Total</span><span>' + format_price(total) + '</span></div>'
        '</div>',
        unsafe_allow_html=True,
    )

    if st.button("Lanjut ke Konfirmasi →", key="buy_next_" + event_id, type="primary", use_container_width=True):
        st.session_state["buy_step_" + event_id] = "confirm"
        st.rerun()


def _render_confirm_step(
    event_id: str,
    event_title: str,
    tickets: List[Dict],
    on_success: Optional[callable],
) -> None:
    """Step 2: Konfirmasi & proses pembelian."""
    st.markdown(
        '<div style="font-size:0.8rem;font-weight:600;color:#6B7280;'
        'text-transform:uppercase;letter-spacing:0.05em;margin-bottom:0.75rem;">'
        'Langkah 2 dari 2 — Konfirmasi Pemesanan</div>',
        unsafe_allow_html=True,
    )

    ticket_id     = st.session_state.get("buy_ticket_id_"    + event_id, "")
    ticket_name   = st.session_state.get("buy_ticket_name_"  + event_id, "Tiket")
    ticket_price  = st.session_state.get("buy_ticket_price_" + event_id, 0)
    quantity      = st.session_state.get("buy_qty_val_"      + event_id, 1)
    payment_method= st.session_state.get("buy_payment_val_"  + event_id, "free")
    payment_label = st.session_state.get("buy_payment_lbl_"  + event_id, "Gratis")
    total         = ticket_price * quantity

    # Ringkasan pesanan
    st.markdown(
        '<div class="order-summary">'
        '<div style="font-weight:600;color:#F8F9FA;font-size:0.9rem;margin-bottom:0.75rem;">📋 Ringkasan Pesanan</div>'
        '<div class="summary-row"><span>Event</span><span style="color:#F8F9FA;text-align:right;max-width:60%;">' + event_title + '</span></div>'
        '<div class="summary-row"><span>Tiket</span><span>' + ticket_name + '</span></div>'
        '<div class="summary-row"><span>Jumlah</span><span>' + str(quantity) + ' tiket</span></div>'
        '<div class="summary-row"><span>Harga Satuan</span><span>' + format_price(ticket_price) + '</span></div>'
        '<div class="summary-row"><span>Metode Bayar</span><span>' + payment_label + '</span></div>'
        '<div class="summary-total"><span>Total Pembayaran</span><span style="color:#10B981;">' + format_price(total) + '</span></div>'
        '</div>',
        unsafe_allow_html=True,
    )

    if payment_method != "free":
        st.markdown(
            '<div style="background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.2);'
            'border-radius:8px;padding:0.75rem;font-size:0.8rem;color:#F59E0B;margin-bottom:0.75rem;">'
            '⚠️ Setelah konfirmasi, lakukan pembayaran sesuai metode yang dipilih. '
            'Tiket aktif setelah pembayaran dikonfirmasi admin.</div>',
            unsafe_allow_html=True,
        )

    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("← Kembali", key="buy_back_" + event_id, use_container_width=True):
            st.session_state["buy_step_" + event_id] = "select"
            st.rerun()
    with col2:
        if st.button(
            "✅ Konfirmasi & Pesan",
            key="buy_confirm_" + event_id,
            type="primary",
            use_container_width=True,
        ):
            _process_booking(event_id, ticket_id, quantity, payment_method, on_success)


def _process_booking(
    event_id: str,
    ticket_id: str,
    quantity: int,
    payment_method: str,
    on_success: Optional[callable],
) -> None:
    """Kirim request booking ke backend."""
    token = SessionManager.get_token()
    if not token:
        st.error("❌ Silakan login terlebih dahulu.")
        return

    client = APIClient(token=token)
    try:
        with st.spinner("Memproses pemesanan..."):
            result = client.book_ticket(
                ticket_id=ticket_id,
                quantity=quantity,
                payment_method=payment_method if payment_method != "free" else None,
            )

        total_price = result.get("total_price", 0)
        msg = result.get("message", "Pemesanan berhasil!")

        queue_toast("🎉 " + msg + " Total: " + format_price(total_price), "success")
        _reset_state(event_id)

        # Invalidate semua cache event agar sold_count & registered_count langsung update
        _invalidate_event_cache(event_id)

        if on_success:
            on_success(result)
        else:
            st.session_state["current_page"] = "Profil_saya"
            st.rerun()

    except APIError as e:
        if e.status_code == 401:
            st.error("❌ Sesi habis. Silakan login ulang.")
        elif e.status_code == 400:
            st.error("❌ " + e.message)
        else:
            st.error("❌ Gagal memesan tiket: " + e.message)
    except Exception as e:
        st.error("❌ Tidak dapat terhubung ke server.")


def _invalidate_event_cache(event_id: str) -> None:
    """Hapus cache event (detail + list) agar data tiket & peserta langsung fresh."""
    keys_to_delete = [
        k for k in st.session_state.keys()
        if k.startswith("events_")
        or k.startswith("event_detail_")
        or k == f"event_detail_{event_id}"
        or k == f"event_detail_{event_id}_ts"
    ]
    for k in keys_to_delete:
        st.session_state.pop(k, None)


def _reset_state(event_id: str) -> None:
    """Bersihkan semua state pembelian tiket."""
    keys = [
        "buy_step_", "buy_ticket_id_", "buy_ticket_name_",
        "buy_ticket_price_", "buy_qty_val_", "buy_payment_val_", "buy_payment_lbl_",
    ]
    for k in keys:
        st.session_state.pop(k + event_id, None)
