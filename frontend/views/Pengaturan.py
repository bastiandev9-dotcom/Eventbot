"""
Pengaturan Chatbot Page — EventBot
"""

import streamlit as st
from components.toast import render_toast, queue_toast
from hooks.use_auth import use_auth
from hooks.use_theme import use_theme
from utils.api_client import APIClient
from utils.session_manager import SessionManager


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
        '<h1 style="font-size:1.75rem;font-weight:800;color:#F8F9FA;margin:0 0 0.25rem;">⚙️ Pengaturan Chatbot</h1>'
        '<p style="color:#6B7280;font-size:0.9rem;margin:0;">Konfigurasi personality, pesan, dan perilaku EventBot</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    settings = _fetch_settings(client)
    tab1, tab2, tab3, tab4 = st.tabs(["🤖 Personality", "💬 Pesan Bot", "⚡ Perilaku", "🔧 System"])

    with tab1:
        _personality_tab(settings, client)
    with tab2:
        _messages_tab(settings, client)
    with tab3:
        _behavior_tab(settings, client)
    with tab4:
        _system_tab(client)


def _personality_tab(settings, client):
    with st.form("personality_form"):
        c1, c2 = st.columns(2)
        with c1:
            bot_name  = st.text_input("Nama Bot", value=settings.get("bot_name","EventBot"))
            bot_emoji = st.text_input("Emoji/Icon", value=settings.get("bot_emoji","🤖"))
        with c2:
            options = ["Profesional & Formal","Ramah & Casual","Energik & Fun","Netral"]
            idx = options.index(settings.get("personality","Ramah & Casual")) if settings.get("personality") in options else 1
            personality = st.selectbox("Kepribadian", options, index=idx)
            language    = st.selectbox("Bahasa Utama", ["Bahasa Indonesia","English","Bilingual (ID/EN)"])
        tagline = st.text_input("Tagline", value=settings.get("tagline","Asisten cerdas untuk manajemen event"))
        if st.form_submit_button("💾 Simpan Personality", type="primary", use_container_width=True):
            _save(client, {"bot_name": bot_name, "bot_emoji": bot_emoji,
                           "personality": personality, "language": language, "tagline": tagline})

    # Preview
    st.markdown("---")
    st.markdown("**Preview:**")
    bot_name_cur  = settings.get("bot_name","EventBot")
    bot_emoji_cur = settings.get("bot_emoji","🤖")
    tagline_cur   = settings.get("tagline","asisten cerdas untuk manajemen event")
    st.markdown(
        '<div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);'
        'border-radius:14px;padding:1.25rem;max-width:400px;">'
        '<div style="display:flex;align-items:center;gap:0.625rem;margin-bottom:1rem;">'
        '<div style="width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#7C3AED,#10B981);'
        'display:flex;align-items:center;justify-content:center;font-size:1rem;">' + bot_emoji_cur + '</div>'
        '<div><div style="font-weight:700;color:#F8F9FA;font-size:0.875rem;">' + bot_name_cur + '</div>'
        '<div style="font-size:0.7rem;color:#10B981;">● Online</div></div></div>'
        '<div style="background:rgba(255,255,255,0.06);border-radius:4px 14px 14px 14px;'
        'padding:0.75rem;font-size:0.875rem;color:#F8F9FA;">'
        'Halo! 👋 Saya <strong>' + bot_name_cur + '</strong>, ' + tagline_cur + '. Ada yang bisa saya bantu?'
        '</div></div>',
        unsafe_allow_html=True,
    )


