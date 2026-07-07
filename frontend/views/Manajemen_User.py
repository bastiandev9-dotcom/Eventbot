import streamlit as st
from components.data_table import render_data_table, render_table_header, render_confirm_delete
from components.toast import render_toast, queue_toast
from hooks.use_auth import use_auth
from hooks.use_theme import use_theme
from utils.api_client import APIClient
from utils.session_manager import SessionManager
from utils.formatters import format_status_badge


def render() -> None:
    theme = use_theme()
    theme["apply_theme"]()
    render_toast()

    auth = use_auth()
    if not auth["require_role"]("admin"):
        return

    token  = SessionManager.get_token()
    client = APIClient(token=token)

    st.markdown(
        '<div style="margin-bottom:1.5rem;">'
        '<h1 style="font-size:1.75rem;font-weight:800;color:#F8F9FA;margin:0 0 0.25rem;">👥 Manajemen User</h1>'
        '<p style="color:#6B7280;font-size:0.9rem;margin:0;">Kelola akun user, role, dan status</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    users = _fetch_users(client)

    if "edit_user" not in st.session_state:
        st.session_state["edit_user"] = None
    if "delete_user_id" not in st.session_state:
        st.session_state["delete_user_id"] = None

    if st.session_state["edit_user"] is not None:
        _render_edit_form(st.session_state["edit_user"], client)
        return

    if st.session_state["delete_user_id"]:
        uid    = st.session_state["delete_user_id"]
        target = next((u for u in users if str(u.get("id")) == uid), {})
        render_confirm_delete(
            item_name=target.get("name", uid),
            on_confirm=lambda: _do_delete(uid, client),
            on_cancel=lambda: st.session_state.update({"delete_user_id": None}) or st.rerun(),
            key="del_user",
        )
        st.markdown("---")

    col_map = {"name": "Nama", "email": "Email", "role": "Role",
               "is_active": "Status", "created_at": "Bergabung"}

    def on_edit(row):
        st.session_state["edit_user"] = row; st.rerun()
    def on_delete(uid):
        st.session_state["delete_user_id"] = uid; st.rerun()

    tab_all, tab_admin, tab_part = st.tabs(["Semua", "Admin", "Peserta"])

    with tab_all:
        render_table_header("Semua User", count=len(users),
                            on_add=lambda: st.session_state.update({"edit_user": {}}) or st.rerun())
        render_data_table(_fmt_users(users), columns=col_map, key="ut_all",
                          on_edit=on_edit, on_delete=on_delete)

    with tab_admin:
        admins = [u for u in users if u.get("role") == "admin"]
        render_table_header("Admin", count=len(admins))
        render_data_table(_fmt_users(admins), columns=col_map, key="ut_adm", on_edit=on_edit)

    with tab_part:
        parts = [u for u in users if u.get("role") == "participant"]
        render_table_header("Peserta", count=len(parts))
        render_data_table(_fmt_users(parts), columns=col_map, key="ut_prt",
                          on_edit=on_edit, on_delete=on_delete)


def _fetch_users(client):
    try:
        return client._get("/admin/users").get("data", [])
    except Exception:
        return [
            {"id": "1", "name": "Admin Utama", "email": "admin@eventbot.com", "role": "admin",       "is_active": True,  "created_at": "2026-01-01"},
            {"id": "2", "name": "Budi Santoso", "email": "budi@email.com",    "role": "participant", "is_active": True,  "created_at": "2026-02-15"},
            {"id": "3", "name": "Sari Dewi",    "email": "sari@email.com",    "role": "participant", "is_active": True,  "created_at": "2026-03-10"},
            {"id": "4", "name": "Ahmad Rizki",  "email": "ahmad@email.com",   "role": "participant", "is_active": False, "created_at": "2026-04-05"},
        ]


def _fmt_users(users):
    return [{"id": u.get("id",""), "name": u.get("name","-"), "email": u.get("email","-"),
             "role": format_status_badge(u.get("role",""), with_emoji=True),
             "is_active": "✅ Aktif" if u.get("is_active", True) else "⛔ Nonaktif",
             "created_at": (u.get("created_at","")[:10] if u.get("created_at") else "-")}
            for u in users]


def _render_edit_form(user: dict, client) -> None:
    is_new = not user.get("id")
    title  = "➕ Tambah User Baru" if is_new else "✏️ Edit User: " + user.get("name","")
    st.markdown('<h2 style="font-size:1.25rem;font-weight:700;color:#F8F9FA;">' + title + '</h2>',
                unsafe_allow_html=True)
    if st.button("← Kembali", key="edit_user_back"):
        st.session_state["edit_user"] = None; st.rerun()
    st.markdown("---")

    with st.form("edit_user_form"):
        name      = st.text_input("Nama Lengkap", value=user.get("name",""))
        email     = st.text_input("Email",         value=user.get("email",""))
        role      = st.selectbox("Role", ["participant", "admin"],
                                  index=["participant", "admin"].index(user.get("role", "participant")) if user.get("role") in ["participant", "admin"] else 0)
        is_active = st.checkbox("Akun Aktif", value=user.get("is_active", True))
        if is_new:
            password = st.text_input("Password", type="password", placeholder="Min. 6 karakter")
        else:
            st.info("Kosongkan password jika tidak ingin mengubahnya.")
            password = st.text_input("Password Baru (opsional)", type="password")

        if st.form_submit_button("💾 Simpan" if not is_new else "➕ Tambah",
                                  type="primary", use_container_width=True):
            if not name or not email:
                st.error("Nama dan email wajib diisi.")
                return
            payload = {"name": name, "email": email, "role": role, "is_active": is_active}
            if password:
                payload["password"] = password
            try:
                if is_new:
                    client._post("/admin/users", payload)
                    queue_toast("User berhasil ditambahkan!", "success")
                else:
                    client._put("/admin/users/" + str(user["id"]), payload)
                    queue_toast("User berhasil diperbarui!", "success")
                st.session_state["edit_user"] = None; st.rerun()
            except Exception as e:
                st.error("❌ Gagal: " + str(e))


def _do_delete(uid, client):
    try:
        client._delete("/admin/users/" + uid)
        queue_toast("User berhasil dihapus.", "success")
    except Exception as e:
        queue_toast("Gagal: " + str(e), "error")
    st.session_state["delete_user_id"] = None
