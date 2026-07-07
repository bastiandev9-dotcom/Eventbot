"""
EventBot Backend - Main Application
====================================
Entry point untuk FastAPI application.

Menjalankan:
    uvicorn backend.main:app --reload --port 8000
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
import time

from backend.config.settings import APP_NAME, APP_VERSION, APP_ENV, DEBUG
from backend.config.database import get_connection_pool, close_all_connections
from backend.api.v1 import router as api_v1_router
from backend.api.websocket import websocket_router


# ── Lifespan ──────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inisialisasi dan cleanup saat app start/stop."""
    # Startup
    try:
        get_connection_pool()
        print(f"{APP_NAME} v{APP_VERSION} started [{APP_ENV}]")
    except Exception as e:
        print(f"Startup error: {e}")

    yield

    # Shutdown
    close_all_connections()
    print(f"{APP_NAME} shutdown gracefully")


# ── App Instance ──────────────────────────────────────────
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="EventBot API — Chatbot berbasis NLP untuk manajemen event",
    docs_url="/docs" if DEBUG else None,
    redoc_url="/redoc" if DEBUG else None,
    openapi_url="/openapi.json" if DEBUG else None,
    lifespan=lifespan,
)

# ── CORS Middleware ───────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if DEBUG else ["https://eventbot.example.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request Timing Middleware ─────────────────────────────
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    return response


# ── Routers ───────────────────────────────────────────────
app.include_router(api_v1_router, prefix="/api/v1")
app.include_router(websocket_router)

# ── Static Files (uploads) ────────────────────────────────
# Gambar yang diupload bisa diakses via: http://localhost:8000/uploads/events/nama-file.jpg
_UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(os.path.join(_UPLOADS_DIR, "events"), exist_ok=True)
app.mount("/uploads", StaticFiles(directory=_UPLOADS_DIR), name="uploads")


# ── Upload Endpoint ───────────────────────────────────────
from fastapi import UploadFile, File, Header, HTTPException, status as http_status
import uuid
import shutil

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@app.post("/api/v1/upload/image", tags=["Upload"])
async def upload_image(
    file: UploadFile = File(...),
    folder: str = "events",
    authorization: str = Header(None),
):
    """
    Upload gambar event ke server.

    - **file**: File gambar (jpg, jpeg, png, webp, gif). Maks 10 MB.
    - **folder**: Sub-folder tujuan (default: events)

    Returns URL gambar yang bisa langsung dipakai sebagai image_url:
    `http://localhost:8000/uploads/events/nama-file.jpg`
    """
    from backend.api.deps import require_auth

    # Validasi auth
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED, detail="Token tidak ditemukan")
    try:
        require_auth(authorization.split(" ", 1)[1])
    except ValueError as e:
        raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED, detail=str(e))

    # Validasi ekstensi
    _, ext = os.path.splitext(file.filename or "")
    ext = ext.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Format tidak didukung. Gunakan: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Validasi ukuran file
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Ukuran file terlalu besar. Maksimal 10 MB.",
        )

    # Simpan dengan nama unik agar tidak ada tabrakan
    safe_folder = os.path.basename(folder)  # Cegah path traversal
    dest_dir = os.path.join(_UPLOADS_DIR, safe_folder)
    os.makedirs(dest_dir, exist_ok=True)

    filename = f"{uuid.uuid4().hex}{ext}"
    dest_path = os.path.join(dest_dir, filename)

    with open(dest_path, "wb") as f:
        f.write(contents)

    url = f"http://localhost:8000/uploads/{safe_folder}/{filename}"
    return {
        "success":  True,
        "url":      url,
        "filename": filename,
        "size":     len(contents),
        "message":  "Gambar berhasil diupload",
    }


# ── Root Endpoints ────────────────────────────────────────
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint — health check dasar."""
    return {
        "app": APP_NAME,
        "version": APP_VERSION,
        "status": "running",
        "env": APP_ENV,
    }


@app.get("/health", tags=["Root"])
async def health_check():
    """Health check endpoint untuk load balancer / monitoring."""
    from backend.config.database import test_connection
    db_ok = test_connection()
    status = "healthy" if db_ok else "degraded"
    return JSONResponse(
        status_code=200 if db_ok else 503,
        content={
            "status": status,
            "database": "connected" if db_ok else "disconnected",
        },
    )
