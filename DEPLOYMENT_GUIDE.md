# Panduan Deployment EventBot ke Cloud
## Deploy Full Stack (Frontend + Backend + Database)

### 📋 Ringkasan Strategi
1. **Database** → Neon/Supabase (PostgreSQL cloud gratis)
2. **Backend** → Railway/Render (FastAPI)
3. **Frontend** → Streamlit Cloud

---

## 🗄️ Step 1: Deploy Database (Neon PostgreSQL)

### 1.1 Buat Database di Neon
1. Buka https://neon.tech
2. Sign up / Login dengan GitHub
3. Klik **Create Project**
4. Beri nama: `eventbot-db`
5. Region: Pilih yang terdekat (Singapore untuk Indonesia)
6. Copy **Connection String** yang diberikan:
   ```
   postgresql://username:password@host.neon.tech/eventbot?sslmode=require
   ```

### 1.2 Import Schema & Data
```bash
# Set environment variable
$env:DATABASE_URL="postgresql://username:password@host.neon.tech/eventbot?sslmode=require"

# Import schema
psql $env:DATABASE_URL -f database/schema.sql
psql $env:DATABASE_URL -f database/functions.sql
psql $env:DATABASE_URL -f database/triggers.sql
psql $env:DATABASE_URL -f database/data.sql
```

**Alternatif menggunakan pgAdmin:**
1. Download pgAdmin: https://www.pgadmin.org/download/
2. Add new server dengan credentials dari Neon
3. Tools → Query Tool → Open File → Execute schema.sql, dst

---

## 🔧 Step 2: Deploy Backend (Railway)

### 2.1 Persiapan
1. Push semua perubahan ke GitHub:
   ```bash
   git add .
   git commit -m "Add deployment configs"
   git push origin main
   ```

### 2.2 Deploy ke Railway
1. Buka https://railway.app
2. Sign up dengan GitHub
3. Klik **New Project** → **Deploy from GitHub repo**
4. Pilih repository: `bastiandev9-dotcom/Eventbot`
5. Railway akan auto-detect Python app

### 2.3 Configure Environment Variables
Di Railway Dashboard → Variables → Add Variables:
```env
DB_HOST=your-neon-host.neon.tech
DB_PORT=5432
DB_USER=your-username
DB_PASSWORD=your-password
DB_NAME=eventbot
DB_SSLMODE=require

APP_ENV=production
SECRET_KEY=generate-random-32-chars-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
PORT=8000
```

### 2.4 Set Start Command
Settings → Deploy → Start Command:
```bash
cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
```

### 2.5 Generate Domain
Settings → Networking → Generate Domain

Copy URL: `https://eventbot-production-xxxx.up.railway.app`

---

## 🎨 Step 3: Deploy Frontend (Streamlit Cloud)

### 3.1 Deploy
1. Buka https://share.streamlit.io
2. Sign in dengan GitHub
3. Klik **New app**
4. Pilih:
   - **Repository**: `bastiandev9-dotcom/Eventbot`
   - **Branch**: `main`
   - **Main file path**: `streamlit_app.py`
5. Klik **Advanced settings**

### 3.2 Configure Secrets
Paste di Secrets (format TOML):
```toml
# Backend API URL from Railway
BACKEND_URL = "https://eventbot-production-xxxx.up.railway.app"

APP_ENV = "production"
```

### 3.3 Deploy
Klik **Deploy!**

Tunggu 2-5 menit, aplikasi akan live di:
```
https://your-app-name.streamlit.app
```

---

## ✅ Verifikasi Deployment

### Test Backend
```bash
curl https://eventbot-production-xxxx.up.railway.app/health
# Expected: {"status": "ok"}
```

### Test Frontend
1. Buka URL Streamlit Cloud
2. Coba login dengan akun default:
   - Email: `admin@eventbot.com`
   - Password: `admin123`
3. Test chatbot: ketik "Halo"
4. Test event explorer

---

## 🔧 Troubleshooting

### Backend tidak bisa connect ke Database
**Solusi**: Pastikan `DB_SSLMODE=require` ada di environment variables Railway

### Frontend tidak bisa connect ke Backend
**Solusi**: 
1. Cek `BACKEND_URL` di Streamlit Secrets sudah benar
2. Pastikan tidak ada trailing slash: `https://api.com` bukan `https://api.com/`
3. Pastikan backend sudah online (test dengan curl)

### CORS Error
Backend sudah dikonfigurasi CORS di `backend/main.py`. Jika masih error, pastikan:
- `allow_origins=["*"]` ada di konfigurasi CORS
- Request dari frontend menggunakan URL backend yang benar

### Database connection pool exhausted
**Solusi**: Neon free tier punya limit koneksi. Tambahkan di Railway env:
```env
DB_MAX_CONNECTIONS=5
```

---

## 📊 Monitoring

### Railway (Backend)
- Dashboard → Metrics untuk CPU/Memory/Network
- Logs → Real-time logs backend

### Streamlit Cloud
- Manage app → Logs untuk error frontend
- Analytics → Usage statistics

### Neon (Database)
- Dashboard → Monitoring → Query stats
- Connection pooling stats

---

## 💰 Biaya

### Free Tier Limits
- **Neon**: 0.5GB storage, 1 project
- **Railway**: $5 credit/bulan (cukup untuk demo)
- **Streamlit Cloud**: 1 private app gratis

### Upgrade Recommendations
Jika aplikasi production:
- **Database**: Supabase Pro ($25/bulan) untuk backup otomatis
- **Backend**: Railway Hobby ($5/bulan) untuk custom domain
- **Frontend**: Streamlit Community Cloud free, atau self-host

---

## 🔐 Security Checklist

- [ ] `.env` sudah masuk `.gitignore` (jangan commit secrets!)
- [ ] `SECRET_KEY` backend di-generate dengan `openssl rand -hex 32`
- [ ] PostgreSQL password strong (min 16 karakter)
- [ ] HTTPS enabled di semua service (default Railway + Streamlit)
- [ ] CORS hanya allow domain production setelah testing

---

## 📚 Resources

- [Railway Docs](https://docs.railway.app/)
- [Streamlit Cloud Docs](https://docs.streamlit.io/streamlit-community-cloud)
- [Neon Docs](https://neon.tech/docs/introduction)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)

---

**Selamat! EventBot sekarang live di cloud! 🎉**

URL Frontend: `https://eventbot.streamlit.app`
URL Backend API: `https://eventbot-production.up.railway.app`
Swagger Docs: `https://eventbot-production.up.railway.app/docs`
