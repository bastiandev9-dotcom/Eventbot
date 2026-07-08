# 🎯 EventBot Deployment Flow

Visual guide untuk deployment EventBot ke cloud.

---

## 📊 Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      🌐 Internet                             │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
        ┌─────────────────────────────┐
        │  🎨 Streamlit Cloud          │
        │  Frontend (streamlit_app.py) │
        │  https://eventbot.streamlit.app
        └─────────────┬───────────────┘
                      │ HTTP API calls
                      │ (via BACKEND_URL)
                      ▼
        ┌─────────────────────────────┐
        │  🔧 Railway                  │
        │  Backend FastAPI (uvicorn)   │
        │  https://backend.railway.app │
        └─────────────┬───────────────┘
                      │ PostgreSQL connection
                      │ (psycopg2)
                      ▼
        ┌─────────────────────────────┐
        │  🗄️ Neon PostgreSQL          │
        │  Database (Managed)          │
        │  neon.tech                   │
        └─────────────────────────────┘
```

---

## 🔄 Deployment Steps Flow

```
START
  │
  ├─► 📦 [1] Persiapan
  │    ├─ git add .
  │    ├─ git commit
  │    └─ git push origin main
  │
  ├─► 🗄️ [2] Deploy Database (Neon)
  │    ├─ Sign up di neon.tech
  │    ├─ Create project: eventbot-db
  │    ├─ Copy connection string
  │    └─ Import schema via psql
  │         ├─ schema.sql
  │         ├─ functions.sql
  │         ├─ triggers.sql
  │         └─ data.sql
  │
  ├─► 🔧 [3] Deploy Backend (Railway)
  │    ├─ Sign up di railway.app
  │    ├─ New Project → Deploy from GitHub
  │    ├─ Set Environment Variables:
  │    │   ├─ DB_HOST
  │    │   ├─ DB_PORT
  │    │   ├─ DB_USER
  │    │   ├─ DB_PASSWORD
  │    │   ├─ DB_NAME
  │    │   ├─ DB_SSLMODE=require
  │    │   ├─ SECRET_KEY
  │    │   └─ JWT_ALGORITHM
  │    ├─ Set Start Command:
  │    │   └─ cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
  │    ├─ Generate Domain
  │    └─ Test: curl https://backend.railway.app/health
  │
  ├─► 🎨 [4] Deploy Frontend (Streamlit)
  │    ├─ Sign up di share.streamlit.io
  │    ├─ New App:
  │    │   ├─ Repository: bastiandev9-dotcom/Eventbot
  │    │   ├─ Branch: main
  │    │   └─ Main file: streamlit_app.py
  │    ├─ Set Secrets:
  │    │   ├─ BACKEND_URL = "https://backend.railway.app"
  │    │   └─ APP_ENV = "production"
  │    └─ Click Deploy!
  │
  └─► ✅ [5] Verification
       ├─ Test login: admin@eventbot.com / admin123
       ├─ Test chatbot: "Halo"
       ├─ Test event explorer
       ├─ Test API docs: /docs
       └─ Monitor logs
```

---

## 🎯 File Dependencies

### Streamlit Cloud
```
streamlit_app.py  ────┬─→ frontend/app.py
                      │
