# Deployment Guide — EventBot

Panduan ini menjelaskan cara menyiapkan dan menjalankan EventBot di lingkungan lokal (development) maupun server (production).

---

## Daftar Isi

- [Prasyarat](#prasyarat)
- [Struktur Port](#struktur-port)
- [Setup Lokal (Development)](#setup-lokal-development)
  - [1. Clone & Persiapan](#1-clone--persiapan)
  - [2. Setup Database](#2-setup-database)
  - [3. Konfigurasi Environment](#3-konfigurasi-environment)
  - [4. Jalankan Backend](#4-jalankan-backend)
  - [5. Jalankan Frontend](#5-jalankan-frontend)
- [Verifikasi Instalasi](#verifikasi-instalasi)
- [Environment Variables](#environment-variables)
- [Perintah Berguna](#perintah-berguna)
- [Troubleshooting](#troubleshooting)

---

## Prasyarat

| Software   | Versi Minimum | Keterangan                      |
|------------|---------------|---------------------------------|
| Python     | 3.10+         | Wajib untuk backend dan frontend |
| PostgreSQL | 14+           | Database utama                  |
| pip        | 23+           | Package manager Python          |
| Git        | 2.x           | Version control                 |

---

## Struktur Port

| Service    | Port Default | URL                        |
|------------|-------------|----------------------------|
| Backend    | 8000        | http://localhost:8000      |
| Frontend   | 8501        | http://localhost:8501      |
| PostgreSQL | 5432        | localhost:5432             |
| API Docs   | 8000        | http://localhost:8000/docs |

---

## Setup Lokal (Development)

### 1. Clone & Persiapan

```bash
git clone <repo-url>
cd eventbot
```

**Setup virtual environment backend:**

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
```

**Setup virtual environment frontend (terminal terpisah):**

```bash
cd frontend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
```

---

### 2. Setup Database

**Buat database di PostgreSQL:**

```sql
-- Masuk ke psql
psql -U postgres

-- Buat database
CREATE DATABASE eventbot;
\q
```

**Jalankan schema, functions, dan triggers:**

```bash
psql -U postgres -d eventbot -f database/schema.sql
psql -U postgres -d eventbot -f database/functions.sql
psql -U postgres -d eventbot -f database/triggers.sql
```

> **Catatan:** File `seed_data.sql` sudah tidak ada di project ini. Database yang sudah memiliki data nyata tidak perlu di-seed ulang. Jika setup dari awal, buat data admin dan kategori awal langsung via psql atau endpoint `/auth/register`.

---

### 3. Konfigurasi Environment

Salin file contoh dan isi sesuai environment lokal:

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env`:

```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password_here
DB_NAME=eventbot

# App
APP_ENV=development
SECRET_KEY=ganti-dengan-string-acak-minimal-32-karakter

# JWT
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

> **Penting:** Jangan pernah commit file `.env` ke Git. File ini sudah ada di `.gitignore`.

---

### 4. Jalankan Backend

```bash
# Dari root project, dengan virtual env backend aktif
uvicorn backend.main:app --reload --port 8000
```

Atau dari dalam folder backend:

```bash
cd backend
venv\Scripts\activate   # Windows
uvicorn main:app --reload --port 8000
```

Cek apakah backend berjalan:

```
http://localhost:8000/        → { "status": "running", ... }
http://localhost:8000/health  → { "status": "healthy", ... }
http://localhost:8000/docs    → Swagger UI (development only)
```

---

### 5. Jalankan Frontend

Buka terminal baru:

```bash
cd frontend
venv\Scripts\activate   # Windows
streamlit run app.py
```

Frontend akan otomatis terbuka di browser: `http://localhost:8501`

---

## Verifikasi Instalasi

Jalankan test suite untuk memastikan semua komponen berfungsi:

```bash
# Dari root project, dengan virtual env backend aktif
pytest backend/tests/ -v

# Test spesifik
pytest backend/tests/test_auth.py -v
pytest backend/tests/test_events.py -v
pytest backend/tests/test_chatbot.py -v
```

---

## Environment Variables

Daftar lengkap variabel yang dapat dikonfigurasi di `backend/.env`:

### Database

| Variabel      | Default     | Keterangan           |
|---------------|-------------|----------------------|
| `DB_HOST`     | `localhost` | Host PostgreSQL      |
| `DB_PORT`     | `5432`      | Port PostgreSQL      |
| `DB_USER`     | `postgres`  | Username database    |
| `DB_PASSWORD` | *(kosong)*  | Password database    |
| `DB_NAME`     | `eventbot`  | Nama database        |

### Aplikasi

| Variabel                       | Default       | Keterangan                      |
|--------------------------------|---------------|---------------------------------|
| `APP_ENV`                      | `development` | `development` atau `production` |
| `SECRET_KEY`                   | *(dev key)*   | Secret key JWT — ganti di prod! |
| `JWT_ALGORITHM`                | `HS256`       | Algoritma JWT                   |
| `ACCESS_TOKEN_EXPIRE_MINUTES`  | `30`          | Durasi token (menit)            |

### Opsional

| Variabel        | Default    | Keterangan                    |
|-----------------|------------|-------------------------------|
| `UPLOAD_DIR`    | `uploads`  | Folder upload file gambar     |
| `MAX_FILE_SIZE` | `10485760` | Maks ukuran file upload (10MB)|
| `SMTP_HOST`     | *(kosong)* | Host SMTP untuk notifikasi    |
| `SMTP_PORT`     | `587`      | Port SMTP                     |
| `SMTP_USER`     | *(kosong)* | Email pengirim notifikasi     |
| `SMTP_PASSWORD` | *(kosong)* | Password email / app password |

---

## Perintah Berguna

### Backend

```bash
# Development (auto-reload)
uvicorn backend.main:app --reload --port 8000

# Production
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4

# Jalankan test
pytest backend/tests/ -v

# Test dengan coverage
pytest backend/tests/ --cov=backend --cov-report=term-missing
```

### Frontend

```bash
# Jalankan dengan port custom
streamlit run frontend/app.py --server.port 8502

# Headless (tanpa buka browser otomatis)
streamlit run frontend/app.py --server.headless true
```

### Database

```bash
# Koneksi langsung ke database
psql -U postgres -d eventbot

# Backup database
pg_dump -U postgres eventbot > backup_$(date +%Y%m%d).sql

# Restore dari backup
psql -U postgres -d eventbot < backup_20260708.sql

# Reset database dari awal (HATI-HATI: menghapus semua data)
psql -U postgres -c "DROP DATABASE IF EXISTS eventbot; CREATE DATABASE eventbot;"
psql -U postgres -d eventbot -f database/schema.sql
psql -U postgres -d eventbot -f database/functions.sql
psql -U postgres -d eventbot -f database/triggers.sql
```

---

## Troubleshooting

### Backend gagal start — `connection refused` ke database

```
psycopg2.OperationalError: could not connect to server
```

PostgreSQL belum berjalan atau kredensial salah.

```bash
# Windows
net start postgresql-x64-14

# Linux
sudo systemctl start postgresql

# Cek koneksi manual
psql -U postgres -h localhost -d eventbot
```

Pastikan nilai `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` di `.env` sudah benar.

---

### Backend error — `module not found`

```
ModuleNotFoundError: No module named 'fastapi'
```

Virtual environment belum aktif atau dependencies belum terinstall.

```bash
cd backend
venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

---

### Frontend tidak bisa connect ke backend

```
APIError: Tidak dapat terhubung ke server. Pastikan backend sudah berjalan.
```

Backend belum berjalan. Pastikan backend aktif di port 8000 dan coba akses `http://localhost:8000/health` di browser. URL base API ada di `frontend/utils/api_client.py` (default: `http://localhost:8000/api/v1`).

---

### Halaman admin tidak bisa diakses

Pastikan user yang login memiliki role `admin` di database. Cek via psql:

```sql
SELECT email, role FROM users WHERE email = 'your@email.com';
```

Jika perlu update role:

```sql
UPDATE users SET role = 'admin' WHERE email = 'your@email.com';
```

---

### Streamlit error — `DuplicateWidgetID`

Terjadi jika ada dua widget Streamlit dengan `key` yang sama di satu halaman. Pastikan setiap widget memiliki `key` yang unik, terutama di komponen yang di-render dalam loop.

---

### `psycopg2` gagal install di Windows

```bash
# Gunakan binary version
pip install psycopg2-binary
```

---

### Port sudah dipakai

```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux
lsof -i :8000
kill -9 <PID>
```

---

### Upload gambar gagal

Pastikan folder `backend/uploads/events/` ada dan bisa ditulis:

```bash
# Windows
mkdir backend\uploads\events

# Linux
mkdir -p backend/uploads/events
chmod 755 backend/uploads/events
```
