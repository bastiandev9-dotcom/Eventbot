"""
Profil Saya Page — EventBot
"""

import streamlit as st
from components.ticket_card import render_ticket_list
from components.toast import render_toast, queue_toast
from hooks.use_auth import use_auth
from hooks.use_theme import use_theme
from utils.api_client import APIClient
from utils.session_manager import SessionManager
from utils.formatters import avatar_initials, format_datetime, format_status_badge


def render() -> None:
    theme = use_theme()
    theme["apply_theme"]()
    render_toast()

    auth = use_auth()
    if not auth["require_login"]("Silakan login untuk mengakses profil."):
        return

    user   = auth["user"] or {}
    token  = SessionManager.get_token()
    client = APIClient(token=token)

    # Profile header
    initials   = avatar_initials(user.get("name", ""))
    role_badge = format_status_badge(auth["role"])
    joined     = format_datetime(user.get("created_at", ""))
    name       = user.get("name", "User")
    email      = user.get("email", "")

    st.markdown(
        '<div style="background:linear-gradient(135deg,rgba(124,58,237,0.12),rgba(79,70,229,0.06));'
        'border:1px solid rgba(124,58,237,0.2);border-radius:20px;padding:2rem;'
        'display:flex;align-items:center;gap:1.5rem;margin-bottom:2rem;">'
        '<div style="width:72px;height:72px;border-radius:50%;'
        'background:linear-gradient(135deg,#7C3AED,#4F46E5);'
        'display:flex;align-items:center;justify-content:center;'
        'font-size:1.75rem;font-weight:800;color:white;'
        'box-shadow:0 4px 20px rgba(124,58,237,0.4);flex-shrink:0;">'
        + initials +
        '</div><div>'
        '<h2 style="font-size:1.5rem;font-weight:800;color:#F8F9FA;margin:0 0 0.25rem;">' + name + '</h2>'
        '<div style="font-size:0.875rem;color:#ADB5BD;margin-bottom:0.4rem;">' + email + '</div>'
        '<div style="display:flex;gap:0.5rem;align-items:center;flex-wrap:wrap;">'
        '<span style="font-size:0.8rem;">' + role_badge + '</span>'
        '<span style="color:#374151;font-size:0.75rem;">·</span>'
        '<span style="font-size:0.75rem;color:#4B5563;">Bergabung: ' + joined + '</span>'
        '</div></div></div>',
        unsafe_allow_html=True,
    )

    tab_tickets, tab_edit, tab_password = st.tabs(["🎫 Tiket Saya", "✏️ Edit Profil", "🔒 Ganti Password"])

    with tab_tickets:
        # Bust cache tiket jika ada flag refresh
        if st.session_state.pop("_profile_tickets_refresh", False):
            st.session_state.pop("_cached_my_registrations", None)
            st.session_state.pop("_cached_my_registrations_ts", None)

        _render_tickets_tab(client)

    with tab_edit:
        _render_edit_tab(user, client)

    with tab_password:
        _render_password_tab(client)


def _render_tickets_tab(client):
    st.markdown("**Tiket & Registrasi Saya**")
    filter_sel = st.radio("Filter Status", ["Semua", "✅ Aktif", "⏳ Waitlist", "❌ Dibatalkan"],
                          horizontal=True, key="ticket_filter", label_visibility="collapsed")
    tickets = _fetch_tickets(client)

    if filter_sel == "✅ Aktif":
        tickets = [t for t in tickets if t.get("status") in ("confirmed", "registered", "attended")]
    elif filter_sel == "⏳ Waitlist":
        tickets = [t for t in tickets if t.get("status") in ("pending", "waitlist")]
    elif filter_sel == "❌ Dibatalkan":
        tickets = [t for t in tickets if t.get("status") in ("cancelled", "cancelled_reg")]

    def on_cancel(tid):
        try:
            client.cancel_registration(tid)
            queue_toast("Pendaftaran berhasil dibatalkan.", "success")
            # Hapus cache registrasi agar list tiket langsung fresh
            st.session_state.pop("_cached_my_registrations", None)
            st.session_state.pop("_cached_my_registrations_ts", None)
            # Hapus cache event agar sold count & registered count ikut update
            stale = [k for k in st.session_state if k.startswith(("events_", "event_detail_"))]
            for k in stale:
                st.session_state.pop(k, None)
            st.session_state["_explorer_needs_refresh"] = True
        except Exception as e:
            queue_toast("Gagal membatalkan: " + str(e), "error")
        st.rerun()

    render_ticket_list(tickets=tickets, on_cancel=on_cancel,
                       empty_message="Kamu belum mendaftar event apapun.")


