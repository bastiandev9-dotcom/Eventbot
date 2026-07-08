# ✅ Deployment Checklist EventBot

## Pre-Deployment

- [ ] Semua fitur sudah di-test lokal
- [ ] Virtual environment sudah dihapus dari tracking (`venv/` in `.gitignore`)
- [ ] `.env` tidak ter-commit (hanya `.env.example`)
- [ ] `requirements.txt` sudah up-to-date
- [ ] Dokumentasi API lengkap di `docs/`

## Database (Neon/Supabase)

- [ ] Account dibuat di https://neon.tech
- [ ] Project database dibuat: `eventbot-db`
- [ ] Connection string sudah dicopy
- [ ] Schema SQL sudah diimport via psql/pgAdmin:
  - [ ] `database/schema.sql`
  - [ ] `database/functions.sql`
  - [ ] `database/triggers.sql`
  - [ ] `database/data.sql`
- [ ] Test koneksi: `psql "your-connection-string" -c "SELECT COUNT(*) FROM users;"`

## Backend (Railway/Render)

- [ ] Code sudah di-push ke GitHub
- [ ] Account dibuat di https://railway.app
- [ ] Project Railway dibuat dan linked ke GitHub repo
- [ ] Environment variables sudah diset:
  - [ ] `DB_HOST`
  - [ ] `DB_PORT`
  - [ ] `DB_USER`
  - [ ] `DB_PASSWORD`
  - [ ] `DB_NAME`
  - [ ] `DB_SSLMODE=require`
  - [ ] `SECRET_KEY` (generated: `openssl rand -hex 32`)
  - [ ] `JWT_ALGORITHM=HS256`
  - [ ] `ACCESS_TOKEN_EXPIRE_MINUTES=30`
  - [ ] `APP_ENV=production`
- [ ] Start command diset: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
- [ ] Domain generated dan dicopy
- [ ] Test endpoint: `curl https://your-backend.railway.app/health`
- [ ] Test Swagger UI: `https://your-backend.railway.app/docs`

## Frontend (Streamlit Cloud)

- [ ] Account dibuat di https://share.streamlit.io
- [ ] Repository linked: `bastiandev9-dotcom/Eventbot`
- [ ] Main file path: `streamlit_app.py`
- [ ] Secrets configured:
  ```toml
  BACKEND_URL = "https://your-backend.railway.app"
  APP_ENV = "production"
  ```
- [ ] Deploy button clicked
- [ ] App successfully deployed
- [ ] Test login dengan akun default
- [ ] Test semua halaman utama:
  - [ ] Landing page
  - [ ] Event Explorer
  - [ ] Chatbot
  - [ ] Profile (setelah login)
  - [ ] Admin Dashboard (login as admin)

## Post-Deployment Testing

### Functional Tests
- [ ] User bisa register akun baru
- [ ] User bisa login
- [ ] User bisa browse events
- [ ] User bisa search events dengan filter
- [ ] Chatbot merespons "Halo"
- [ ] Chatbot bisa cari event: "Ada event musik?"
- [ ] User bisa beli tiket (jika fitur payment enabled)
- [ ] Admin bisa CRUD event
- [ ] Admin bisa CRUD tiket
- [ ] Admin bisa manage users
- [ ] Dashboard admin menampilkan statistik

### Performance Tests
- [ ] Loading time < 3 detik
- [ ] API response time < 500ms
- [ ] Database query time < 200ms
- [ ] No memory leaks (monitor Railway dashboard)

### Security Tests
- [ ] HTTPS enabled di semua endpoint
- [ ] JWT token berfungsi
- [ ] Protected routes tidak bisa diakses tanpa login
- [ ] Admin routes hanya bisa diakses admin
- [ ] CORS hanya allow domain yang valid
- [ ] SQL injection prevention (prepared statements)
- [ ] XSS prevention (input sanitization)

## Monitoring Setup

- [ ] Railway monitoring dashboard checked
- [ ] Streamlit Cloud logs configured
- [ ] Neon database monitoring enabled
- [ ] Alert setup untuk downtime (optional)

## Documentation

- [ ] README.md updated dengan production URLs
- [ ] API docs accessible di `/docs`
- [ ] Credentials untuk testing dicatat (jangan commit!)
- [ ] Deployment notes documented

## Rollback Plan

Jika ada error setelah deployment:

1. **Frontend error**: Revert to previous app version di Streamlit Cloud
2. **Backend error**: Railway → Deployments → Rollback to previous deploy
3. **Database error**: Restore dari backup (Neon auto-backup)

## Next Steps (Optional)

- [ ] Custom domain setup
- [ ] CDN untuk static files (Cloudflare)
- [ ] Email notifications (SendGrid/Mailgun)
- [ ] Scheduled backups
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Error tracking (Sentry)
- [ ] Analytics (Google Analytics/Plausible)

---

**Ready to deploy? Start with Database → Backend → Frontend! 🚀**

Dokumentasi lengkap: `DEPLOYMENT_GUIDE.md`
