"""
NSBM EduSphere — Role-Based Access Control (RBAC) System
Defines granular permission constants, default institutional role mappings,
hierarchical resolution, and FastAPI permission enforcement dependencies.
"""
from typing import List, Set, Dict, Optional, Callable
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database import get_db
from backend.models import User, UserRole, Role, Permission, RolePermission, UserRoleAssignment
from backend.core.dependencies import get_current_user


class StandardPermissions:
    # Users & Auth
    USERS_READ = "users:read"
    USERS_WRITE = "users:write"
    USERS_DELETE = "users:delete"
    USERS_MANAGE_ROLES = "users:manage_roles"

    # Students Management
    STUDENTS_READ = "students:read"
    STUDENTS_WRITE = "students:write"
    STUDENTS_DELETE = "students:delete"
    STUDENTS_EXPORT = "students:export"

    # Academics, Courses & Curricula
    COURSES_READ = "courses:read"
    COURSES_WRITE = "courses:write"
    COURSES_DELETE = "courses:delete"
    GRADES_READ = "grades:read"
    GRADES_ENTER = "grades:enter"
    GRADES_PUBLISH = "grades:publish"

    # Assessments & Examinations
    EXAMS_READ = "exams:read"
    EXAMS_WRITE = "exams:write"
    EXAMS_GRADE = "exams:grade"

    # Library & Campus Services
    LIBRARY_READ = "library:read"
    LIBRARY_MANAGE = "library:manage"
    SPORTS_MANAGE = "sports:manage"
    NEWS_PUBLISH = "news:publish"

    # Governance & System
    SYSTEM_CONFIG = "system:config"
    AUDIT_READ = "audit:read"
    RBAC_MANAGE = "rbac:manage"


# Default base permissions mapped to core institutional roles
DEFAULT_ROLE_PERMISSIONS: Dict[str, Set[str]] = {
    UserRole.ADMIN.value: {
        # Super admin receives all standard permissions
        StandardPermissions.USERS_READ,
        StandardPermissions.USERS_WRITE,
        StandardPermissions.USERS_DELETE,
        StandardPermissions.USERS_MANAGE_ROLES,
        StandardPermissions.STUDENTS_READ,
        StandardPermissions.STUDENTS_WRITE,
        StandardPermissions.STUDENTS_DELETE,
        StandardPermissions.STUDENTS_EXPORT,
        StandardPermissions.COURSES_READ,
        StandardPermissions.COURSES_WRITE,
        StandardPermissions.COURSES_DELETE,
        StandardPermissions.GRADES_READ,
        StandardPermissions.GRADES_ENTER,
        StandardPermissions.GRADES_PUBLISH,
        StandardPermissions.EXAMS_READ,
        StandardPermissions.EXAMS_WRITE,
        StandardPermissions.EXAMS_GRADE,
        StandardPermissions.LIBRARY_READ,
        StandardPermissions.LIBRARY_MANAGE,
        StandardPermissions.SPORTS_MANAGE,
        StandardPermissions.NEWS_PUBLISH,
        StandardPermissions.SYSTEM_CONFIG,
        StandardPermissions.AUDIT_READ,
        StandardPermissions.RBAC_MANAGE,
    },
    UserRole.DEAN.value: {
        StandardPermissions.STUDENTS_READ,
        StandardPermissions.STUDENTS_EXPORT,
        StandardPermissions.COURSES_READ,
        StandardPermissions.COURSES_WRITE,
        StandardPermissions.GRADES_READ,
        StandardPermissions.GRADES_PUBLISH,
        StandardPermissions.EXAMS_READ,
        StandardPermissions.AUDIT_READ,
        StandardPermissions.NEWS_PUBLISH,
    },
    UserRole.REGISTRAR.value: {
        StandardPermissions.STUDENTS_READ,
        StandardPermissions.STUDENTS_WRITE,
        StandardPermissions.STUDENTS_EXPORT,
        StandardPermissions.COURSES_READ,
        StandardPermissions.GRADES_READ,
        StandardPermissions.GRADES_PUBLISH,
        StandardPermissions.AUDIT_READ,
    },
    UserRole.LECTURER.value: {
        StandardPermissions.STUDENTS_READ,
        StandardPermissions.COURSES_READ,
        StandardPermissions.COURSES_WRITE,
        StandardPermissions.GRADES_READ,
        StandardPermissions.GRADES_ENTER,
        StandardPermissions.EXAMS_READ,
        StandardPermissions.EXAMS_WRITE,
        StandardPermissions.EXAMS_GRADE,
        StandardPermissions.LIBRARY_READ,
        StandardPermissions.NEWS_PUBLISH,
    },
    UserRole.LIBRARIAN.value: {
        StandardPermissions.STUDENTS_READ,
        StandardPermissions.LIBRARY_READ,
        StandardPermissions.LIBRARY_MANAGE,
        StandardPermissions.NEWS_PUBLISH,
    },
    UserRole.STUDENT.value: {
        StandardPermissions.COURSES_READ,
        StandardPermissions.GRADES_READ,
        StandardPermissions.EXAMS_READ,
        StandardPermissions.LIBRARY_READ,
    },
    UserRole.ALUMNI.value: {
        StandardPermissions.COURSES_READ,
        StandardPermissions.LIBRARY_READ,
    },
    UserRole.GUARDIAN.value: {
        StandardPermissions.COURSES_READ,
        StandardPermissions.GRADES_READ,
    },
}


async def get_user_permissions(user: User, db: AsyncSession) -> Set[str]:
    """
    Computes the complete, resolved set of permissions for a user.
    Combines:
    1. Built-in permissions mapped to the user's primary UserRole
    2. Any custom database-assigned roles via UserRoleAssignment
    """
    role_key = user.role.value if hasattr(user.role, "value") else str(user.role)
    permissions = set(DEFAULT_ROLE_PERMISSIONS.get(role_key, set()))

    # Admin role is unconditionally omnipotent
    if role_key == UserRole.ADMIN.value:
        return permissions

    # Query dynamic role assignments from DB
    res = await db.execute(
        select(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(Role, Role.id == RolePermission.role_id)
        .join(UserRoleAssignment, UserRoleAssignment.role_id == Role.id)
        .where(UserRoleAssignment.user_id == user.id)
    )
    dynamic_permissions = res.scalars().all()
    permissions.update(dynamic_permissions)
    return permissions


async def has_permission(user: User, permission_code: str, db: AsyncSession) -> bool:
    """Checks whether the user possesses a specific permission"""
    role_key = user.role.value if hasattr(user.role, "value") else str(user.role)
    if role_key == UserRole.ADMIN.value:
        return True

    user_perms = await get_user_permissions(user, db)
    return permission_code in user_perms


def require_permission(permission_code: str) -> Callable:
    """
    FastAPI dependency that enforces a specific permission.
    Raises HTTP 403 Forbidden if current user lacks the permission.
    """
    async def dependency(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        allowed = await has_permission(current_user, permission_code, db)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: missing required permission '{permission_code}'.",
            )
        return current_user

    return dependency


def require_any_permissions(*permission_codes: str) -> Callable:
    """FastAPI dependency requiring at least one of the listed permissions"""
    async def dependency(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        user_perms = await get_user_permissions(current_user, db)
        role_key = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
        if role_key == UserRole.ADMIN.value or any(p in user_perms for p in permission_codes):
            return current_user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: requires one of [{', '.join(permission_codes)}].",
        )

    return dependency
