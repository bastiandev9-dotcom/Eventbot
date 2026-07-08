# 🎪 EventBot

**EventBot** adalah aplikasi web manajemen event berbasis chatbot NLP, dibangun sebagai proyek mata kuliah **Teori Bahasa dan Otomata**. Chatbot menggunakan *rule-based NLP* dengan **regular expression (regex)** sebagai implementasi langsung dari konsep finite automata dan formal language.

Pengguna dapat mencari event, melihat detail, membeli tiket, dan berinteraksi melalui chatbot dalam satu platform.

---

## ✨ Fitur Utama

| Pengguna | Admin |
|----------|-------|
| Cari & filter event | Buat, edit, hapus event |
| Chatbot NLP | Manajemen tiket & user |
| Beli tiket | Dashboard statistik |
| Riwayat registrasi | Knowledge base chatbot |

**Chatbot** mendukung: cari event, detail event, booking tiket, jadwal saya, profil, dan fallback ke knowledge base.

---

## 🏗 Arsitektur Sistem

```
┌─────────────────────────────────────────────────────────────────┐
│                        Browser (User)                           │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Streamlit Frontend (:8501)                      │
│                                                                  │
│  app.py  ──────────────────────────────────────────────────────┐│
│                                                                  ││
│  views/                    hooks/              utils/           ││
│  ├── Landing.py             ├── use_auth.py     ├── api_client  ││
│  ├── Event_Explorer.py      ├── use_events.py   ├── session_mgr ││
│  ├── Chatbot.py             ├── use_chat.py     ├── formatters  ││
│  ├── Manajemen_Event.py     └── use_theme.py    └── state_pers  ││
│  ├── Manajemen_Ticket.py                                        ││
│  ├── Manajemen_User.py      components/         styles/         ││
│  ├── Dashboard_admin.py     ├── event_card.py   ├── global.css  ││
│  ├── Knowledge_Base.py      ├── sidebar.py      ├── dark_theme  ││
│  ├── Profil_saya.py         ├── chat_bubble.py  ├── glassmorphi ││
│  └── Login_register.py      ├── data_table.py   └── animation  ││
│                             └── filter_panel.py                 ││
└──────────────────────────────┬──────────────────────────────────┘│
                               │ HTTP REST / WebSocket              │
                               ▼                                    │
┌─────────────────────────────────────────────────────────────────┐│
│                   FastAPI Backend (:8000)                        ││
│                                                                  ││
│  main.py ───────────────────────────────────────────────────┐   ││
│                                                              │   ││
│  api/v1/                    services/                        │   ││
│  ├── auth.py                ├── auth_service.py              │   ││
│  ├── events.py              ├── event_service.py             │   ││
│  ├── tickets.py             ├── ticket_service.py            │   ││
│  ├── registrations.py       ├── registration_service.py      │   ││
│  ├── chatbot.py             ├── chatbot_service.py           │   ││
│  ├── admin.py               ├── notification_service.py      │   ││
│  └── knowledge_base.py      └── recommendation_service.py    │   ││
│                                                              │   ││
│  models/                    nlp/                             │   ││
│  ├── event.py               ├── regex_rules.py               │   ││
│  ├── ticket.py              ├── response_templates.py        │   ││
│  ├── user.py                └── context_manager.py           │   ││
│  ├── registration.py                                         │   ││
│  ├── knowledge_base.py      config/                          │   ││
│  └── chat_history.py        ├── database.py (pool)           │   ││
│                             ├── settings.py                  │   ││
│  repositories/              └── security.py (JWT)            │   ││
│  ├── event_repository.py                                     │   ││
│  ├── user_repository.py     utils/                           │   ││
│  ├── ticket_repository.py   ├── validators.py                │   ││
│  └── registration_repo.py   ├── formatters.py                │   ││
│                             └── exceptions.py                │   ││
└──────────────────────────────┬───────────────────────────────┘   ││
                               │ psycopg2 (raw SQL)                 ││
                               ▼                                    ││
┌─────────────────────────────────────────────────────────────────┐││
│                    PostgreSQL (:5432)                            │││
│                                                                  │││
│  database/                                                       │││
│  ├── schema.sql      → tabel, enum, index                        │││
│  ├── functions.sql   → stored functions                          │││
│  ├── triggers.sql    → auto slug & updated_at                    │││
│  └── data.sql        → seed data lengkap                         │││
│                                                                  │││
│  Tabel:                                                          │││
│  users · events · tickets · registrations                        │││
│  categories · event_categories · chat_sessions                   │││
│  chat_messages · knowledge_base · system_settings                │││
└──────────────────────────────────────────────────────────────────┘││
                                                                    ││
└───────────────────────────────────────────────────────────────────┘│
└────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Struktur Project

```
eventbot/
├── backend/                         # FastAPI REST API
│   ├── main.py                      # Entry point + CORS + static files
│   ├── .env                         # Konfigurasi environment (tidak di-commit)
│   ├── .env.example                 # Template konfigurasi
│   ├── requirements.txt             # Dependensi Python backend
│   │
│   ├── api/
│   │   ├── v1/
│   │   │   ├── auth.py              # Endpoint: register, login, logout, me
│   │   │   ├── events.py            # Endpoint: CRUD event, search, trending
│   │   │   ├── tickets.py           # Endpoint: CRUD tiket per event
│   │   │   ├── registrations.py     # Endpoint: booking, riwayat, konfirmasi
│   │   │   ├── chatbot.py           # Endpoint: kirim pesan, history, intents
│   │   │   ├── admin.py             # Endpoint: statistik, manajemen user
│   │   │   └── knowledge_base.py    # Endpoint: CRUD knowledge base chatbot
│   │   ├── websocket.py             # WebSocket chat real-time
│   │   └── deps.py                  # Dependency: validasi JWT token
│   │
│   ├── services/
│   │   ├── auth_service.py          # Logic: login, register, JWT
│   │   ├── event_service.py         # Logic: CRUD & pencarian event
│   │   ├── ticket_service.py        # Logic: manajemen tiket
│   │   ├── registration_service.py  # Logic: booking & pembayaran
│   │   ├── chatbot_service.py       # Logic: orkestrasi NLP + database
│   │   ├── notification_service.py  # Logic: notifikasi email/sistem
│   │   └── recommendation_service.py # Logic: trending & rekomendasi event
│   │
│   ├── models/
│   │   ├── event.py                 # Query SQL tabel events
│   │   ├── ticket.py                # Query SQL tabel tickets
│   │   ├── user.py                  # Query SQL tabel users
│   │   ├── registration.py          # Query SQL tabel registrations
│   │   ├── category.py              # Query SQL tabel categories
│   │   ├── chat_history.py          # Query SQL tabel chat_sessions & messages
│   │   ├── knowledge_base.py        # Query SQL tabel knowledge_base
│   │   └── system_settings.py       # Query SQL tabel system_settings
│   │
│   ├── nlp/
│   │   ├── regex_rules.py           # Pola regex intent & entity extraction
│   │   ├── response_templates.py    # Builder respons chatbot (teks + quick replies)
│   │   └── context_manager.py       # Manajemen state percakapan per sesi
│   │
│   ├── repositories/
│   │   ├── base_repository.py       # CRUD generik (parent class)
│   │   ├── event_repository.py      # Query kompleks event
│   │   ├── user_repository.py       # Query kompleks user
│   │   ├── ticket_repository.py     # Query kompleks tiket
│   │   └── registration_repository.py # Query kompleks registrasi
│   │
│   ├── config/
│   │   ├── database.py              # Connection pool psycopg2 (singleton)
│   │   ├── settings.py              # Baca environment variable
│   │   └── security.py             # Generate & verify JWT token
│   │
│   ├── utils/
│   │   ├── validators.py            # Validasi input (email, password, dll)
│   │   ├── formatters.py            # Format data (tanggal, harga, dll)
│   │   └── exceptions.py           # Custom exception handler
│   │
│   ├── uploads/
│   │   └── events/                  # File gambar event yang diupload
│   │
│   └── tests/
│       ├── conftest.py              # Konfigurasi pytest & fixture
│       ├── test_auth.py             # Test endpoint autentikasi
│       ├── test_events.py           # Test endpoint event
│       ├── test_chatbot.py          # Test NLP & chatbot
│       └── test_backend.py          # Test integrasi backend
│
├── frontend/                        # Streamlit UI
│   ├── app.py                       # Entry point + routing SPA + proteksi halaman
│   ├── requirements.txt             # Dependensi Python frontend
│   │
│   ├── views/
│   │   ├── Landing.py               # Halaman beranda & hero section
│   │   ├── Login_register.py        # Form login & registrasi akun
│   │   ├── Event_Explorer.py        # Jelajahi & filter event
│   │   ├── Chatbot.py               # Antarmuka chatbot NLP
│   │   ├── Profil_saya.py           # Profil user & riwayat tiket
│   │   ├── Manajemen_Event.py       # Admin: CRUD event
│   │   ├── Manajemen_Ticket.py      # Admin: CRUD tiket per event
│   │   ├── Manajemen_User.py        # Admin: kelola akun user
│   │   ├── Dashboard_admin.py       # Admin: statistik & grafik
│   │   ├── Knowledge_Base.py        # Admin: kelola knowledge base chatbot
│   │   ├── Pengaturan.py            # Admin: konfigurasi sistem
│   │   └── About.py                 # Halaman tentang aplikasi
│   │
│   ├── components/
│   │   ├── navbar.py                # Navigasi atas
│   │   ├── sidebar.py               # Sidebar menu berbasis role
│   │   ├── auth_form.py             # Form login & register
│   │   ├── hero_section.py          # Banner utama halaman landing
│   │   ├── event_card.py            # Kartu tampilan event (grid)
│   │   ├── ticket_card.py           # Kartu tampilan tiket
│   │   ├── buy_ticket_modal.py      # Modal pembelian tiket
│   │   ├── chat_bubble.py           # Gelembung pesan chatbot
│   │   ├── quick_reply.py           # Tombol quick reply chatbot
│   │   ├── filter_panel.py          # Panel filter pencarian event
│   │   ├── data_table.py            # Tabel data dengan aksi edit/hapus
│   │   ├── metric_card.py           # Kartu statistik dashboard
│   │   ├── toast.py                 # Notifikasi toast (sukses/error)
│   │   └── footer.py                # Footer halaman
│   │
│   ├── hooks/
│   │   ├── use_auth.py              # State & logic autentikasi
│   │   ├── use_events.py            # State & logic data event (+ cache TTL)
│   │   ├── use_chat.py              # State & logic percakapan chatbot
│   │   └── use_theme.py             # Manajemen tema tampilan
│   │
│   ├── utils/
│   │   ├── api_client.py            # HTTP client ke backend (wrapper requests)
│   │   ├── session_manager.py       # Wrapper st.session_state (auth state)
│   │   ├── state_persistence.py     # Simpan state ke file lokal (JSON)
│   │   └── formatters.py            # Format tanggal, harga, status badge
│   │
│   ├── styles/
│   │   ├── theme_manager.py         # Inject CSS ke halaman Streamlit
│   │   ├── global.css               # Styling global
│   │   ├── dark_theme.css           # Tema gelap
│   │   ├── glassmorphism.css        # Efek kaca / blur
│   │   └── animation.css            # Animasi transisi
│   │
│   └── .streamlit/
│       └── config.toml              # Konfigurasi Streamlit (tema, port, dll)
│
├── database/
│   ├── schema.sql                   # DDL: tabel, enum, index
│   ├── functions.sql                # Stored functions PostgreSQL
│   ├── triggers.sql                 # Trigger auto-update slug & timestamp
│   └── data.sql                     # Data lengkap (export pg_dump)
│
├── docs/
│   ├── architecture.md              # Arsitektur sistem dan alur data
│   ├── api-docs.md                  # Referensi semua endpoint API
│   ├── chatbot-intents.md           # Intent, entity, dan pola regex chatbot
│   └── deployment.md                # Panduan deployment lengkap
│
├── .gitignore                       # File yang tidak di-push ke GitHub
└── README.md                        # Dokumentasi utama project
```

---

## 💬 Contoh Penggunaan Chatbot

Berikut contoh kalimat yang bisa diketik langsung ke chatbot:

| Tujuan | Contoh Kalimat |
|--------|---------------|
| Sapa bot | `Halo`, `Selamat pagi`, `Apa kabar?` |
| Minta bantuan | `Bantuan`, `Kamu bisa apa?`, `Menu` |
| Cari event | `Ada event teknologi di Jakarta?` |
| Cari event gratis | `Event gratis bulan Agustus` |
| Cari berdasarkan kategori | `Event musik minggu ini`, `Seminar bisnis online` |
| Detail event | `Berapa harga tiketnya?`, `Jam berapa mulainya?` |
| Booking tiket | `Mau beli tiket`, `Cara pesan tiket?` |
| Lihat jadwal | `Tiket saya`, `Riwayat pemesanan` |
| Lihat profil | `Profil saya`, `Info akun` |
| Keluar | `Terima kasih`, `Bye` |

---

## 🛠 Teknologi

### Backend
| Teknologi | Versi | Kegunaan |
|-----------|-------|----------|
| Python | 3.10+ | Bahasa pemrograman utama |
| FastAPI | latest | REST API framework |
| uvicorn | latest | ASGI server |
| psycopg2-binary | ≥2.9.9 | Driver koneksi PostgreSQL |
| PyJWT | ≥2.8.0 | JSON Web Token (autentikasi) |
| bcrypt | ≥4.1.0 | Hash & verifikasi password |
| pydantic | ≥2.5.0 | Validasi request & response |
| python-dotenv | ≥1.0.0 | Manajemen environment variable |

### Frontend
| Teknologi | Versi | Kegunaan |
|-----------|-------|----------|
| Python | 3.10+ | Bahasa pemrograman utama |
| Streamlit | 1.35.0 | Framework UI web |
| requests | 2.32.3 | HTTP client ke backend API |
| pandas | 2.2.2 | Manipulasi data tabel |
| plotly | 5.22.0 | Visualisasi grafik dashboard |
| python-dotenv | 1.0.1 | Manajemen environment variable |

### Database
| Teknologi | Versi | Kegunaan |
|-----------|-------|----------|
| PostgreSQL | 14+ | Database relasional utama |
| psql | 14+ | CLI untuk menjalankan file SQL |

### NLP (Chatbot)
| Pendekatan | Keterangan |
|------------|------------|
| Rule-based Regex | Deteksi intent via pattern matching (tanpa ML) |
| Entity Extraction | Ekstraksi lokasi, tanggal, kategori, harga dari teks |
| Context Manager | Menyimpan state percakapan per sesi |
| Knowledge Base | Fallback jawaban dari database jika intent tidak dikenali |

---

## ✅ Prasyarat

Install semua software berikut sebelum mulai:

- [Python 3.10+](https://www.python.org/downloads/)
- [PostgreSQL 14+](https://www.postgresql.org/download/)

Cek instalasi:
```bash
python --version   # minimal 3.10.x
psql --version     # minimal 14.x
```

---

## 🗄 Setup Database

> Lakukan **sekali** setelah clone. Semua perintah dijalankan dari folder root project (`eventbot/`).

**1. Buat database baru:**
```bash
psql -U postgres -c "CREATE DATABASE eventbot;"
```

**2. Import schema + data:**
```bash
psql -U postgres -d eventbot -f database/schema.sql
psql -U postgres -d eventbot -f database/functions.sql
psql -U postgres -d eventbot -f database/triggers.sql
psql -U postgres -d eventbot -f database/data.sql
```

> **⚠️ Windows — jika `psql` tidak dikenali di terminal:**
> Tambahkan PostgreSQL ke PATH, atau gunakan path lengkap:
> ```bash
> "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -c "CREATE DATABASE eventbot;"
> ```
> Sesuaikan angka `16` dengan versi PostgreSQL yang terinstall.

Jika berhasil, tidak ada pesan error dan prompt kembali ke terminal.

---

## ⚙️ Setup Backend

> Semua perintah dijalankan dari folder **`eventbot/backend/`**.

```bash
# 1. Masuk ke folder backend
cd backend

