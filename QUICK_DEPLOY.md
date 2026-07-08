# 🚀 Quick Deploy EventBot ke Streamlit Cloud

Panduan super cepat deploy EventBot (5-10 menit).

---

## Prasyarat
- ✅ Akun GitHub (untuk repository)
- ✅ Akun Streamlit Cloud (gratis)
- ✅ Akun Railway/Render (backend)
- ✅ Akun Neon/Supabase (database)

---

## 🗄️ Step 1: Database (5 menit)

1. **Buka** https://neon.tech → Sign up dengan GitHub
2. **Buat project** → Nama: `eventbot-db` → Region: Singapore
3. **Copy connection string**:
   ```
   postgresql://user:pass@host.neon.tech/eventbot?sslmode=require
   ```
4. **Import data** menggunakan pgAdmin atau psql:
   ```bash
   psql "postgresql://..." -f database/schema.sql
   psql "postgresql://..." -f database/functions.sql
   psql "postgresql://..." -f database/triggers.sql
   psql "postgresql://..." -f database/data.sql
   ```

✅ **Test**: Buka Neon Console → SQL Editor → `SELECT * FROM users;`

---

## 🔧 Step 2: Backend (5 menit)

1. **Push code ke GitHub** (jika belum):
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Buka** https://railway.app → Login dengan GitHub

3. **New Project** → **Deploy from GitHub repo** → Pilih: `bastiandev9-dotcom/Eventbot`

4. **Settings** → **Variables** → Tambahkan:
   ```env
   DB_HOST=your-neon-host.neon.tech
   DB_PORT=5432
   DB_USER=neon-username
   DB_PASSWORD=neon-password
   DB_NAME=eventbot
   DB_SSLMODE=require
   SECRET_KEY=generate-dengan-openssl-rand-hex-32
   JWT_ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   APP_ENV=production
   ```

5. **Settings** → **Start Command**:
   ```bash
   cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

6. **Settings** → **Networking** → **Generate Domain**

7. **Copy URL**: `https://eventbot-production.up.railway.app`

✅ **Test**: Buka `https://your-backend.railway.app/docs`

---

## 🎨 Step 3: Frontend (2 menit)

1. **Buka** https://share.streamlit.io → Sign in dengan GitHub

2. **New app**:
   - Repository: `bastiandev9-dotcom/Eventbot`
   - Branch: `main`
   - Main file path: `streamlit_app.py`

3. **Advanced settings** → **Secrets** → Paste:
   ```toml
   BACKEND_URL = "https://eventbot-production.up.railway.app"
   APP_ENV = "production"
   ```

4. **Deploy!**

5. Tunggu 2-5 menit sampai muncul URL:
   ```
   https://eventbot.streamlit.app
   ```

✅ **Test**: Login dengan `admin@eventbot.com` / `admin123`

---

## ✅ Verification Checklist

- [ ] Database bisa diakses via pgAdmin/psql
- [ ] Backend Swagger docs bisa dibuka: `/docs`
- [ ] Frontend loading tanpa error
- [ ] Login berhasil
- [ ] Chatbot merespons "Halo"
- [ ] Event Explorer menampilkan data

---

## 🆘 Troubleshooting

### ❌ Frontend: "Tidak dapat terhubung ke server"
**Fix**: Cek `BACKEND_URL` di Streamlit Secrets (tidak ada trailing slash!)

### ❌ Backend: "Could not connect to database"
**Fix**: Tambahkan `DB_SSLMODE=require` di Railway Variables

### ❌ Database: "permission denied"
**Fix**: Pastikan Neon user punya write access (default sudah ada)

---

## 📚 Dokumentasi Lengkap

Untuk penjelasan detail setiap langkah:
- **DEPLOYMENT_GUIDE.md** — Panduan lengkap dengan screenshot
- **DEPLOYMENT_CHECKLIST.md** — Checklist detail untuk production

---

## 💰 Biaya

Semua service di atas **GRATIS** untuk tier dasar:
- **Neon**: 0.5GB storage
- **Railway**: $5 credit/bulan
- **Streamlit Cloud**: 1 app private

Cukup untuk demo & proyek kuliah! 🎓

---

**Happy Deploying! 🚀**

Made with ❤️ for Teori Bahasa dan Otomata