def _render_edit_tab(user, client):
    with st.form("edit_profile_form"):
        st.markdown("**Edit Informasi Profil**")
        name  = st.text_input("Nama Lengkap", value=user.get("name",""))
        st.text_input("Email", value=user.get("email",""), disabled=True,
                      help="Email tidak dapat diubah.")
        phone = st.text_input("Nomor HP", value=user.get("phone","") or "", placeholder="08xxxxxxxxxx")
        bio   = st.text_area("Bio", value=user.get("bio","") or "",
                              placeholder="Ceritakan sedikit tentang dirimu...", height=100)
        st.markdown("---")
        if st.form_submit_button("💾 Simpan Perubahan", type="primary", use_container_width=True):
            if not name or len(name.strip()) < 2:
                st.error("Nama minimal 2 karakter."); return
            try:
                client._put("/auth/profile", {"name": name.strip(),
                                               "phone": phone.strip() or None,
                                               "bio": bio.strip() or None})
                updated = dict(user)
                updated.update({"name": name.strip(), "phone": phone.strip() or None, "bio": bio.strip() or None})
                SessionManager.login(user=updated, token=SessionManager.get_token())
                queue_toast("Profil berhasil diperbarui!", "success")
                st.rerun()
            except Exception as e:
                st.error("❌ Gagal: " + str(e))


def _render_password_tab(client):
    with st.form("change_pass_form", clear_on_submit=True):
        st.markdown("**🔒 Ganti Password**")
        old_p  = st.text_input("Password Lama", type="password", placeholder="••••••••")
        new_p  = st.text_input("Password Baru", type="password", placeholder="Min. 6 karakter")
        conf_p = st.text_input("Konfirmasi Password Baru", type="password", placeholder="Ulangi password baru")
        if st.form_submit_button("💾 Simpan Password", type="primary", use_container_width=True):
            if not old_p or not new_p:
                st.error("Semua field wajib diisi.")
            elif len(new_p) < 6:
                st.error("Password baru minimal 6 karakter.")
            elif new_p != conf_p:
                st.error("Konfirmasi password tidak cocok.")
            else:
                try:
                    result = client.change_password(old_p, new_p)
                    if result.get("success"):
                        queue_toast("Password berhasil diubah!", "success")
                        st.rerun()
                    else:
                        st.error(result.get("message","Gagal mengubah password."))
                except Exception as e:
                    st.error("❌ " + str(e))


def _fetch_tickets(client):
    import time
    cache_key = "_cached_my_registrations"
    ts_key    = "_cached_my_registrations_ts"
    ttl       = 5  # detik — cukup untuk menghindari double-fetch, tapi langsung stale setelah cancel

    cached = st.session_state.get(cache_key)
    ts     = st.session_state.get(ts_key, 0)
    if cached is not None and (time.time() - ts) < ttl:
        return cached

    try:
        data = client.get_my_registrations().get("data", [])
        st.session_state[cache_key] = data
        st.session_state[ts_key]    = time.time()
        return data
    except Exception:
        return [
            {"id": "reg_1", "event_id": "evt_1", "event_title": "Tech Conference 2026",
             "event_date": "2026-08-15", "event_location": "Jakarta Convention Center",
             "ticket_name": "Regular", "ticket_code": "EVT-TC2026-001",
             "status": "registered", "price": 150000, "registered_at": "2026-07-01T10:00:00"},
            {"id": "reg_2", "event_id": "evt_2", "event_title": "Design Workshop",
             "event_date": "2026-09-05", "event_location": "Bandung Creative Hub",
             "ticket_name": "Early Bird", "ticket_code": "EVT-DW2026-042",
             "status": "registered", "price": 0, "registered_at": "2026-07-03T14:30:00"},
        ]
