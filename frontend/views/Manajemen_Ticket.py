"""
Manajemen Tiket Page
====================
Kelola tiket per event: pricing, kuota, dan analytics.
Tema: Form + Table + Analytics
"""

import streamlit as st
from components.data_table import render_data_table, render_table_header, render_confirm_delete
from components.metric_card import render_metric_row
from components.toast import render_toast, queue_toast
from hooks.use_auth import use_auth
from hooks.use_theme import use_theme
from utils.api_client import APIClient
from utils.session_manager import SessionManager
from utils.formatters import format_price, format_status_badge


def render() -> None:
    """Entry point halaman Manajemen Tiket."""
    theme = use_theme()
    theme["apply_theme"]()
    render_toast()

    auth = use_auth()
    if not auth["require_role"]("admin"):
        return

    token  = SessionManager.get_token()
    client = APIClient(token=token)

    st.markdown("""
    <div style="margin-bottom:1.5rem; animation:fadeInDown 0.4s ease both;">
        <h1 style="font-size:1.75rem; font-weight:800; color:#F8F9FA; margin:0 0 0.25rem;">
            🎫 Manajemen Tiket
        </h1>
        <p style="color:#6B7280; font-size:0.9rem; margin:0;">Kelola jenis tiket, harga, kuota, dan konfirmasi pembayaran</p>
    </div>
    """, unsafe_allow_html=True)

    tab_tiket, tab_konfirmasi = st.tabs(["🎫 Tiket Event", "💳 Konfirmasi Pembayaran"])

    with tab_tiket:
        _render_ticket_management(client)

    with tab_konfirmasi:
        _render_payment_confirmation(client)


def _render_ticket_management(client: APIClient) -> None:
    """Tab manajemen tiket (tambah/edit/hapus tiket per event)."""
    # ── State ─────────────────────────────────────────────
    if "mt_edit_ticket" not in st.session_state:
        st.session_state["mt_edit_ticket"] = None
    if "mt_delete_id" not in st.session_state:
        st.session_state["mt_delete_id"] = None

    # ── Ambil data events (untuk form tambah tiket) ───────
    events = _fetch_events(client)

    # ── Modal form tiket ──────────────────────────────────
    if st.session_state["mt_edit_ticket"] is not None:
        _render_ticket_form(st.session_state["mt_edit_ticket"], client, None, events)
        return

    # ── Confirm delete ────────────────────────────────────
    if st.session_state["mt_delete_id"]:
        render_confirm_delete(
            item_name=f"Tiket ID: {st.session_state['mt_delete_id']}",
            on_confirm=lambda: _do_delete_ticket(st.session_state["mt_delete_id"], client),
            on_cancel=lambda: st.session_state.update({"mt_delete_id": None}),
            key="del_ticket",
        )
        st.markdown("---")

    # ── Tiket list — ambil semua tiket lalu filter di frontend ──
    tickets       = _fetch_tickets(client, None)

    # Filter per event
    event_options = {"— Semua Event —": None}
    event_options.update({e.get("title", e["id"]): e["id"] for e in events})
    selected_label = st.selectbox("Filter per Event", options=list(event_options.keys()), key="mt_event_filter")
    selected_event_id = event_options.get(selected_label)

    if selected_event_id:
        tickets = [t for t in tickets if str(t.get("event_id", "")) == str(selected_event_id)]

    total_tickets = len(tickets)
    total_quota   = sum(t.get("quota", 0) for t in tickets)
    total_sold    = sum(t.get("sold_count", 0) for t in tickets)
    free_count    = sum(1 for t in tickets if not t.get("price"))

    render_metric_row([
        {"label": "Jenis Tiket",  "value": str(total_tickets), "icon": "🎫", "color": "purple"},
        {"label": "Total Kuota",  "value": str(total_quota),   "icon": "🪑", "color": "blue"},
        {"label": "Terjual",      "value": str(total_sold),    "icon": "✅", "color": "green"},
        {"label": "Tiket Gratis", "value": str(free_count),    "icon": "🆓", "color": "teal"},
    ])
    st.markdown("<br>", unsafe_allow_html=True)

    col_map = {
        "event_title": "Event",
        "name":        "Nama Tiket",
        "price":       "Harga",
        "quota":       "Kuota",
        "sold_count":  "Terjual",
        "status":      "Status",
    }

    def on_edit(row: dict) -> None:
        tid      = str(row.get("id", ""))
        original = next((t for t in tickets if str(t.get("id")) == tid), row)
        st.session_state["mt_edit_ticket"] = original
        st.rerun()

    def on_delete(tid: str) -> None:
        st.session_state["mt_delete_id"] = tid
        st.rerun()

    # Search di luar tabel agar count badge sinkron
    search_q = st.text_input("🔍 Cari tiket...", key="ticket_search", placeholder="Cari nama tiket atau event...")
    formatted = _format_tickets(tickets)
    if search_q:
        q_lower = search_q.lower()
        formatted = [t for t in formatted if any(
            q_lower in str(v).lower() for v in t.values()
        )]

    render_table_header(
        title="Daftar Tiket", count=len(formatted),
        on_add=lambda: st.session_state.update({"mt_edit_ticket": {}}),
        add_label="➕ Tambah Tiket",
    )
    render_data_table(
        data=formatted, columns=col_map,
        key="ticket_table", on_edit=on_edit, on_delete=on_delete,
        id_field="id", page_size=10,
        searchable=False,  # search sudah ditangani di atas
    )