# 2. Buat virtual environment
python -m venv venv

# 3. Aktifkan virtual environment
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux / macOS

# Jika berhasil, terminal akan menampilkan (venv) di awal baris

# 4. Install semua dependencies
pip install -r requirements.txt
pip install fastapi uvicorn

# 5. Buat file konfigurasi dari template
copy .env.example .env       # Windows
# cp .env.example .env       # Linux / macOS
```

**6. Edit file `backend/.env`** — sesuaikan dengan konfigurasi PostgreSQL lokal:

```env
# Sesuaikan dengan kredensial PostgreSQL kamu
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=password_postgresql_kamu   # ← ganti ini
DB_NAME=eventbot

APP_ENV=development
SECRET_KEY=bebas-isi-string-acak-asal-minimal-32-karakter
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

> Untuk nilai `DB_PASSWORD` yang benar, hubungi pemilik repository.

---

## 🎨 Setup Frontend

> Buka **terminal baru** (jangan tutup terminal backend). Jalankan dari folder **`eventbot/frontend/`**.

```bash
# 1. Dari root project, masuk ke folder frontend
cd frontend

# 2. Buat virtual environment
python -m venv venv

# 3. Aktifkan virtual environment
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux / macOS

# 4. Install semua dependencies
pip install -r requirements.txt
```

