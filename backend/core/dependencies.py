"""
NSBM EduSphere — Core Security & Auth Dependencies
Standard dependency injection helpers for route authentication and authorization
"""
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db
from backend.models import User
from backend.utils.security import (
    get_current_user as _sec_get_current_user,
    require_roles as _sec_require_roles,
    get_current_student as _sec_get_current_student,
    get_current_lecturer as _sec_get_current_lecturer,
    get_current_admin as _sec_get_current_admin,
)

# Re-export core dependencies for modular access
get_current_user = _sec_get_current_user
require_roles = _sec_require_roles
get_current_student = _sec_get_current_student
get_current_lecturer = _sec_get_current_lecturer
get_current_admin = _sec_get_current_admin
