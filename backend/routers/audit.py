"""
NSBM EduSphere — Security Audit Logs Router
Exposes queryable audit trail endpoints for institutional compliance and forensics.
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database import get_db
from backend.models import AuditLog, User, AuditSeverity
from backend.schemas import AuditLogOut
from backend.core.dependencies import get_current_user
from backend.core.rbac import StandardPermissions, require_permission

router = APIRouter(prefix="/api/audit-logs", tags=["Security Audit Trail"])


@router.get("", response_model=List[AuditLogOut])
async def list_audit_logs(
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    username: Optional[str] = None,
    resource_type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_permission(StandardPermissions.AUDIT_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Query immutable security audit trails with filtering and pagination (Requires AUDIT_READ)"""
    query = select(AuditLog)

    if event_type:
        query = query.where(AuditLog.event_type == event_type)
    if severity:
        try:
            sev_enum = AuditSeverity(severity.upper())
            query = query.where(AuditLog.severity == sev_enum)
        except ValueError:
            pass
    if username:
        query = query.where(AuditLog.username.ilike(f"%{username}%"))
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)

    # Restrict institutional staff to their institution, allow superadmins to view platform-wide
    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if role_val != "admin" and current_user.institution_id:
        query = query.where(AuditLog.institution_id == current_user.institution_id)

    query = query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit)
    res = await db.execute(query)
    logs = res.scalars().all()

    return [
        AuditLogOut(
            id=log.id,
            timestamp=log.timestamp,
            event_type=log.event_type,
            severity=log.severity.value if hasattr(log.severity, "value") else str(log.severity),
            user_id=log.user_id,
            username=log.username,
            institution_id=log.institution_id,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            correlation_id=log.correlation_id,
            details=log.details or {},
        )
        for log in logs
    ]


@router.get("/{audit_id}", response_model=AuditLogOut)
async def get_audit_log_by_id(
    audit_id: int,
    current_user: User = Depends(require_permission(StandardPermissions.AUDIT_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve detailed information for a specific audit log entry (Requires AUDIT_READ)"""
    res = await db.execute(select(AuditLog).where(AuditLog.id == audit_id))
    log = res.scalar_one_or_none()
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit log entry not found")

    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if role_val != "admin" and current_user.institution_id and log.institution_id != current_user.institution_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return AuditLogOut(
        id=log.id,
        timestamp=log.timestamp,
        event_type=log.event_type,
        severity=log.severity.value if hasattr(log.severity, "value") else str(log.severity),
        user_id=log.user_id,
        username=log.username,
        institution_id=log.institution_id,
        ip_address=log.ip_address,
        user_agent=log.user_agent,
        resource_type=log.resource_type,
        resource_id=log.resource_id,
        correlation_id=log.correlation_id,
        details=log.details or {},
    )
