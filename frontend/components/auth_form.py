"""
Auth Form Component
===================
Formulir login dan registrasi dengan glassmorphism style.
"""

import streamlit as st
from typing import Callable, Optional, Tuple


def render_login_form(
    on_submit: Callable[[str, str], Tuple[bool, str]],
    key: str = "login",
    show_register_link: bool = True,
) -> None:
    """
    Render form login.

    Args:
        on_submit: Callback(email, password) -> (success, message)
        key: Key prefix Streamlit
        show_register_link: Tampilkan link ke halaman registrasi
    """
    st.markdown("""
    <div style="
        max-width: 420px;
        margin: 0 auto;
        background: rgba(255,255,255,0.05);
        backdrop-filter: blur(30px);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 24px;
        padding: 2.5rem;
        box-shadow: 0 25px 50px rgba(0,0,0,0.4);
        animation: fadeInUp 0.4s ease forwards;
    ">
        <div style="text-align:center; margin-bottom:2rem;">
            <div style="font-size:2.5rem; margin-bottom:0.5rem;">🎪</div>
            <h2 style="
                font-size:1.5rem; font-weight:800; color:#F8F9FA;
                margin:0 0 0.25rem;
            ">Selamat Datang!</h2>
            <p style="font-size:0.875rem; color:#6B7280; margin:0;">
                Masuk ke akun EventBot kamu
            </p>
        </div>
    """, unsafe_allow_html=True)

    with st.form(key=f"form_{key}_login", clear_on_submit=False):
        email = st.text_input(
            "Email",
            placeholder="contoh@email.com",
            key=f"{key}_email",
        )
        password = st.text_input(
            "Password",
            type="password",
            placeholder="••••••••",
            key=f"{key}_password",
        )

        # Spacer
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

        submitted = st.form_submit_button(
            "🔐 Masuk",
            use_container_width=True,
            type="primary",
        )

        if submitted:
            if not email or not password:
                st.error("⚠️ Email dan password wajib diisi.")
            else:
                with st.spinner("Memverifikasi..."):
                    success, message = on_submit(email.strip(), password)
                if success:
                    st.success(f"✅ {message}")
                    st.balloons()
                    st.rerun()
                else:
                    st.error(f"❌ {message}")

    if show_register_link:
        st.markdown("""
        <div style="text-align:center; margin-top:1.5rem;">
            <span style="font-size:0.875rem; color:#6B7280;">Belum punya akun?</span>
        </div>
        """, unsafe_allow_html=True)
        if st.button("✨ Daftar sekarang →", key=f"{key}_to_register", use_container_width=True):
            st.session_state["auth_tab"] = "register"
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def render_register_form(
    on_submit: Callable[..., Tuple[bool, str]],
    key: str = "register",
    show_login_link: bool = True,
) -> None:
    """
    Render form registrasi.

    Args:
        on_submit: Callback(name, email, password, role, phone, bio) -> (success, message)
        key: Key prefix Streamlit
        show_login_link: Tampilkan link ke halaman login
    """
    st.markdown("""
    <div style="
        max-width: 460px;
        margin: 0 auto;
        background: rgba(255,255,255,0.05);
        backdrop-filter: blur(30px);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 24px;
        padding: 2.5rem;
        box-shadow: 0 25px 50px rgba(0,0,0,0.4);
        animation: fadeInUp 0.4s ease forwards;
    ">
        <div style="text-align:center; margin-bottom:2rem;">
            <div style="font-size:2.5rem; margin-bottom:0.5rem;">🚀</div>
            <h2 style="
                font-size:1.5rem; font-weight:800; color:#F8F9FA;
                margin:0 0 0.25rem;
            ">Buat Akun Baru</h2>
            <p style="font-size:0.875rem; color:#6B7280; margin:0;">
                Bergabung dan temukan event seru!
            </p>
        </div>
    """, unsafe_allow_html=True)

    with st.form(key=f"form_{key}_register", clear_on_submit=False):
        # Nama lengkap
        name = st.text_input(
            "Nama Lengkap",
            placeholder="Nama lengkap kamu",
            key=f"{key}_name",
        )

        # Email
        email = st.text_input(
            "Email",
            placeholder="contoh@email.com",
            key=f"{key}_email",
        )

        # Password
        col_pass1, col_pass2 = st.columns(2)
        with col_pass1:
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Min. 6 karakter",
                key=f"{key}_password",
            )
        with col_pass2:
            confirm_pass = st.text_input(
                "Konfirmasi Password",
                type="password",
                placeholder="Ulangi password",
                key=f"{key}_confirm_pass",
            )

        # Nomor HP (opsional)
        phone = st.text_input(
            "Nomor HP (opsional)",
            placeholder="08xxxxxxxxxx",
            key=f"{key}_phone",
        )

        # Role
        role_options = {
            "Peserta (Participant)": "participant",
        }
        role_label = st.selectbox(
            "Daftar sebagai",
            options=list(role_options.keys()),
            key=f"{key}_role",
        )
        role = role_options[role_label]

        # Syarat & ketentuan
        agree = st.checkbox(
            "Saya menyetujui syarat & ketentuan EventBot",
            key=f"{key}_agree",
        )

        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

        submitted = st.form_submit_button(
            "🚀 Daftar Sekarang",
            use_container_width=True,
            type="primary",
        )

        if submitted:
            # Validasi
            errors = []
            if not name or len(name.strip()) < 2:
                errors.append("Nama minimal 2 karakter.")
            if not email or "@" not in email:
                errors.append("Format email tidak valid.")
            if not password or len(password) < 6:
                errors.append("Password minimal 6 karakter.")
            if password != confirm_pass:
                errors.append("Konfirmasi password tidak cocok.")
            if not agree:
                errors.append("Harap setujui syarat & ketentuan.")

            if errors:
                for err in errors:
                    st.error(f"⚠️ {err}")
            else:
                with st.spinner("Membuat akun..."):
                    success, message = on_submit(
                        name=name.strip(),
                        email=email.strip(),
                        password=password,
                        role=role,
                        phone=phone.strip() if phone else None,
                    )
                if success:
                    st.success(f"✅ {message}")
                    st.info("Silakan login dengan akun baru Anda.")
                    st.session_state["auth_tab"] = "login"
                    st.rerun()
                else:
                    st.error(f"❌ {message}")

    if show_login_link:
        st.markdown("""
        <div style="text-align:center; margin-top:1.5rem;">
            <span style="font-size:0.875rem; color:#6B7280;">Sudah punya akun?</span>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🔐 Masuk sekarang →", key=f"{key}_to_login", use_container_width=True):
            st.session_state["auth_tab"] = "login"
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def render_change_password_form(
    on_submit: Callable[[str, str], Tuple[bool, str]],
    key: str = "change_pass",
) -> None:
    """
    Render form ganti password.

    Args:
        on_submit: Callback(old_password, new_password) -> (success, message)
    """
    with st.form(key=f"form_{key}", clear_on_submit=True):
        st.markdown("**🔒 Ganti Password**")

        old_pass = st.text_input(
            "Password Lama",
            type="password",
            placeholder="••••••••",
            key=f"{key}_old",
        )
        new_pass = st.text_input(
            "Password Baru",
            type="password",
            placeholder="Min. 6 karakter",
            key=f"{key}_new",
        )
        confirm_new = st.text_input(
            "Konfirmasi Password Baru",
            type="password",
            placeholder="Ulangi password baru",
            key=f"{key}_confirm",
        )

        submitted = st.form_submit_button(
            "💾 Simpan Password",
            use_container_width=True,
            type="primary",
        )

        if submitted:
            if not old_pass or not new_pass:
                st.error("Semua field wajib diisi.")
            elif len(new_pass) < 6:
                st.error("Password baru minimal 6 karakter.")
            elif new_pass != confirm_new:
                st.error("Konfirmasi password tidak cocok.")
            else:
                with st.spinner("Menyimpan..."):
                    success, message = on_submit(old_pass, new_pass)
                if success:
                    st.success(f"✅ {message}")
                else:
                    st.error(f"❌ {message}")