requirements.txt      │   ├─→ views/*.py
                      │   ├─→ components/*.py
.streamlit/           │   ├─→ hooks/*.py
├─ config.toml       │   └─→ utils/api_client.py
└─ secrets.toml       │                │
   (not committed)    │                │
   BACKEND_URL ───────┘                │
                                       │
                     ┌─────────────────┘
                     │ HTTP requests to backend
                     │
                     ▼
```

### Railway (Backend)
```
railway.json ────┬─→ backend/main.py
                 │        │
Procfile         │        ├─→ api/v1/*.py
(alternatif)     │        ├─→ services/*.py
                 │        ├─→ models/*.py
                 │        ├─→ nlp/*.py
backend/         │        └─→ config/database.py
requirements.txt │                    │
                 │                    │
Environment Vars ─┘                   │
(DB_HOST, etc)                        │
                                      │
                     ┌────────────────┘
                     │ PostgreSQL connection
                     │
                     ▼
```

### Neon (Database)
```
database/schema.sql ────┬─→ PostgreSQL
database/functions.sql ─┤   (Managed Service)
database/triggers.sql ──┤
database/data.sql ──────┘
```

---

## 🔐 Secrets & Environment Variables

### Streamlit Cloud (Secrets)
```toml
# .streamlit/secrets.toml (production)
# Diset via Streamlit Cloud Dashboard

BACKEND_URL = "https://eventbot-backend.up.railway.app"
APP_ENV = "production"
```

### Railway (Environment Variables)
```env
# Diset via Railway Dashboard → Variables

# Database
DB_HOST=ep-xxx.neon.tech
DB_PORT=5432
DB_USER=neon_user
DB_PASSWORD=secure_password_here
DB_NAME=eventbot
DB_SSLMODE=require

# Security
SECRET_KEY=generate_with_openssl_rand_hex_32
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# App
APP_ENV=production
PORT=8000  # Auto-set by Railway
```

### Neon (Connection String)
```
postgresql://user:password@host.neon.tech/eventbot?sslmode=require
```

---

## ✅ Verification Checklist

```
Database (Neon)
  ☐ Project created
  ☐ Schema imported successfully
  ☐ Test query: SELECT * FROM users;
  ☐ Connection string copied

Backend (Railway)
  ☐ GitHub repo connected
  ☐ Environment variables set (9 vars)
  ☐ Start command configured
  ☐ Domain generated
  ☐ Health check passes: /health
  ☐ Swagger UI accessible: /docs
  ☐ Database connection successful

Frontend (Streamlit)
  ☐ App deployed from repo
  ☐ streamlit_app.py set as main file
  ☐ BACKEND_URL secret added
  ☐ App builds successfully
  ☐ Landing page loads
  ☐ Login works
  ☐ Chatbot responds
  ☐ Event Explorer shows data
  ☐ Admin dashboard accessible

Integration
  ☐ Frontend → Backend API calls work
  ☐ Backend → Database queries work
  ☐ CORS configured properly
  ☐ JWT authentication works
  ☐ File uploads work (if enabled)
  ☐ No console errors
```

---

## 📱 URLs After Deployment

### Production
```
Frontend:     https://eventbot.streamlit.app
Backend API:  https://eventbot-production.up.railway.app
API Docs:     https://eventbot-production.up.railway.app/docs
Database:     ep-xxx.neon.tech (internal)
```

### Monitoring
```
Streamlit:    https://share.streamlit.io/[your-username]
Railway:      https://railway.app/project/[project-id]
Neon:         https://console.neon.tech/app/projects/[project-id]
```

---

## 🔧 Troubleshooting Decision Tree

```
Problem: Frontend tidak load
  │
  ├─ Check Streamlit Cloud logs
  │  └─ Error: "Module not found"
  │      └─ Fix: Update requirements.txt
  │
  └─ Error: "Cannot connect to backend"
      └─ Check BACKEND_URL in Secrets
          ├─ Typo? → Fix URL
          └─ Backend down? → Check Railway

Problem: Backend tidak connect DB
  │
  ├─ Check Railway logs
  │  └─ Error: "connection refused"
  │      └─ Check DB_HOST, DB_USER, DB_PASSWORD
  │
  └─ Error: "SSL required"
      └─ Add: DB_SSLMODE=require

Problem: Database import failed
  │
  └─ Check psql connection
      ├─ Use full connection string
      └─ Add ?sslmode=require
```

---

## 💰 Cost Breakdown (Free Tier)

```
Service         Free Tier           Limits
────────────────────────────────────────────────
Neon            0.5 GB storage      1 project
                                    Unlimited queries
                                    
Railway         $5 credit/month     ~500 hours runtime
                                    512MB RAM
                                    1GB disk
                                    
Streamlit       1 private app       Unlimited viewers
Cloud                               1GB resources
                                    
────────────────────────────────────────────────
TOTAL           FREE for demo       Cukup untuk proyek kuliah! 🎓
```

---

**Flow ini akan memandu Anda step-by-step! 🚀**

Baca `QUICK_DEPLOY.md` untuk implementasi detail setiap step.
