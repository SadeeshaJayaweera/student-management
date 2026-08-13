"""
NSBM EduSphere — Main FastAPI Application
Production-grade Student Management System
"""
import os
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse

from backend.config import settings
from backend.database import init_db

# Import all routers
from backend.routers.auth import router as auth_router
from backend.routers.students import router as students_router
from backend.routers.lecturers import router as lecturers_router
from backend.routers.ai_assistant import router as ai_router
from backend.routers.portals import (
    alumni_router, library_router, sports_router,
    news_router, admin_router, ws_router
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    print(f"\n🚀 Starting {settings.app_name} v{settings.app_version}")
    print("=" * 60)

    # Initialize database
    print("📦 Initializing database...")
    await init_db()

    # Seed database with demo data
    print("🌱 Seeding demo data...")
    try:
        from backend.utils.seeder import seed_database
        await seed_database()
    except Exception as e:
        print(f"⚠️  Seeder: {e}")

    # Initialize RAG service
    print("🤖 Initializing AI/RAG service...")
    try:
        from backend.services.rag_service import rag_service
        await rag_service.initialize()
    except Exception as e:
        print(f"⚠️  RAG Service: {e}")

    # Create upload directories
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.chroma_persist_dir).mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print(f"✅ {settings.app_name} is LIVE!")
    print(f"📍 Backend API: http://localhost:8000")
    print(f"📖 Swagger Docs: http://localhost:8000/docs")
    print(f"⚛️  React Frontend: http://localhost:5173 (dev) or http://localhost:8000 (prod)")
    print(f"🔐 Demo Logins:")
    print(f"   • Admin:    admin     / Admin@123")
    print(f"   • Student:  student01 / Student@123")
    print(f"   • Lecturer: kperera   / Lecturer@123")
    print(f"   • Alumni:   alumni01  / Alumni@123")
    print("=" * 60 + "\n")

    yield

    print(f"\n👋 {settings.app_name} shutting down...")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Advanced Student Management System with AI-powered portals for Students, Lecturers, Alumni, Library, Sports & Clubs, and News",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── Middleware ─────────────────────────────────────────────────────────────────

app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API Routers ────────────────────────────────────────────────────────────────

app.include_router(auth_router)
app.include_router(students_router)
app.include_router(lecturers_router)
app.include_router(alumni_router)
app.include_router(library_router)
app.include_router(sports_router)
app.include_router(news_router)
app.include_router(admin_router)
app.include_router(ai_router)
app.include_router(ws_router)

# ── Health Check ───────────────────────────────────────────────────────────────

@app.get("/api/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "ai_enabled": settings.ai_enabled,
        "institution": settings.institution_name
    }

# ── Static Files & Production React SPA Serving ────────────────────────────────

dist_path = Path(__file__).parent / "static_dist"
if (dist_path / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(dist_path / "assets")), name="assets")

@app.get("/{full_path:path}", include_in_schema=False)
async def serve_react_app(full_path: str):
    """Fallback handler to serve built React SPA for any non-API routes"""
    # Check if the requested file exists in dist
    target_file = dist_path / full_path
    if full_path and target_file.is_file():
        return FileResponse(target_file)
    
    # Fallback to React index.html for client-side routing
    index_file = dist_path / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    
    return HTMLResponse(
        "<h2>React frontend is building or running on Vite dev server (http://localhost:5173).</h2>"
        "<p>API is available at <a href='/docs'>/docs</a>.</p>"
    )


# ── Global Exception Handlers ──────────────────────────────────────────────────

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status_code": exc.status_code}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc) if settings.debug else "Contact admin"}
    )


# ── Entry Point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )
