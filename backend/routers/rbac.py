"""
NSBM EduSphere — RBAC Management Router
Provides endpoints to list permissions, view roles, manage custom roles,
and inspect current user's resolved permission matrix.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database import get_db
from backend.models import User, Role, Permission, RolePermission
from backend.schemas import (
    PermissionOut,
    RoleOut,
    RoleCreateRequest,
    RolePermissionUpdateRequest,
    UserPermissionsResponse,
)
from backend.core.dependencies import get_current_user
from backend.core.rbac import (
    StandardPermissions,
    require_permission,
    get_user_permissions,
)

router = APIRouter(prefix="/api/rbac", tags=["Role-Based Access Control"])


@router.get("/permissions", response_model=List[PermissionOut])
async def list_permissions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all available system permissions"""
    result = await db.execute(select(Permission).order_by(Permission.module, Permission.code))
    return list(result.scalars().all())


@router.get("/roles", response_model=List[RoleOut])
async def list_roles(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all roles and their assigned permissions"""
    result = await db.execute(select(Role).order_by(Role.name))
    roles = result.scalars().all()

    output = []
    for r in roles:
        # Load permissions for this role
        perm_res = await db.execute(
            select(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id == r.id)
        )
        perm_codes = list(perm_res.scalars().all())
        output.append(
            RoleOut(
                id=r.id,
                name=r.name,
                description=r.description,
                is_system=r.is_system,
                permissions=perm_codes,
            )
        )
    return output


@router.post("/roles", response_model=RoleOut, status_code=201)
async def create_custom_role(
    payload: RoleCreateRequest,
    current_user: User = Depends(require_permission(StandardPermissions.RBAC_MANAGE)),
    db: AsyncSession = Depends(get_db)
):
    """Create a new custom institutional role (Requires RBAC_MANAGE)"""
    existing = await db.execute(select(Role).where(Role.name == payload.name.lower()))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role with name '{payload.name}' already exists."
        )

    new_role = Role(
        name=payload.name.lower(),
        description=payload.description,
        is_system=False,
    )
    db.add(new_role)
    await db.commit()
    await db.refresh(new_role)

    # Attach requested permissions
    assigned_codes = []
    if payload.permission_codes:
        perms = await db.execute(
            select(Permission).where(Permission.code.in_(payload.permission_codes))
        )
        for p in perms.scalars().all():
            db.add(RolePermission(role_id=new_role.id, permission_id=p.id))
            assigned_codes.append(p.code)
        await db.commit()

    return RoleOut(
        id=new_role.id,
        name=new_role.name,
        description=new_role.description,
        is_system=new_role.is_system,
        permissions=assigned_codes,
    )


@router.post("/roles/{role_id}/permissions", response_model=RoleOut)
async def assign_role_permissions(
    role_id: int,
    payload: RolePermissionUpdateRequest,
    current_user: User = Depends(require_permission(StandardPermissions.RBAC_MANAGE)),
    db: AsyncSession = Depends(get_db)
):
    """Assign or update permissions on an institutional role (Requires RBAC_MANAGE)"""
    role_res = await db.execute(select(Role).where(Role.id == role_id))
    role = role_res.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    # Clear existing role permissions
    existing_rp = await db.execute(select(RolePermission).where(RolePermission.role_id == role_id))
    for rp in existing_rp.scalars().all():
        await db.delete(rp)

    # Add new permissions
    assigned_codes = []
    if payload.permission_codes:
        perms = await db.execute(
            select(Permission).where(Permission.code.in_(payload.permission_codes))
        )
        for p in perms.scalars().all():
            db.add(RolePermission(role_id=role.id, permission_id=p.id))
            assigned_codes.append(p.code)

    await db.commit()
    return RoleOut(
        id=role.id,
        name=role.name,
        description=role.description,
        is_system=role.is_system,
        permissions=assigned_codes,
    )


@router.get("/my-permissions", response_model=UserPermissionsResponse)
async def get_my_permissions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns the authenticated user's computed permission list"""
    perms = await get_user_permissions(current_user, db)
    role_str = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    return UserPermissionsResponse(
        user_id=current_user.id,
        role=role_str,
        permissions=sorted(list(perms)),
    )