def _render_payment_confirmation(client: APIClient) -> None:
    """Tab konfirmasi pembayaran — list registrasi pending dan aksi konfirmasi/tolak."""
    st.markdown(
        '<div style="margin-bottom:1rem;">'
        '<h3 style="font-size:1.1rem;font-weight:700;color:#F8F9FA;margin:0 0 0.25rem;">💳 Registrasi Menunggu Konfirmasi</h3>'
        '<p style="color:#6B7280;font-size:0.85rem;margin:0;">Konfirmasi pembayaran peserta yang sudah transfer</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Filter event opsional
    events        = _fetch_events(client)
    event_opts    = {"— Semua Event —": None}
    event_opts.update({e.get("title", e["id"]): e["id"] for e in events})
    ev_label      = st.selectbox("Filter Event", options=list(event_opts.keys()), key="konfirmasi_event_filter")
    filter_eid    = event_opts.get(ev_label)

    # Ambil data pending
    pending = _fetch_pending_registrations(client, filter_eid)

    if not pending:
        st.success("✅ Tidak ada pembayaran yang menunggu konfirmasi.")
        return

    st.markdown(f'<p style="color:#F59E0B;font-size:0.85rem;margin-bottom:1rem;">⏳ {len(pending)} registrasi menunggu konfirmasi</p>', unsafe_allow_html=True)

    for reg in pending:
        _render_pending_card(reg, client)


def _render_pending_card(reg: dict, client: APIClient) -> None:
    """Render satu card registrasi pending dengan tombol konfirmasi/tolak."""
    reg_id       = str(reg.get("id", ""))
    user_name    = reg.get("user_name", "-")
    user_email   = reg.get("user_email", "-")
    event_title  = reg.get("event_title", "-")
    ticket_name  = reg.get("ticket_name", "-")
    total_price  = reg.get("total_price", 0)
    payment_meth = reg.get("payment_method") or "Tidak diketahui"
    quantity     = reg.get("quantity", 1)
    created_at   = reg.get("created_at", "")

    payment_labels = {
        "transfer_bank": "💳 Transfer Bank",
        "e_wallet":      "📱 E-Wallet",
        "free":          "🆓 Gratis",
    }
    payment_display = payment_labels.get(payment_meth, payment_meth)

    from utils.formatters import format_price, format_datetime
    st.markdown(
        f'<div style="background:rgba(255,255,255,0.04);border:1px solid rgba(245,158,11,0.3);'
        f'border-radius:12px;padding:1.25rem;margin-bottom:1rem;">'
        f'<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:0.75rem;">'
        f'<div>'
        f'<div style="font-size:0.7rem;font-weight:700;color:#6B7280;text-transform:uppercase;letter-spacing:0.08em;">{ticket_name}</div>'
        f'<div style="font-size:1rem;font-weight:700;color:#F8F9FA;margin:0.2rem 0;">{event_title}</div>'
        f'<div style="font-size:0.8rem;color:#ADB5BD;">👤 {user_name} · {user_email}</div>'
        f'</div>'
        f'<div style="text-align:right;">'
        f'<div style="font-size:1.1rem;font-weight:700;color:#10B981;">{format_price(total_price)}</div>'
        f'<div style="font-size:0.75rem;color:#6B7280;">{payment_display} · {quantity} tiket</div>'
        f'</div></div>'
        f'<div style="font-size:0.75rem;color:#4B5563;">Dipesan: {format_datetime(created_at)} · ID: {reg_id[:8].upper()}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([2, 2, 3])
    with col1:
        if st.button("✅ Konfirmasi", key=f"confirm_{reg_id}", type="primary", use_container_width=True):
            try:
                client.confirm_payment(reg_id)
                queue_toast(f"Pembayaran {user_name} dikonfirmasi!", "success")
                st.rerun()
            except Exception as e:
                queue_toast(f"Gagal: {e}", "error")
    with col2:
        if st.button("❌ Tolak", key=f"reject_{reg_id}", use_container_width=True):
            st.session_state[f"confirm_reject_{reg_id}"] = True
            st.rerun()

    if st.session_state.get(f"confirm_reject_{reg_id}"):
        st.warning(f"⚠️ Yakin ingin menolak registrasi **{user_name}**?")
        r1, r2 = st.columns(2)
        with r1:
            if st.button("Ya, Tolak", key=f"reject_yes_{reg_id}", type="primary", use_container_width=True):
                try:
                    client.reject_registration(reg_id)
                    queue_toast(f"Registrasi {user_name} ditolak.", "success")
                    st.session_state.pop(f"confirm_reject_{reg_id}", None)
                    st.rerun()
                except Exception as e:
                    queue_toast(f"Gagal: {e}", "error")
        with r2:
            if st.button("Batal", key=f"reject_no_{reg_id}", use_container_width=True):
                st.session_state.pop(f"confirm_reject_{reg_id}", None)
                st.rerun()


def _fetch_pending_registrations(client: APIClient, event_id=None) -> list:
    try:
        params = {"status": "pending"}
        if event_id:
            params["event_id"] = event_id
        result = client._get("/registrations/", params)
        return result.get("data", [])
    except Exception:
        return []


def _fetch_events(client: APIClient) -> list:
    try:
        result = client._get("/events/", {"page_size": 100})
        return result.get("data", [])
    except Exception:
        return [
            {"id": "1", "title": "Tech Conference 2026"},
            {"id": "2", "title": "Design Workshop"},
            {"id": "3", "title": "Startup Pitch Night"},
        ]


def _fetch_tickets(client: APIClient, event_id=None) -> list:
    try:
        params = {}
        if event_id:
            params["event_id"] = event_id
        result = client._get("/tickets/", params)
        return result.get("data", [])
    except Exception as e:
        st.caption(f"⚠️ Gagal memuat tiket dari server: {e}. Menampilkan data demo.")
        # Demo data — filter sesuai event_id jika dipilih
        all_demo = [
            {"id": "t1", "event_id": "1", "event_title": "Tech Conference", "name": "Regular",   "price": 150000, "quota": 200, "sold_count": 130, "status": "active"},
            {"id": "t2", "event_id": "1", "event_title": "Tech Conference", "name": "VIP",        "price": 350000, "quota": 50,  "sold_count": 45,  "status": "active"},
            {"id": "t3", "event_id": "2", "event_title": "Design Workshop", "name": "Early Bird", "price": 0,      "quota": 50,  "sold_count": 50,  "status": "sold_out"},
            {"id": "t4", "event_id": "3", "event_title": "Startup Pitch",   "name": "General",    "price": 50000,  "quota": 150, "sold_count": 60,  "status": "active"},
        ]
        if event_id:
            return [t for t in all_demo if t["event_id"] == str(event_id)]
        return all_demo


def _format_tickets(tickets: list) -> list:
    return [
        {
            "id":          str(t.get("id", "")),
            "event_title": t.get("event_title") or t.get("event", {}).get("title", "-"),
            "name":        t.get("name", "-"),
            "price":       format_price(t.get("price", 0)),
            "quota":       str(t.get("quota", 0)),
            "sold_count":  str(t.get("sold_count", 0)),
            "status":      format_status_badge(t.get("status", "active"), with_emoji=True),
        }
        for t in tickets
    ]


def _render_ticket_form(ticket: dict, client: APIClient, default_event_id, events: list) -> None:
    """Render form tambah/edit tiket."""
    is_new = not ticket.get("id")
    title  = "➕ Tambah Tiket Baru" if is_new else f"✏️ Edit Tiket: {ticket.get('name','')}"

    st.markdown(f'<h2 style="font-size:1.25rem; font-weight:700; color:#F8F9FA;">{title}</h2>',
                unsafe_allow_html=True)

    if st.button("← Kembali", key="ticket_form_back"):
        st.session_state["mt_edit_ticket"] = None
        st.rerun()

    st.markdown("---")

    with st.form("ticket_form"):
        # Pilih event untuk tiket baru
        if is_new:
            event_opts = {e.get("title", e["id"]): e["id"] for e in events}
            ev_label   = st.selectbox("Event *", options=list(event_opts.keys()))
            event_id   = event_opts.get(ev_label)
        else:
            event_id = ticket.get("event_id", default_event_id)
            ev_name  = next((e["title"] for e in events if str(e["id"]) == str(event_id)), str(event_id))
            st.markdown(f'**Event:** {ev_name}')

        col1, col2 = st.columns(2)
        with col1:
            name  = st.text_input("Nama Tiket *", value=ticket.get("name", "") or "", placeholder="Regular / VIP / Early Bird")
            price = st.number_input("Harga (0 = Gratis)", min_value=0, value=int(ticket.get("price", 0) or 0), step=10000)
        with col2:
            quota       = st.number_input("Kuota", min_value=0, value=int(ticket.get("quota") or ticket.get("quantity") or 0))
            status_idx  = {"available": 0, "sold_out": 1, "reserved": 2, "unavailable": 3}.get(ticket.get("status", "available"), 0)
            status      = st.selectbox("Status", ["available", "sold_out", "reserved", "unavailable"], index=status_idx)

        description = st.text_area("Deskripsi Tiket (opsional)",
                                   value=ticket.get("description", "") or "",
                                   height=80)

        submitted = st.form_submit_button(
            "💾 Simpan Tiket",
            type="primary",
            use_container_width=True,
        )

        if submitted:
            if not name or not str(name).strip():
                st.error("Nama tiket wajib diisi.")
                return

            base_payload = {
                "name":        str(name).strip(),
                "price":       float(price),
                "quota":       int(quota),
                "status":      status,
                "description": str(description).strip() or None,
            }

            try:
                if is_new:
                    create_payload = dict(base_payload, event_id=event_id)
                    client._post("/tickets/", create_payload)
                    queue_toast("Tiket berhasil ditambahkan!", "success")
                    # Set filter ke event yang baru ditambahkan tiketnya
                    st.session_state["mt_event_filter"] = ev_label
                else:
                    client._put(f"/tickets/{ticket['id']}", base_payload)
                    queue_toast("Tiket berhasil diperbarui!", "success")
                st.session_state["mt_edit_ticket"] = None
                st.session_state["ticket_table_page"] = 1
                st.rerun()
            except Exception as e:
                st.error(f"❌ Gagal menyimpan tiket: {e}")


def _do_delete_ticket(tid: str, client: APIClient) -> None:
    try:
        client._delete(f"/tickets/{tid}")
        queue_toast("Tiket berhasil dihapus.", "success")
    except Exception as e:
        queue_toast(f"Gagal: {e}", "error")
    finally:
        st.session_state["mt_delete_id"] = None
