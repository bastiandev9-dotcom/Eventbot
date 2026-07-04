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
import time

from backend.config.settings import APP_NAME, APP_VERSION, APP_ENV, DEBUG
from backend.config.database import get_connection_pool, close_all_connections
from backend.api.v1 import router as api_v1_router
from backend.api.websocket import websocket_router

# ── App Instance ──────────────────────────────────────────
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="EventBot API — Chatbot berbasis NLP untuk manajemen event",
    docs_url="/docs" if DEBUG else None,
    redoc_url="/redoc" if DEBUG else None,
    openapi_url="/openapi.json" if DEBUG else None,
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


# ── Startup / Shutdown Events ─────────────────────────────
@app.on_event("startup")
async def startup_event():
    """Inisialisasi database connection pool saat app start."""
    try:
        get_connection_pool()
        print(f"{APP_NAME} v{APP_VERSION} started [{APP_ENV}]")
    except Exception as e:
        print(f"Startup error: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Tutup semua koneksi database saat app shutdown."""
    close_all_connections()
    print(f"{APP_NAME} shutdown gracefully")


# ── Routers ───────────────────────────────────────────────
app.include_router(api_v1_router, prefix="/api/v1")
app.include_router(websocket_router)


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
