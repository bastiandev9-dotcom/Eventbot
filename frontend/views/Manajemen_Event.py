"""
Manajemen Event Page
====================
CRUD event untuk admin.
Tema: Form + Table
"""

import streamlit as st
from components.data_table import render_data_table, render_table_header, render_confirm_delete
from components.toast import render_toast, queue_toast
from hooks.use_auth import use_auth
from hooks.use_events import use_events
from hooks.use_theme import use_theme
from utils.formatters import format_date, format_status_badge
from utils.session_manager import SessionManager


def render() -> None:
    """Entry point halaman Manajemen Event."""
    theme = use_theme()
    theme["apply_theme"]()
    render_toast()

    auth = use_auth()
    if not auth["require_role"]("admin"):
        return

    events_hook = use_events()

    # ── State modal ───────────────────────────────────────
    if "me_edit_event" not in st.session_state:
        st.session_state["me_edit_event"] = None
    if "me_delete_id" not in st.session_state:
        st.session_state["me_delete_id"] = None

    # ── Page Header ───────────────────────────────────────
    st.markdown("""
    <div style="margin-bottom:1.5rem; animation:fadeInDown 0.4s ease both;">
        <h1 style="font-size:1.75rem; font-weight:800; color:#F8F9FA; margin:0 0 0.25rem;">
            🎪 Manajemen Event
        </h1>
        <p style="color:#6B7280; font-size:0.9rem; margin:0;">Buat, edit, dan hapus event</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Modal edit/tambah ─────────────────────────────────
    if st.session_state["me_edit_event"] is not None:
        _render_event_form(st.session_state["me_edit_event"], events_hook)
        return

    # ── Confirm delete ────────────────────────────────────
    if st.session_state["me_delete_id"]:
        del_id = st.session_state["me_delete_id"]
        # Tampilkan konfirmasi
        st.markdown(
            '<div style="background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.25);'
            'border-radius:12px;padding:1.25rem;margin:0.5rem 0;">'
            '<div style="font-weight:600;color:#EF4444;margin-bottom:0.5rem;">⚠️ Konfirmasi Hapus</div>'
            '<div style="color:#ADB5BD;font-size:0.9rem;">Yakin ingin menghapus event ini? '
            'Tindakan ini tidak dapat dibatalkan.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button("🗑️ Ya, Hapus", key="del_confirm_yes", type="primary", use_container_width=True):
                success, msg = events_hook["delete_event"](del_id)
                st.session_state["me_delete_id"] = None
                if success:
                    _bust_event_cache()
                queue_toast(msg, "success" if success else "error")
                st.rerun()
        with col_no:
            if st.button("❌ Batal", key="del_confirm_no", use_container_width=True):
                st.session_state["me_delete_id"] = None
                st.rerun()
        # Hentikan render di sini — tabel tidak perlu ditampilkan saat konfirmasi aktif
        return

    # ── Ambil events ──────────────────────────────────────
    role = auth["role"]
    if role == "admin":
        events, _, err = events_hook["fetch_events"](status="", page_size=100, use_cache=False)
    else:
        events, err = events_hook["fetch_my_events"]()
        if isinstance(events, tuple):
            events, err = events

    if err:
        st.warning(f"⚠️ {err} — menampilkan data demo")
        events = _demo_events()

    # ── Tabs status ───────────────────────────────────────
    all_events      = events
    upcoming_events = [e for e in events if e.get("status") == "upcoming"]
    ongoing_events  = [e for e in events if e.get("status") == "ongoing"]
    completed_events= [e for e in events if e.get("status") == "completed"]

    col_map = {
        "title":      "Judul Event",
        "location":   "Lokasi",
        "start_date": "Tanggal",
        "status":     "Status",
        "capacity":   "Kapasitas",
    }

    def on_edit(row: dict) -> None:
        # Load detail lengkap event (termasuk is_published, start_time, end_time, dll)
        eid = str(row.get("id", ""))
        detail, err = events_hook["fetch_event"](eid)
        if detail:
            st.session_state["me_edit_event"] = detail
        else:
            # Fallback ke data dari list jika fetch_event gagal
            original = next((e for e in events if str(e.get("id")) == eid), row)
            st.session_state["me_edit_event"] = original
        st.rerun()

    def on_delete(eid: str) -> None:
        st.session_state["me_delete_id"] = eid
        st.rerun()

    def on_view(eid: str) -> None:
        st.session_state["detail_event_id"] = eid
        st.session_state["current_page"] = "Event_Explorer"
        st.rerun()

    tab_all, tab_up, tab_on, tab_done = st.tabs([
        f"Semua ({len(all_events)})",
        f"Akan Datang ({len(upcoming_events)})",
        f"Berlangsung ({len(ongoing_events)})",
        f"Selesai ({len(completed_events)})",
    ])

    with tab_all:
        render_table_header(
            title="Semua Event",
            count=len(all_events),
            on_add=lambda: st.session_state.update({"me_edit_event": {}}),
            add_label="➕ Buat Event",
        )
        render_data_table(
            data=_format_events(all_events),
            columns=col_map,
            key="event_table_all",
            on_edit=on_edit,
            on_delete=on_delete,
            on_view=on_view,
            id_field="id",
        )

    with tab_up:
        render_data_table(
            data=_format_events(upcoming_events),
            columns=col_map,
            key="event_table_up",
            on_edit=on_edit,
            on_delete=on_delete,
            on_view=on_view,
            id_field="id",
        )

    with tab_on:
        render_data_table(
            data=_format_events(ongoing_events),
            columns=col_map,
            key="event_table_on",
            on_edit=on_edit,
            on_view=on_view,
            id_field="id",
        )

    with tab_done:
        render_data_table(
            data=_format_events(completed_events),
            columns=col_map,
            key="event_table_done",
            on_view=on_view,
            id_field="id",
        )


def _format_events(events: list) -> list:
    return [
        {
            "id":         str(e.get("id", "")),
            "title":      e.get("title", "-"),
            "location":   e.get("location", "-"),
            "start_date": format_date(e.get("start_date", "")),
            "status":     format_status_badge(e.get("status", ""), with_emoji=True),
            "capacity":   str(e.get("capacity", 0)) if e.get("capacity") else "Tak terbatas",
        }
        for e in events
    ]


def _render_event_form(event: dict, events_hook: dict) -> None:
    """Render form tambah/edit event."""
    is_new = not event.get("id")
    title  = "➕ Tambah Event Baru" if is_new else f"✏️ Edit: {event.get('title','')}"

    st.markdown(f'<h2 style="font-size:1.25rem; font-weight:700; color:#F8F9FA;">{title}</h2>',
                unsafe_allow_html=True)

    if st.button("← Kembali ke Daftar", key="ev_form_back"):
        st.session_state["me_edit_event"] = None
        st.session_state.pop("ev_uploaded_url", None)
        st.rerun()

    st.markdown("---")

    # ── Upload gambar di LUAR form (file_uploader tidak bisa di dalam st.form) ──
    st.markdown("**Gambar Event**")
    st.caption("Upload file gambar dari komputer, atau isi URL di dalam form di bawah.")

    uploaded_file = st.file_uploader(
        "Upload File Gambar (jpg, png, webp)",
        type=["jpg", "jpeg", "png", "webp"],
        key="event_img_upload",
    )

    # Jika ada file baru diupload, langsung kirim ke backend dan simpan URL ke session_state
    if uploaded_file is not None:
        import requests as _req
        import os as _os
        _BACKEND_URL = _os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
        token = SessionManager.get_token()
        upload_key = f"ev_uploaded_url_{uploaded_file.name}_{len(uploaded_file.getvalue())}"
        if st.session_state.get("ev_upload_key") != upload_key:
            with st.spinner("Mengupload gambar..."):
                try:
                    resp = _req.post(
                        f"{_BACKEND_URL}/api/v1/upload/image",
                        files={"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)},
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=30,
                    )
                    if resp.ok:
                        uploaded_url = resp.json().get("url", "")
                        st.session_state["ev_uploaded_url"] = uploaded_url
                        st.session_state["ev_upload_key"]   = upload_key
                        st.success(f"Gambar berhasil diupload!")
                    else:
                        st.error(f"Gagal upload: {resp.text}")
                except Exception as e:
                    st.error(f"Gagal upload: {e}")

        # Tampilkan preview
        preview_url = st.session_state.get("ev_uploaded_url", "")
        if preview_url:
            st.image(preview_url, width=200, caption="Preview gambar yang diupload")

    st.markdown("---")

    with st.form("event_form", clear_on_submit=False):
        ev_title = st.text_input("Judul Event *", value=event.get("title", ""), placeholder="Nama event yang menarik")

        short_desc = st.text_area(
            "Deskripsi Singkat *",
            value=event.get("short_description", ""),
            placeholder="Max 500 karakter",
            max_chars=500,
            height=80,
        )

        description = st.text_area(
            "Deskripsi Lengkap *",
            value=event.get("description", ""),
            placeholder="Jelaskan detail event, agenda, pembicara, dll.",
            height=150,
        )

        # Tanggal & Waktu
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Tanggal Mulai *", key="ev_form_start")
            start_time = st.text_input("Jam Mulai", value=event.get("start_time", "") or "", placeholder="09:00")
        with col2:
            end_date = st.date_input("Tanggal Selesai *", key="ev_form_end")
            end_time = st.text_input("Jam Selesai", value=event.get("end_time", "") or "", placeholder="17:00")

        # Lokasi
        location     = st.text_input("Lokasi *", value=event.get("location", ""), placeholder="Nama venue / Online")
        location_url = st.text_input("Link Maps (opsional)", value=event.get("location_map_url", "") or "")

        # Kapasitas & Status
        col3, col4 = st.columns(2)
        with col3:
            capacity = st.number_input("Kapasitas (0 = tak terbatas)",
                                       min_value=0, value=int(event.get("capacity", 0) or 0))
        with col4:
            status_idx = {"upcoming": 0, "ongoing": 1, "completed": 2, "cancelled": 3}.get(
                event.get("status", "upcoming"), 0)
            status = st.selectbox("Status", ["upcoming", "ongoing", "completed", "cancelled"],
                                  index=status_idx)

        # URL gambar manual (fallback jika tidak upload file)
        current_img = st.session_state.get("ev_uploaded_url") or event.get("image_url", "") or ""
        url_input = st.text_input(
            "URL Gambar (opsional, akan dipakai jika tidak upload file)",
            value=current_img,
            placeholder="https://...",
        )

        is_published = st.checkbox("Publikasikan event", value=bool(event.get("is_published", False)))

        submitted = st.form_submit_button(
            "💾 Simpan Event" if not is_new else "🚀 Buat Event",
            type="primary",
            use_container_width=True,
        )

        if submitted:
            if not ev_title or not description or not location:
                st.error("⚠️ Judul, deskripsi, dan lokasi wajib diisi.")
                return

            # Prioritas: file yang sudah diupload > URL manual > gambar lama
            final_image_url = (
                st.session_state.get("ev_uploaded_url")
                or url_input.strip()
                or event.get("image_url")
                or None
            )

            payload = {
                "title":             ev_title.strip(),
                "description":       description.strip(),
                "short_description": short_desc.strip() or description[:200],
                "start_date":        start_date.strftime("%Y-%m-%d"),
                "end_date":          end_date.strftime("%Y-%m-%d"),
                "start_time":        start_time.strip() or None,
                "end_time":          end_time.strip() or None,
                "location":          location.strip(),
                "location_map_url":  location_url.strip() or None,
                "image_url":         final_image_url,
                "capacity":          int(capacity),
                "status":            status,
                "is_published":      is_published,
            }

            with st.spinner("Menyimpan..."):
                if is_new:
                    success, msg, _ = events_hook["create_event"](payload)
                else:
                    success, msg, _ = events_hook["update_event"](str(event["id"]), payload)

            if success:
                queue_toast(msg, "success")
                _bust_event_cache()
                st.session_state["me_edit_event"] = None
                st.session_state.pop("ev_uploaded_url", None)
                st.session_state.pop("ev_upload_key", None)
                st.rerun()
            else:
                st.error(f"❌ {msg}")


def _bust_event_cache() -> None:
    """
    Hapus semua cache event agar Event Explorer reload data terbaru.

    AMAN: Fungsi ini hanya menghapus key cache event — TIDAK menyentuh
    auth keys (access_token, is_logged_in, user, user_role, dll).
    """
    # Daftar prefix cache event yang boleh dihapus
    _CACHE_PREFIXES = ("events_", "event_detail_")

    # Daftar key auth yang harus DILINDUNGI (tidak boleh dihapus)
    _PROTECTED_KEYS = {
        "access_token", "is_logged_in", "user", "user_role",
        "current_page", "theme", "toast_message", "notifications",
        "chat_session_token", "chat_history",
        # state halaman Manajemen_Event
        "me_edit_event", "me_delete_id",
    }

    stale = [
        k for k in list(st.session_state.keys())
        if any(k.startswith(prefix) for prefix in _CACHE_PREFIXES)
        and k not in _PROTECTED_KEYS
    ]
    for k in stale:
        del st.session_state[k]

    # Tandai Event Explorer perlu refresh saat dibuka
    st.session_state["_explorer_needs_refresh"] = True


def _do_delete(eid: str, events_hook: dict) -> None:
    success, msg = events_hook["delete_event"](eid)
    queue_toast(msg, "success" if success else "error")
    st.session_state["me_delete_id"] = None


def _demo_events() -> list:
    return [
        {"id": f"demo_{i}", "title": f"Demo Event {i}", "location": "Jakarta",
         "start_date": "2026-08-15", "status": ["upcoming","ongoing","completed"][i%3],
         "capacity": 200}
        for i in range(5)
    ]