---

## 🚀 Menjalankan Aplikasi

Butuh **2 terminal** yang berjalan bersamaan. Pastikan virtual environment sudah aktif di masing-masing terminal.

**Terminal 1 — Backend** (dari folder root `eventbot/`):
```bash
uvicorn backend.main:app --reload --port 8000
```
Tunggu hingga muncul: `Application startup complete.`

**Terminal 2 — Frontend** (dari folder root `eventbot/`):
```bash
streamlit run frontend/app.py
```
Browser akan otomatis terbuka. Jika tidak, buka manual:

| Service | URL |
|---------|-----|
| Frontend | http://localhost:8501 |
| Backend API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |

---

## 👤 Akun Default

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@eventbot.com | admin123 |

> Akun participant bisa dibuat melalui halaman **Login / Daftar**.

---

## ☁️ Deploy ke Cloud (Production)

EventBot bisa di-deploy ke cloud untuk diakses dari internet:

### Panduan Deploy (Pilih salah satu):

| Guide | Untuk Siapa | Waktu |
|-------|-------------|-------|
| **[QUICK_DEPLOY.md](QUICK_DEPLOY.md)** | Yang ingin deploy cepat (5-10 menit) | ⚡ Quick |
| **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** | Yang ingin pemahaman lengkap + screenshot | 📚 Detail |
| **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** | Quality assurance & testing | ✅ QA |

