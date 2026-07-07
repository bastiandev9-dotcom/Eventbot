"""
Event Explorer Page — EventBot
"""

import streamlit as st
from components.event_card import render_event_grid, render_event_detail
from components.filter_panel import render_filter_panel, render_active_filters
from components.toast import render_toast, queue_toast
from components.buy_ticket_modal import render_buy_ticket_modal
from hooks.use_events import use_events
from hooks.use_auth import use_auth
from hooks.use_theme import use_theme
from utils.session_manager import SessionManager


def render() -> None:
    theme = use_theme()
    theme["apply_theme"]()
    render_toast()

    events_hook = use_events()
    auth        = use_auth()

    # Cek apakah sedang di halaman detail
    # Gunakan .get() bukan .pop() agar state tidak hilang saat widget interaction
    detail_event_id = st.session_state.get("detail_event_id", None)

    # Kalau ada event_id baru yang di-set (dari card), baru simpan ke state permanen
    incoming = st.session_state.pop("_incoming_detail_id", None)
    if incoming:
        st.session_state["detail_event_id"] = incoming
        detail_event_id = incoming

    if detail_event_id:
        # auto_open hanya berlaku sekali saat pertama masuk
        auto_open_modal = st.session_state.pop("show_buy_modal_" + str(detail_event_id), False)
        _render_detail_page(detail_event_id, events_hook, auth, auto_open_modal=auto_open_modal)
        return

    st.markdown(
        '<div style="margin-bottom:1.5rem;">'
        '<h1 style="font-size:1.75rem;font-weight:800;color:#F8F9FA;margin:0 0 0.25rem;">📋 Jelajahi Event</h1>'
        '<p style="color:#6B7280;font-size:0.9rem;margin:0;">Temukan event seru yang sesuai minatmu</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Filter di sidebar (tidak nested columns) ──────────
    with st.sidebar:
        st.markdown("---")
        filters = render_filter_panel(key_prefix="explorer")

    # ── Konten utama (tidak dalam st.columns agar grid bisa bebas) ──
    render_active_filters(filters)

    if "explorer_page" not in st.session_state:
        st.session_state["explorer_page"] = 1

    # Bust cache event list setiap kali masuk halaman (dari navigasi sidebar)
    if st.session_state.pop("_explorer_needs_refresh", False):
        stale = [k for k in st.session_state if k.startswith("events_")]
        for k in stale:
            del st.session_state[k]

    min_p = 0.0 if filters.get("free_only") else filters.get("min_price")
    max_p = 0.0 if filters.get("free_only") else filters.get("max_price")

    with st.spinner("Memuat event..."):
        events, total, err = events_hook["fetch_events"](
            q=filters.get("q") or None,
            location=filters.get("location"),
            category=filters.get("category"),
            start_date=filters.get("start_date"),
            end_date=filters.get("end_date"),
            status=filters.get("status") or None,
            min_price=min_p,
            max_price=max_p,
            page=st.session_state["explorer_page"],
            page_size=9,
            use_cache=False,   # selalu ambil data terbaru dari backend
        )

    if err:
        st.warning("⚠️ " + err)
        _render_demo_events()
        return

    q_text = ' untuk "' + filters["q"] + '"' if filters.get("q") else ""
    st.markdown(
        '<p style="color:#6B7280;font-size:0.85rem;margin-bottom:1rem;">Menampilkan '
        '<strong style="color:#F8F9FA;">' + str(total) + '</strong> event' + q_text + '</p>',
        unsafe_allow_html=True,
    )

    def on_detail(event_id: str) -> None:
        st.session_state["_incoming_detail_id"] = event_id
        st.rerun()

    def on_register(event_id: str) -> None:
        if not auth["is_logged_in"]:
            queue_toast("Silakan login terlebih dahulu.", "warning")
            st.session_state["current_page"] = "Login_register"
            st.rerun()
        else:
            st.session_state["_incoming_detail_id"]          = event_id
            st.session_state["show_buy_modal_" + event_id]   = True
            st.rerun()

    page_key = "explorer_p" + str(st.session_state.get("explorer_page", 1))
    render_event_grid(
        events=events, columns=3,
        on_detail=on_detail, on_register=on_register,
        grid_key=page_key,
    )

    # Pagination
    if total > 9:
        total_pages = (total + 8) // 9
        current     = st.session_state["explorer_page"]
        p1, p2, p3  = st.columns([1, 2, 1])
        with p1:
            if st.button("◀ Sebelumnya", disabled=(current <= 1), key="exp_prev"):
                st.session_state["explorer_page"] = current - 1
                st.rerun()
        with p2:
            st.markdown(
                '<p style="text-align:center;color:#6B7280;font-size:0.85rem;margin:0.5rem 0;">Halaman '
                + str(current) + ' / ' + str(total_pages) + '</p>',
                unsafe_allow_html=True,
            )
        with p3:
            if st.button("Berikutnya ▶", disabled=(current >= total_pages), key="exp_next"):
                st.session_state["explorer_page"] = current + 1
                st.rerun()


def _render_detail_page(
    event_id: str,
    events_hook: dict,
    auth: dict,
    auto_open_modal: bool = False,
) -> None:
    """Render halaman detail event dengan modal beli tiket."""
    if st.button("← Kembali ke Daftar Event", key="back_to_list"):
        # Hapus state detail agar kembali ke halaman list
        st.session_state.pop("detail_event_id", None)
        st.session_state.pop("show_modal_" + event_id, None)
        _reset_buy_state(event_id)
        st.rerun()
    st.markdown("---")

    with st.spinner("Memuat detail event..."):
        event, err = events_hook["fetch_event"](event_id)

    if err:
        st.error("❌ " + err)
        return
    if not event:
        st.error("Event tidak ditemukan.")
        return

    render_event_detail(event)

    # Tombol beli tiket (muncul jika event masih aktif)
    event_status = event.get("status", "upcoming")
    tickets      = event.get("tickets", [])

    if event_status in ("completed", "cancelled"):
        st.info("Event ini sudah selesai atau dibatalkan — pendaftaran ditutup.")
        return

    if not tickets:
        st.warning("⚠️ Belum ada tiket tersedia untuk event ini.")
        return

    st.markdown("---")

    # State: apakah modal beli tiket sedang ditampilkan
    modal_key = "show_modal_" + event_id
    if auto_open_modal and modal_key not in st.session_state:
        st.session_state[modal_key] = True

    if not st.session_state.get(modal_key, False):
        # Tampilkan tombol pemicu
        if not auth["is_logged_in"]:
            st.warning("🔒 Silakan [login](/?page=Login_register) terlebih dahulu untuk membeli tiket.")
            if st.button("🔑 Login / Daftar", key="login_prompt_" + event_id, type="primary"):
                queue_toast("Silakan login terlebih dahulu.", "warning")
                st.session_state["current_page"] = "Login_register"
                st.rerun()
        else:
            if st.button(
                "🎫 Beli Tiket Sekarang",
                key="open_modal_" + event_id,
                type="primary",
                use_container_width=True,
            ):
                st.session_state[modal_key] = True
                st.rerun()
    else:
        # Tampilkan modal beli tiket
        def on_success(result: dict) -> None:
            """Setelah booking berhasil — arahkan ke profil."""
            queue_toast("🎉 Tiket berhasil dipesan!", "success")
            st.session_state.pop(modal_key, None)
            st.session_state["current_page"] = "Profil_saya"
            st.rerun()

        def on_cancel() -> None:
            """User klik batal — tutup modal."""
            st.session_state.pop(modal_key, None)
            st.rerun()

        render_buy_ticket_modal(
            event=event,
            on_success=on_success,
            on_cancel=on_cancel,
        )




def _reset_buy_state(event_id: str) -> None:
    """Bersihkan semua state pembelian tiket untuk event tertentu."""
    keys = [
        "buy_step_", "buy_ticket_id_", "buy_ticket_name_",
        "buy_ticket_price_", "buy_qty_val_", "buy_payment_val_", "buy_payment_lbl_",
    ]
    for k in keys:
        st.session_state.pop(k + event_id, None)


def _render_demo_events() -> None:
    demo = [
        {"id": "demo_" + str(i),
         "title": "Demo Event — " + ("Teknologi" if i % 2 == 0 else "Bisnis") + " " + str(2026 + i),
         "short_description": "Event seru yang wajib dihadiri.",
         "location": ["Jakarta", "Bandung", "Online"][i % 3],
         "start_date": "2026-0" + str(8 + i) + "-15",
         "status": "upcoming",
         "tickets": [{"price": [0, 100000][i % 2]}],
         "registered_count": 50 + i * 20, "capacity": 200}
        for i in range(6)
    ]
    render_event_grid(events=demo, columns=3, grid_key="demo")
    st.caption("⚠️ Data demo — backend belum terhubung")
