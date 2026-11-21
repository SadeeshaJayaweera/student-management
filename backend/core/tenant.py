"""
NSBM EduSphere — Multi-Tenant Institution Isolation
ContextVar-backed tenant resolution, middleware, dependencies, and query filters.
"""
from contextvars import ContextVar
from typing import Optional, Any
from fastapi import Request, Depends, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from backend.database import get_db, AsyncSessionLocal
from backend.models import Institution, User, UserRole


tenant_id_ctx: ContextVar[Optional[int]] = ContextVar("tenant_id_ctx", default=None)
tenant_code_ctx: ContextVar[Optional[str]] = ContextVar("tenant_code_ctx", default=None)


def get_current_tenant_id() -> Optional[int]:
    """Retrieves the current active tenant identifier from context"""
    return tenant_id_ctx.get()


def set_current_tenant_id(tenant_id: Optional[int]) -> None:
    """Sets the current active tenant identifier in context"""
    tenant_id_ctx.set(tenant_id)


def get_current_tenant_code() -> Optional[str]:
    """Retrieves the current active institution code from context"""
    return tenant_code_ctx.get()


def set_current_tenant_code(code: Optional[str]) -> None:
    """Sets the current active institution code in context"""
    tenant_code_ctx.set(code)


class TenantMiddleware(BaseHTTPMiddleware):
    """
    HTTP middleware that extracts and binds the active institution tenant.
    Resolves tenant from headers (X-Tenant-ID, X-Institution-Code) or host subdomain.
    """
    async def dispatch(self, request: Request, call_next):
        tenant_id: Optional[int] = None
        tenant_code: Optional[str] = None

        # 1. Header resolution
        raw_tenant_id = request.headers.get("x-tenant-id")
        if raw_tenant_id and raw_tenant_id.isdigit():
            tenant_id = int(raw_tenant_id)

        raw_code = request.headers.get("x-institution-code")
        if raw_code:
            tenant_code = raw_code.strip().upper()

        # 2. Host / Subdomain resolution if header not present
        if not tenant_id and not tenant_code:
            host = request.headers.get("host", "").split(":")[0]
            parts = host.split(".")
            if len(parts) >= 3 and parts[0] not in ("www", "api", "app", "localhost"):
                tenant_code = parts[0].upper()

        # Set context variables
        token_id = tenant_id_ctx.set(tenant_id)
        token_code = tenant_code_ctx.set(tenant_code)

        try:
            response = await call_next(request)
            if tenant_id:
                response.headers["X-Tenant-ID"] = str(tenant_id)
            if tenant_code:
                response.headers["X-Institution-Code"] = tenant_code
            return response
        finally:
            tenant_id_ctx.reset(token_id)
            tenant_code_ctx.reset(token_code)


async def get_current_tenant_optional(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Optional[Institution]:
    """
    Resolves the Institution object for the current request.
    Returns None if no tenant is specified or if global system context.
    """
    tenant_id = get_current_tenant_id()
    tenant_code = get_current_tenant_code()

    if not tenant_id and not tenant_code:
        return None

    query = select(Institution)
    if tenant_id and tenant_code:
        query = query.where(or_(Institution.id == tenant_id, Institution.code == tenant_code))
    elif tenant_id:
        query = query.where(Institution.id == tenant_id)
    elif tenant_code:
        query = query.where(Institution.code == tenant_code)

    res = await db.execute(query)
    return res.scalar_one_or_none()


async def require_tenant(
    tenant: Optional[Institution] = Depends(get_current_tenant_optional),
) -> Institution:
    """Enforces that an active institution tenant is identified for the endpoint"""
    if not tenant or not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid and active institutional tenant context is required for this operation.",
        )
    return tenant


def apply_tenant_filter(query: Any, model: Any, tenant_id: Optional[int] = None) -> Any:
    """
    Applies multi-tenant isolation filter to SQLAlchemy query.
    If model has `institution_id`, restricts results to matching tenant.
    """
    t_id = tenant_id or get_current_tenant_id()
    if t_id and hasattr(model, "institution_id"):
        return query.where(model.institution_id == t_id)
    return query