def _messages_tab(settings, client):
    with st.form("messages_form"):
        welcome  = st.text_area("Pesan Selamat Datang",
                                 value=settings.get("welcome_message","Halo! 👋 Saya EventBot, ada yang bisa saya bantu?"),
                                 height=100)
        farewell = st.text_area("Pesan Perpisahan",
                                 value=settings.get("farewell_message","Terima kasih! Sampai jumpa! 👋"),
                                 height=80)
        fallback = st.text_area("Pesan Fallback",
                                 value=settings.get("fallback_message","Maaf, saya belum mengerti. Ketik 'bantuan'."),
                                 height=80)
        error    = st.text_area("Pesan Error",
                                 value=settings.get("error_message","Terjadi kesalahan. Coba lagi!"),
                                 height=80)
        qr_raw   = st.text_input("Quick Replies Default (pisah koma)",
                                  value=", ".join(settings.get("default_quick_replies",
                                                               ["Ada event apa?","Event gratis","Bantuan"])))
        if st.form_submit_button("💾 Simpan Pesan", type="primary", use_container_width=True):
            qr_list = [r.strip() for r in qr_raw.split(",") if r.strip()]
            _save(client, {"welcome_message": welcome, "farewell_message": farewell,
                           "fallback_message": fallback, "error_message": error,
                           "default_quick_replies": qr_list})


def _behavior_tab(settings, client):
    with st.form("behavior_form"):
        c1, c2 = st.columns(2)
        with c1:
            max_hist    = st.number_input("Maks. riwayat chat", min_value=10, max_value=200,
                                          value=int(settings.get("max_history",50)), step=10)
            typing_del  = st.slider("Delay typing indicator (ms)", 200, 2000,
                                    int(settings.get("typing_delay_ms",800)), 100)
        with c2:
            en_suggest  = st.checkbox("Aktifkan suggested prompts",    value=settings.get("enable_suggestions",True))
            en_cards    = st.checkbox("Tampilkan event cards di chat", value=settings.get("enable_event_cards",True))
            en_typing   = st.checkbox("Animasi mengetik",              value=settings.get("enable_typing_animation",True))
        max_ev = st.slider("Maks. event cards per respons", 1, 10, int(settings.get("max_events_in_chat",3)))
        if st.form_submit_button("💾 Simpan Perilaku", type="primary", use_container_width=True):
            _save(client, {"max_history": int(max_hist), "typing_delay_ms": int(typing_del),
                           "enable_suggestions": en_suggest, "enable_event_cards": en_cards,
                           "enable_typing_animation": en_typing, "max_events_in_chat": int(max_ev)})


def _system_tab(client):
    st.markdown("**Status Sistem**")
    from utils.api_client import APIClient as AC
    is_online = AC.health_check()
    c1, c2 = st.columns(2)
    with c1:
        if is_online:
            st.success("✅ Backend: Online")
        else:
            st.error("❌ Backend: Offline")
    with c2:
        if st.button("🔄 Refresh Status", key="health_refresh"):
            st.rerun()

    st.markdown("---")
    st.markdown("**Informasi Versi**")
    st.markdown("""
| Komponen | Versi |
|----------|-------|
| Frontend (Streamlit) | 1.0.0 |
| Backend (FastAPI) | 1.0.0 |
| Python | 3.12+ |
    """)
    st.markdown("---")
    if st.button("🗑️ Hapus Semua Cache", key="clear_cache"):
        for k in [k for k in st.session_state if k.startswith(("events_","event_detail_"))]:
            del st.session_state[k]
        queue_toast("Cache berhasil dihapus!", "success")
        st.rerun()


def _fetch_settings(client):
    try:
        return client._get("/admin/settings").get("data", {})
    except Exception:
        return {
            "bot_name": "EventBot", "bot_emoji": "🤖", "personality": "Ramah & Casual",
            "tagline": "Asisten cerdas untuk manajemen event",
            "welcome_message": "Halo! 👋 Saya EventBot, ada yang bisa saya bantu?",
            "fallback_message": "Maaf, saya belum mengerti. Ketik 'bantuan'.",
            "farewell_message": "Terima kasih! Sampai jumpa! 👋",
            "error_message": "Terjadi kesalahan. Coba lagi!",
            "default_quick_replies": ["Ada event apa?","Event gratis","Bantuan"],
            "max_history": 50, "typing_delay_ms": 800, "max_events_in_chat": 3,
            "enable_suggestions": True, "enable_event_cards": True, "enable_typing_animation": True,
        }


def _save(client, payload):
    try:
        client._put("/admin/settings", payload)
        queue_toast("Pengaturan berhasil disimpan!", "success")
        st.rerun()
    except Exception as e:
        queue_toast("Gagal menyimpan: " + str(e), "error")
