"""
Knowledge Base Page — EventBot
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
        '<h1 style="font-size:1.75rem;font-weight:800;color:#F8F9FA;margin:0 0 0.25rem;">📚 Knowledge Base</h1>'
        '<p style="color:#6B7280;font-size:0.9rem;margin:0;">Kelola FAQ, intent training data, dan response template</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3, tab4 = st.tabs(["❓ FAQ", "🎯 Intent & Contoh", "💬 Response Templates", "🔤 Regex Rules"])

    with tab1:
        _faq_tab(client)
    with tab2:
        _intents_tab(client)
    with tab3:
        _templates_tab(client)
    with tab4:
        _regex_tab()


def _faq_tab(client):
    col_s, col_a = st.columns([4, 1])
    with col_s:
        q = st.text_input("Cari FAQ", placeholder="🔍 Cari FAQ...", label_visibility="collapsed", key="faq_search")
    with col_a:
        if st.button("➕ Tambah", key="add_faq_btn", type="primary", use_container_width=True):
            st.session_state["faq_add_mode"] = True

    faqs = _fetch_faqs(client)
    if q:
        faqs = [f for f in faqs if q.lower() in f["question"].lower() or q.lower() in f["answer"].lower()]

    st.markdown(
        '<p style="color:#6B7280;font-size:0.8rem;margin:0.5rem 0;">' + str(len(faqs)) + ' FAQ ditemukan</p>',
        unsafe_allow_html=True,
    )

    if st.session_state.get("faq_add_mode"):
        with st.form("add_faq_form"):
            fq = st.text_input("Pertanyaan *")
            fa = st.text_area("Jawaban *", height=100)
            fc = st.text_input("Kategori (opsional)")
            c1, c2 = st.columns(2)
            with c1:
                if st.form_submit_button("💾 Simpan", type="primary", use_container_width=True):
                    if fq and fa:
                        try:
                            client._post("/knowledge-base/faq", {"question": fq, "answer": fa, "category": fc})
                            queue_toast("FAQ berhasil ditambahkan!", "success")
                        except Exception:
                            queue_toast("Gagal menambah FAQ.", "error")
                        st.session_state["faq_add_mode"] = False
                        st.rerun()
                    else:
                        st.error("Pertanyaan dan jawaban wajib diisi.")
            with c2:
                if st.form_submit_button("❌ Batal", use_container_width=True):
                    st.session_state["faq_add_mode"] = False
                    st.rerun()

    for i, faq in enumerate(faqs):
        fid = str(faq.get("id", i))
        with st.expander("❓ " + faq["question"]):
            st.markdown(
                '<div style="background:rgba(255,255,255,0.03);border-radius:10px;padding:1rem;'
                'color:#D1D5DB;font-size:0.9rem;line-height:1.6;">' + faq["answer"] + '</div>',
                unsafe_allow_html=True,
            )
            if faq.get("category"):
                st.caption("Kategori: " + faq["category"])
            if st.button("🗑️ Hapus", key="del_faq_" + fid):
                try:
                    client._delete("/knowledge-base/faq/" + fid)
                    queue_toast("FAQ dihapus.", "success")
                except Exception:
                    pass
                st.rerun()


def _intents_tab(client):
    st.caption("Intent adalah tujuan dari pesan user. Contoh kalimat digunakan untuk melatih chatbot.")
    intents = _fetch_intents(client)
    for intent_name, data in intents.items():
        with st.expander("🎯 " + intent_name):
            st.markdown("**Deskripsi:** " + data.get("description", "-"))
            st.markdown("**Contoh kalimat:**")
            for ex in data.get("examples", [])[:5]:
                st.markdown(
                    '<div style="background:rgba(124,58,237,0.06);border:1px solid rgba(124,58,237,0.15);'
                    'border-radius:8px;padding:0.4rem 0.75rem;margin:0.2rem 0;font-size:0.85rem;color:#D1D5DB;">'
                    '"' + ex + '"</div>',
                    unsafe_allow_html=True,
                )


def _templates_tab(client):
    st.caption("Template respons bot per intent. Gunakan {variable} untuk nilai dinamis.")
    templates = _fetch_templates(client)
    for key, tmpl in templates.items():
        with st.expander("💬 " + key):
            new_val = st.text_area("Template", value=tmpl, height=100,
                                    key="tmpl_" + key, label_visibility="collapsed")
            if st.button("💾 Simpan " + key, key="save_tmpl_" + key):
                try:
                    client._put("/knowledge-base/templates/" + key, {"template": new_val})
                    queue_toast("Template disimpan!", "success")
                    st.rerun()
                except Exception:
                    queue_toast("Gagal menyimpan.", "error")


def _regex_tab():
    st.caption("Regex rules untuk mengenali intent. Edit `backend/nlp/regex_rules.py` untuk perubahan permanen.")
    try:
        client = APIClient()
        intents = client.get_intents().get("data", {})
    except Exception:
        intents = {
            "sapaan":       "Halo, Hi, Assalamualaikum",
            "cari_event":   "Cari event teknologi, ada event apa",
            "daftar_tiket": "Daftar event, pesan tiket",
            "tanya_bantuan":"Bantuan, menu, fitur apa",
        }
    for intent, examples in intents.items():
        st.markdown(
            '<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);'
            'border-radius:10px;padding:0.875rem;margin-bottom:0.5rem;">'
            '<span style="font-family:monospace;color:#7C3AED;font-weight:700;">' + intent + '</span>'
            '<div style="margin-top:0.4rem;font-size:0.8rem;color:#6B7280;">Contoh: ' + str(examples) + '</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    st.info("💡 Untuk mengubah regex rules, edit `backend/nlp/regex_rules.py` dan restart backend.")


def _fetch_faqs(client):
    try:
        return client._get("/knowledge-base/faq").get("data", [])
    except Exception:
        return [
            {"id": "1", "question": "Bagaimana cara mendaftar event?",
             "answer": "Buka Event Explorer, pilih event, klik Daftar.", "category": "Event"},
            {"id": "2", "question": "Bisa batalkan pendaftaran?",
             "answer": "Ya, buka Profil Saya → Tiket Saya → klik Batalkan.", "category": "Tiket"},
        ]


def _fetch_intents(client):
    try:
        return client._get("/knowledge-base/intents").get("data", {})
    except Exception:
        return {
            "sapaan": {"description": "Salam pembuka dari user", "examples": ["Halo", "Hi", "Selamat pagi"]},
            "cari_event": {"description": "User ingin mencari event", "examples": ["Cari event teknologi", "Ada event apa?"]},
        }


def _fetch_templates(client):
    try:
        return client._get("/knowledge-base/templates").get("data", {})
    except Exception:
        return {
            "sapaan_response": "Halo! 👋 Saya EventBot, ada yang bisa saya bantu?",
            "fallback":        "Maaf, saya tidak mengerti. Ketik 'bantuan'.",
        }
