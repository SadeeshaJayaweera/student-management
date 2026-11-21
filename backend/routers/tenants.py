"""
NSBM EduSphere — Multi-Tenant Institution Management Router
Manages institutional tenant provisioning, isolation resolution, and domain bindings.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database import get_db
from backend.models import Institution, User, UserRole
from backend.schemas import InstitutionOut, InstitutionCreate, InstitutionUpdate
from backend.core.dependencies import get_current_user
from backend.core.tenant import get_current_tenant_optional

router = APIRouter(prefix="/api/tenants", tags=["Multi-Tenant Institutions"])


def require_superadmin(current_user: User = Depends(get_current_user)) -> User:
    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if role_val != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superadmin privileges required for tenant institution management."
        )
    return current_user


@router.get("/current", response_model=Optional[InstitutionOut])
async def get_current_tenant_info(
    tenant: Optional[Institution] = Depends(get_current_tenant_optional),
):
    """Returns the resolved institution tenant for the current request context"""
    if not tenant:
        return None
    return tenant


@router.get("", response_model=List[InstitutionOut])
async def list_institutions(
    current_user: User = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """List all registered institutions across the platform (Superadmin only)"""
    res = await db.execute(select(Institution).order_by(Institution.name))
    return list(res.scalars().all())


@router.post("", response_model=InstitutionOut, status_code=201)
async def create_institution(
    payload: InstitutionCreate,
    current_user: User = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Register and provision a new institution tenant (Superadmin only)"""
    code_upper = payload.code.strip().upper()
    existing = await db.execute(select(Institution).where(Institution.code == code_upper))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Institution with code '{code_upper}' already exists."
        )

    institution = Institution(
        code=code_upper,
        name=payload.name.strip(),
        subdomain=payload.subdomain.lower() if payload.subdomain else None,
        domain=payload.domain.lower() if payload.domain else None,
        is_active=True,
        settings=payload.settings or {},
    )
    db.add(institution)
    await db.commit()
    await db.refresh(institution)
    return institution


@router.get("/{institution_id}", response_model=InstitutionOut)
async def get_institution_by_id(
    institution_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get institution details by ID"""
    res = await db.execute(select(Institution).where(Institution.id == institution_id))
    inst = res.scalar_one_or_none()
    if not inst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found")
    return inst


@router.put("/{institution_id}", response_model=InstitutionOut)
async def update_institution(
    institution_id: int,
    payload: InstitutionUpdate,
    current_user: User = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Update institutional tenant configurations (Superadmin only)"""
    res = await db.execute(select(Institution).where(Institution.id == institution_id))
    inst = res.scalar_one_or_none()
    if not inst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found")

    if payload.name is not None:
        inst.name = payload.name.strip()
    if payload.subdomain is not None:
        inst.subdomain = payload.subdomain.lower()
    if payload.domain is not None:
        inst.domain = payload.domain.lower()
    if payload.is_active is not None:
        inst.is_active = payload.is_active
    if payload.settings is not None:
        inst.settings = payload.settings

    await db.commit()
    await db.refresh(inst)
    return inst