### Stack Deployment Rekomendasi:
- **Database**: [Neon](https://neon.tech) (PostgreSQL cloud gratis)
- **Backend**: [Railway](https://railway.app) (FastAPI hosting)
- **Frontend**: [Streamlit Cloud](https://share.streamlit.io) (gratis untuk 1 app)

Semua menggunakan **free tier**, cukup untuk demo & proyek kuliah! 🎓

**Quick Start**:
```bash
# 1. Push ke GitHub
git add .
git commit -m "Ready to deploy"
git push origin main

# 2. Ikuti QUICK_DEPLOY.md step by step
```

Setelah deploy, aplikasi akan live di: `https://eventbot.streamlit.app`

---

## 🔧 Troubleshooting

| Masalah | Solusi |
|---------|--------|
| `psycopg2.OperationalError` | PostgreSQL belum berjalan, atau `DB_PASSWORD` di `.env` salah |
| `psql` tidak dikenali | Tambahkan `C:\Program Files\PostgreSQL\16\bin` ke PATH Windows |
| Frontend tidak bisa konek backend | Pastikan Terminal 1 (backend) sudah berjalan sebelum membuka frontend |
| `psycopg2` gagal install | Ganti dengan `pip install psycopg2-binary` |
| Port 8000 sudah dipakai | Jalankan `netstat -ano \| findstr :8000` lalu `taskkill /PID <PID> /F` |
| `(venv)` tidak muncul di terminal | Virtual environment belum aktif, jalankan ulang `venv\Scripts\activate` |

---

## 📄 Dokumentasi Lengkap

| File | Isi |
|------|-----|
| `docs/architecture.md` | Arsitektur sistem dan alur data |
| `docs/api-docs.md` | Referensi semua endpoint API |
| `docs/chatbot-intents.md` | Intent, entity, dan pola regex chatbot |
| `docs/deployment.md` | Panduan deployment lengkap |

---

*Project akademik — Mata Kuliah Teori Bahasa dan Otomata*
