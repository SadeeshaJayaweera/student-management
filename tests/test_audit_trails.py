"""
NSBM EduSphere — Security Audit Trail Unit & Integration Tests
Tests automated recording of security events (login success, failure, lockout),
audit query endpoints with filtering, and administrative authorization guards.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import User, UserRole, AuditLog, AuditSeverity
from backend.core.audit import AuditEventType
from backend.utils.security import hash_password


@pytest.fixture
async def audit_test_users(test_session: AsyncSession):
    admin = User(
        email="auditor_admin@nsbm.ac.lk",
        username="auditor_admin",
        hashed_password=hash_password("AuditorAdmin@123"),
        full_name="Auditor Admin",
        role=UserRole.ADMIN,
        is_active=True,
    )
    student = User(
        email="audit_student@nsbm.ac.lk",
        username="audit_student",
        hashed_password=hash_password("AuditStudent@123"),
        full_name="Audit Student",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add_all([admin, student])
    await test_session.commit()
    await test_session.refresh(admin)
    await test_session.refresh(student)
    return admin, student


@pytest.mark.asyncio
async def test_authentication_events_recorded_in_audit_trail(
    client: AsyncClient, audit_test_users, test_session: AsyncSession
):
    """Verify failed login, account lockout, and successful login are recorded in audit_logs"""
    _, student = audit_test_users

    # 1. Failed login attempt
    fail_resp = await client.post(
        "/api/auth/login",
        data={"username": "audit_student", "password": "WrongPassword@999"},
        headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "AuditProbe/1.0"},
    )
    assert fail_resp.status_code == 401

    # Verify audit log entry
    res = await test_session.execute(
        select(AuditLog)
        .where(
            AuditLog.username == "audit_student",
            AuditLog.event_type == AuditEventType.AUTH_LOGIN_FAILED,
        )
        .order_by(AuditLog.timestamp.desc())
    )
    fail_log = res.scalars().first()
    assert fail_log is not None
    assert fail_log.severity == AuditSeverity.WARNING

    # 2. Trigger lockout (4 more failures)
    for _ in range(4):
        await client.post(
            "/api/auth/login",
            data={"username": "audit_student", "password": "WrongPassword@999"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    lock_res = await test_session.execute(
        select(AuditLog)
        .where(
            AuditLog.username == "audit_student",
            AuditLog.event_type == AuditEventType.AUTH_LOCKOUT,
        )
    )
    lock_log = lock_res.scalars().first()
    assert lock_log is not None
    assert lock_log.severity == AuditSeverity.CRITICAL

    # 3. Successful login (with admin)
    succ_resp = await client.post(
        "/api/auth/login",
        data={"username": "auditor_admin", "password": "AuditorAdmin@123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert succ_resp.status_code == 200

    succ_res = await test_session.execute(
        select(AuditLog)
        .where(
            AuditLog.username == "auditor_admin",
            AuditLog.event_type == AuditEventType.AUTH_LOGIN_SUCCESS,
        )
    )
    succ_log = succ_res.scalars().first()
    assert succ_log is not None
    assert succ_log.severity == AuditSeverity.INFO


@pytest.mark.asyncio
async def test_audit_logs_query_api_and_authorization(
    client: AsyncClient, audit_test_users, test_session: AsyncSession
):
    """Verify audit query endpoint enforces AUDIT_READ permission and supports filtering"""
    admin, student = audit_test_users

    # 1. Student login and attempt to view audit logs -> 403 Forbidden!
    student_login = await client.post(
        "/api/auth/login",
        data={"username": "audit_student", "password": "AuditStudent@123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    # Clear lockout on student first for clean test
    student.failed_login_attempts = 0
    student.locked_until = None
    await test_session.commit()

    student_login = await client.post(
        "/api/auth/login",
        data={"username": "audit_student", "password": "AuditStudent@123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    student_token = student_login.json()["access_token"]
    student_headers = {"Authorization": f"Bearer {student_token}"}

    forbidden_resp = await client.get("/api/audit-logs", headers=student_headers)
    assert forbidden_resp.status_code == 403

    # 2. Admin login and query audit logs -> 200 OK
    admin_login = await client.post(
        "/api/auth/login",
        data={"username": "auditor_admin", "password": "AuditorAdmin@123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    logs_resp = await client.get("/api/audit-logs", headers=admin_headers)
    assert logs_resp.status_code == 200
    logs = logs_resp.json()
    assert len(logs) >= 1
    log_id = logs[0]["id"]

    # 3. Filter by event_type
    filtered_resp = await client.get(
        f"/api/audit-logs?event_type={AuditEventType.AUTH_LOGIN_SUCCESS}",
        headers=admin_headers,
    )
    assert filtered_resp.status_code == 200
    filtered_logs = filtered_resp.json()
    for l in filtered_logs:
        assert l["event_type"] == AuditEventType.AUTH_LOGIN_SUCCESS

    # 4. Query single log entry
    single_resp = await client.get(f"/api/audit-logs/{log_id}", headers=admin_headers)
    assert single_resp.status_code == 200
    assert single_resp.json()["id"] == log_id
