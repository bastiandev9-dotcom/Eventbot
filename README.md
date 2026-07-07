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

## 🛠 Teknologi

| Layer | Teknologi |
|-------|-----------|
| Backend | Python 3.10+, FastAPI, uvicorn |
| Frontend | Python 3.10+, Streamlit 1.35.0 |
| Database | PostgreSQL 14+ |
| Auth | JWT (PyJWT), bcrypt |
| NLP | Rule-based Regex (tanpa ML) |

---

## ✅ Prasyarat

Install semua software berikut sebelum mulai:

- [Python 3.10+](https://www.python.org/downloads/)
- [PostgreSQL 14+](https://www.postgresql.org/download/)

Cek instalasi:
```bash
python --version
psql --version
```

---

## 🗄 Setup Database

> Lakukan ini sekali setelah clone repository.

**1. Buat database:**
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

> **Windows:** Jika `psql` tidak dikenali, gunakan path lengkap:
> `"C:\Program Files\PostgreSQL\16\bin\psql.exe"`

---

## ⚙️ Setup Backend

```bash
# 1. Masuk ke folder backend
cd backend

# 2. Buat & aktifkan virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/macOS

# 3. Install dependencies
pip install -r requirements.txt
pip install fastapi uvicorn

# 4. Buat file .env dari template
copy .env.example .env         # Windows
# cp .env.example .env         # Linux/macOS
```

**Edit `backend/.env`** sesuai konfigurasi lokal:
```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=password_postgresql_kamu
DB_NAME=eventbot

APP_ENV=development
SECRET_KEY=isi-string-acak-minimal-32-karakter
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

> Untuk `DB_PASSWORD` dan kredensial lainnya, hubungi pemilik repository.

---

## 🎨 Setup Frontend

```bash
# 1. Masuk ke folder frontend (terminal baru)
cd frontend

# 2. Buat & aktifkan virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/macOS

# 3. Install dependencies
pip install -r requirements.txt
```

---

## 🚀 Menjalankan Aplikasi

Butuh **2 terminal** yang berjalan bersamaan.

**Terminal 1 — Backend:**
```bash
uvicorn backend.main:app --reload --port 8000
```

**Terminal 2 — Frontend:**
```bash
streamlit run frontend/app.py
```

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

## 🔧 Troubleshooting

| Masalah | Solusi |
|---------|--------|
| `psycopg2.OperationalError` | Pastikan PostgreSQL berjalan dan kredensial `.env` benar |
| Frontend tidak bisa konek backend | Pastikan backend sudah berjalan di port 8000 |
| `psycopg2` gagal install | Gunakan `pip install psycopg2-binary` |
| Port sudah dipakai | `netstat -ano \| findstr :8000` lalu `taskkill /PID <PID> /F` |

---

## 📄 Dokumentasi Lengkap

| File | Isi |
|------|-----|
| `docs/architecture.md` | Arsitektur sistem |
| `docs/api-docs.md` | Referensi semua endpoint API |
| `docs/chatbot-intents.md` | Intent, entity, dan pola regex chatbot |
| `docs/deployment.md` | Panduan deployment lengkap |

---

*Project akademik — Mata Kuliah Teori Bahasa dan Otomata*
