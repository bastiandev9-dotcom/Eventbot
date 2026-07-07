"""
Login / Register Page — EventBot
Layout: form di tengah, tanpa panel kiri
"""

import streamlit as st
from components.toast import render_toast, queue_toast
from hooks.use_auth import use_auth
from hooks.use_theme import use_theme

_CSS = """<style>
/* Sembunyikan sidebar di halaman auth */
[data-testid="stSidebar"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }

/* Kartu form */
.auth-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 20px;
    padding: 2.5rem 2rem;
}
.auth-title {
    font-size: 1.75rem;
    font-weight: 800;
    color: #F8F9FA;
    margin-bottom: 0.3rem;
}
.auth-sub {
    font-size: 0.875rem;
    color: #6B7280;
    margin-bottom: 1.75rem;
}
.auth-divider {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    color: #4B5563;
    font-size: 0.8rem;
    margin: 1.25rem 0;
}
.auth-divider::before,
.auth-divider::after {
    content: '';
    flex: 1;
    height: 1px;
    background: rgba(255,255,255,0.08);
}
.social-row {
    display: flex;
    gap: 0.75rem;
}
.social-btn {
    flex: 1;
    text-align: center;
    padding: 0.625rem;
    border-radius: 10px;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    color: #D1D5DB;
    font-size: 0.875rem;
    font-weight: 600;
}
</style>"""


def render() -> None:
    theme = use_theme()
    theme["apply_theme"]()
    render_toast()

    auth = use_auth()

    # Redirect jika sudah login
    if auth["is_logged_in"]:
        user_name = auth["user"].get("name", "User") if auth["user"] else "User"
        st.markdown("<br><br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.success("👋 Halo, " + user_name + "! Kamu sudah login.")
            if st.button("🏠 Ke Beranda", use_container_width=True, type="primary"):
                st.session_state["current_page"] = "Landing"
                st.rerun()
            if st.button("🚪 Keluar", use_container_width=True):
                auth["logout"]()
                st.rerun()
        return

    st.markdown(_CSS, unsafe_allow_html=True)

    if "auth_mode" not in st.session_state:
        st.session_state["auth_mode"] = "login"

    # Tengah: 3 kolom, pakai kolom tengah
    _, col, _ = st.columns([1, 2, 1])
    with col:
        # Brand kecil di atas
        st.markdown(
            '<div style="text-align:center;margin-bottom:1.5rem;">'
            '<span style="font-size:1.5rem;font-weight:800;'
            'background:linear-gradient(135deg,#7C3AED,#10B981);'
            '-webkit-background-clip:text;-webkit-text-fill-color:transparent;'
            'background-clip:text;">🎪 EventBot</span>'
            '</div>',
            unsafe_allow_html=True,
        )

        # st.markdown('<div class="auth-card">', unsafe_allow_html=True)

        if st.session_state["auth_mode"] == "login":
            _login_form(auth)
        else:
            _register_form(auth)

        st.markdown('</div>', unsafe_allow_html=True)

        # Tombol kembali ke beranda
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← Kembali ke Beranda", key="auth_back_home", use_container_width=True):
            st.session_state["current_page"] = "Landing"
            st.rerun()


def _login_form(auth: dict) -> None:
    st.markdown(
        '<div class="auth-title">Selamat Datang 👋</div>'
        '<div class="auth-sub">Masuk ke akun EventBot kamu</div>',
        unsafe_allow_html=True,
    )

    with st.form("login_form", clear_on_submit=False):
        email    = st.text_input("Email", placeholder="contoh@email.com", key="li_email")
        password = st.text_input("Password", type="password", placeholder="••••••••", key="li_pass")
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        submitted = st.form_submit_button("Masuk", use_container_width=True, type="primary")

        if submitted:
            if not email or not password:
                st.error("Email dan password wajib diisi.")
            else:
                with st.spinner("Memverifikasi..."):
                    ok, msg = auth["login"](email.strip(), password)
                if ok:
                    queue_toast(msg, "success")
                    st.session_state["current_page"] = "Landing"
                    st.rerun()
                else:
                    st.error("❌ " + msg)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<div style="text-align:center;font-size:0.875rem;color:#6B7280;">Belum punya akun?</div>',
        unsafe_allow_html=True,
    )
    if st.button("✨ Buat akun baru", key="go_register", use_container_width=True):
        st.session_state["auth_mode"] = "register"
        st.rerun()

    with st.expander("💡 Akun Demo"):
        st.markdown("""
| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@eventbot.com` | `admin123` |
| Peserta | `peserta@eventbot.com` | `peserta123` |
        """)


def _register_form(auth: dict) -> None:
    st.markdown(
        '<div class="auth-title">Buat Akun Baru 🚀</div>'
        '<div class="auth-sub">Bergabung dan temukan event seru!</div>',
        unsafe_allow_html=True,
    )

    with st.form("register_form", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            first_name = st.text_input("Nama Depan", placeholder="Budi", key="rg_first")
        with c2:
            last_name = st.text_input("Nama Belakang", placeholder="Santoso", key="rg_last")

        email     = st.text_input("Email", placeholder="contoh@email.com", key="rg_email")
        password  = st.text_input("Password", type="password", placeholder="Minimal 6 karakter", key="rg_pass")
        conf_pass = st.text_input("Konfirmasi Password", type="password", placeholder="Ulangi password", key="rg_conf")
        agree     = st.checkbox("Saya menyetujui syarat & ketentuan EventBot", key="rg_agree")

        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        submitted = st.form_submit_button("Buat Akun", use_container_width=True, type="primary")

        if submitted:
            full_name = (first_name.strip() + " " + last_name.strip()).strip()
            errs = []
            if not first_name:
                errs.append("Nama depan wajib diisi.")
            if not email or "@" not in email:
                errs.append("Format email tidak valid.")
            if not password or len(password) < 6:
                errs.append("Password minimal 6 karakter.")
            if password != conf_pass:
                errs.append("Konfirmasi password tidak cocok.")
            if not agree:
                errs.append("Harap setujui syarat & ketentuan.")
            if errs:
                for e in errs:
                    st.error("⚠️ " + e)
            else:
                with st.spinner("Membuat akun..."):
                    ok, msg = auth["register"](name=full_name, email=email.strip(), password=password)
                if ok:
                    queue_toast("Akun berhasil dibuat! Silakan login. 🎉", "success")
                    st.session_state["auth_mode"] = "login"
                    st.rerun()
                else:
                    st.error("❌ " + msg)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<div style="text-align:center;font-size:0.875rem;color:#6B7280;">Sudah punya akun?</div>',
        unsafe_allow_html=True,
    )
    if st.button("🔐 Masuk ke akun", key="go_login", use_container_width=True):
        st.session_state["auth_mode"] = "login"
        st.rerun()
