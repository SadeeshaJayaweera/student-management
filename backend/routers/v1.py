"""
NSBM EduSphere — API v1 Router
Aggregates and exposes all domain routers under /api/v1 prefix
"""
from fastapi import APIRouter
from fastapi.routing import APIRoute

from backend.routers.auth import router as auth_router
from backend.routers.students import router as students_router
from backend.routers.lecturers import router as lecturers_router
from backend.routers.ai_assistant import router as ai_router
from backend.routers.rbac import router as rbac_router
from backend.routers.tenants import router as tenants_router
from backend.routers.accounts import router as accounts_router
from backend.routers.audit import router as audit_router
from backend.routers.institutions import router as institutions_router
from backend.routers.academic_terms import router as academic_terms_router
from backend.routers.programs import router as programs_router
from backend.routers.portals import (
    alumni_router, library_router, sports_router,
    news_router, admin_router
)

v1_router = APIRouter(prefix="/api/v1")

# Mirror routes from domain routers under /api/v1 prefix
for domain_router in [
    auth_router, students_router, lecturers_router, alumni_router,
    library_router, sports_router, news_router, admin_router, ai_router,
    rbac_router, tenants_router, accounts_router, audit_router, institutions_router,
    academic_terms_router, programs_router
]:
    for route in domain_router.routes:
        if isinstance(route, APIRoute):
            # Clean path under /api/v1 (e.g. "/api/auth/login" -> "/auth/login")
            v1_sub_path = route.path.replace("/api", "", 1)
            v1_router.add_api_route(
                v1_sub_path,
                route.endpoint,
                methods=list(route.methods or ["GET"]),
                response_model=route.response_model,
                status_code=route.status_code,
                tags=route.tags,
                dependencies=route.dependencies,
                summary=route.summary,
                description=route.description,
            )
