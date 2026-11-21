"""
NSBM EduSphere — Security Audit Trail Service
Provides asynchronous, tamper-resistant logging of critical security,
authentication, authorization, and administrative events.
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import AuditLog, AuditSeverity
from backend.core.logging import logger


class AuditEventType:
    # Authentication & Session
    AUTH_LOGIN_SUCCESS = "AUTH_LOGIN_SUCCESS"
    AUTH_LOGIN_FAILED = "AUTH_LOGIN_FAILED"
    AUTH_LOCKOUT = "AUTH_LOCKOUT"
    AUTH_MFA_SETUP = "AUTH_MFA_SETUP"
    AUTH_MFA_VERIFIED = "AUTH_MFA_VERIFIED"
    AUTH_MFA_DISABLED = "AUTH_MFA_DISABLED"
    AUTH_LOGOUT = "AUTH_LOGOUT"
    AUTH_LOGOUT_ALL = "AUTH_LOGOUT_ALL"
    AUTH_SESSION_REVOKED = "AUTH_SESSION_REVOKED"
    AUTH_PASSWORD_CHANGED = "AUTH_PASSWORD_CHANGED"

    # Account Lifecycle
    ACCOUNT_INVITATION_ISSUED = "ACCOUNT_INVITATION_ISSUED"
    ACCOUNT_ACTIVATED = "ACCOUNT_ACTIVATED"
    ACCOUNT_PASSWORD_RESET_REQUESTED = "ACCOUNT_PASSWORD_RESET_REQUESTED"
    ACCOUNT_PASSWORD_RESET_COMPLETED = "ACCOUNT_PASSWORD_RESET_COMPLETED"
    ACCOUNT_SUSPENDED = "ACCOUNT_SUSPENDED"
    ACCOUNT_REACTIVATED = "ACCOUNT_REACTIVATED"

    # Authorization & Governance
    ROLE_CREATED = "ROLE_CREATED"
    ROLE_PERMISSIONS_UPDATED = "ROLE_PERMISSIONS_UPDATED"
    ROLE_ASSIGNED = "ROLE_ASSIGNED"
    PERMISSION_DENIED = "PERMISSION_DENIED"

    # Data Mutations & System
    TENANT_PROVISIONED = "TENANT_PROVISIONED"
    TENANT_UPDATED = "TENANT_UPDATED"
    DATA_MUTATION = "DATA_MUTATION"


async def log_audit_event(
    db: AsyncSession,
    event_type: str,
    severity: AuditSeverity = AuditSeverity.INFO,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    institution_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> Optional[AuditLog]:
    """
    Records an immutable audit event to the database and structured system logs.
    Designed to be fail-safe: failures during audit trail generation are caught
    and logged without crashing the primary business operation.
    """
    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        audit_entry = AuditLog(
            timestamp=now,
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            username=username,
            institution_id=institution_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            correlation_id=correlation_id,
            details=details or {},
        )
        db.add(audit_entry)
        await db.commit()
        await db.refresh(audit_entry)

        logger.info(
            f"[AUDIT] {severity.value} | {event_type} | User: {username or user_id} | Resource: {resource_type}:{resource_id}"
        )
        return audit_entry
    except Exception as err:
        logger.error(f"Failed to record audit trail entry for event {event_type}: {str(err)}")
        return None
