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
from backend.core.middleware import CorrelationIdMiddleware, RequestLoggingMiddleware
from backend.core.tenant import TenantMiddleware
from backend.core.security_headers import SecurityHeadersMiddleware
from backend.core.payload_limit import PayloadSizeLimitMiddleware
from backend.core.logging import setup_logging, logger
from backend.core.responses import APIResponse, APIErrorResponse
from backend.core.exceptions import EduSphereException
from fastapi.exceptions import RequestValidationError

# Import all routers
from backend.routers.auth import router as auth_router
from backend.routers.students import router as students_router
from backend.routers.lecturers import router as lecturers_router
from backend.routers.ai_assistant import router as ai_router
from backend.routers.portals import (
    alumni_router, library_router, sports_router,
    news_router, admin_router, ws_router
)
from backend.routers.rbac import router as rbac_router
from backend.routers.tenants import router as tenants_router
from backend.routers.accounts import router as accounts_router
from backend.routers.audit import router as audit_router
from backend.routers.institutions import router as institutions_router
from backend.routers.academic_terms import router as academic_terms_router
from backend.routers.programs import router as programs_router
from backend.routers.courses import router as courses_router
from backend.routers.enrollments import router as enrollments_router
from backend.routers.cohorts import router as cohorts_router
from backend.routers.advising import router as advising_router
from backend.routers.academic_records import router as academic_records_router
from backend.routers.documents import router as documents_router
from backend.routers.videos import router as videos_router
from backend.routers.progress import router as progress_router
from backend.routers.announcements import router as announcements_router
from backend.routers.v1 import v1_router


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

# Configure centralized logging
setup_logging(level="DEBUG" if settings.debug else "INFO", json_logs=settings.is_production)

# ── Middleware ─────────────────────────────────────────────────────────────────

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(PayloadSizeLimitMiddleware)
app.add_middleware(TenantMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API Routers ────────────────────────────────────────────────────────────────

# Versioned API v1 Router
app.include_router(v1_router)

# Legacy / Non-versioned Routers for backward compatibility
app.include_router(auth_router)
app.include_router(students_router)
app.include_router(lecturers_router)
app.include_router(alumni_router)
app.include_router(library_router)
app.include_router(sports_router)
app.include_router(news_router)
app.include_router(admin_router)
app.include_router(rbac_router)
app.include_router(tenants_router)
app.include_router(accounts_router)
app.include_router(audit_router)
app.include_router(institutions_router)
app.include_router(academic_terms_router)
app.include_router(programs_router)
app.include_router(courses_router)
app.include_router(enrollments_router)
app.include_router(cohorts_router)
app.include_router(advising_router)
app.include_router(academic_records_router)
app.include_router(documents_router)
app.include_router(videos_router)
app.include_router(progress_router)
app.include_router(announcements_router)
app.include_router(ai_router)
app.include_router(ws_router)

# ── Health Check ───────────────────────────────────────────────────────────────

@app.get("/api/health", tags=["System"])
@app.get("/api/v1/health", tags=["System"])
async def health_check(request: Request):
    cid = getattr(request.state, "correlation_id", None)
    payload = {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment.value,
        "ai_enabled": settings.ai_enabled,
        "institution": settings.institution_name,
    }
    return APIResponse.ok(data=payload, correlation_id=cid)

# ── Static Files & Production React SPA Serving ────────────────────────────────

dist_path = Path(__file__).parent / "static_dist"
if (dist_path / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(dist_path / "assets")), name="assets")

@app.get("/{full_path:path}", include_in_schema=False)
async def serve_react_app(full_path: str):
    """Fallback handler to serve built React SPA for any non-API routes"""
    if full_path.startswith("api/") or full_path == "api":
        raise HTTPException(status_code=404, detail="API endpoint not found")

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

@app.exception_handler(EduSphereException)
async def edusphere_exception_handler(request: Request, exc: EduSphereException):
    cid = getattr(request.state, "correlation_id", None)
    return JSONResponse(
        status_code=400,
        content=APIErrorResponse.build(
            code="DOMAIN_ERROR", message=exc.message, details=exc.details, correlation_id=cid
        ).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    cid = getattr(request.state, "correlation_id", None)
    return JSONResponse(
        status_code=422,
        content=APIErrorResponse.build(
            code="VALIDATION_ERROR",
            message="Invalid request payload or query parameters.",
            details={"errors": exc.errors()},
            correlation_id=cid,
        ).model_dump(),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    cid = getattr(request.state, "correlation_id", None)
    code = "HTTP_ERROR"
    if exc.status_code == 401:
        code = "UNAUTHORIZED"
    elif exc.status_code == 403:
        code = "FORBIDDEN"
    elif exc.status_code == 404:
        code = "NOT_FOUND"
    elif exc.status_code == 400:
        code = "BAD_REQUEST"
    elif exc.status_code == 429:
        code = "RATE_LIMIT_EXCEEDED"

    detail_str = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content=APIErrorResponse.build(
            code=code, message=detail_str, correlation_id=cid
        ).model_dump(),
        headers=exc.headers,
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    cid = getattr(request.state, "correlation_id", None)
    return JSONResponse(
        status_code=500,
        content=APIErrorResponse.build(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected internal server error occurred.",
            details={"debug_info": str(exc)} if settings.debug else None,
            correlation_id=cid,
        ).model_dump(),
    )


# ── Entry Point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
