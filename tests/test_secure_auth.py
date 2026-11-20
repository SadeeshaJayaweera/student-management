"""
NSBM EduSphere — Secure Authentication Architecture Unit & Integration Tests
Verifies privilege escalation defense, password complexity, brute-force lockout, and session tracking
"""
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import User, UserSession


@pytest.mark.asyncio
async def test_privilege_escalation_in_registration_rejected(client: AsyncClient):
    """Verify attempting to self-assign elevated roles (admin, lecturer) is strictly rejected"""
    payload = {
        "email": "hacker@domain.com",
        "username": "fakeadmin",
        "password": "SecurePassword@123",
        "full_name": "Fake Admin",
        "role": "admin",
    }
    response = await client.post("/api/auth/register", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert "Elevated roles" in data["detail"]


@pytest.mark.asyncio
async def test_weak_password_rejected(client: AsyncClient):
    """Verify weak passwords failing complexity policy are rejected"""
    # Test password missing uppercase and digit
    payload = {
        "email": "student_weak@nsbm.ac.lk",
        "username": "weakpwdstudent",
        "password": "onlylowercase!",
        "full_name": "Weak Pwd Student",
        "role": "student",
    }
    response = await client.post("/api/auth/register", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert "uppercase" in data["detail"].lower()


@pytest.mark.asyncio
async def test_brute_force_account_lockout(client: AsyncClient, seeded_user, test_session: AsyncSession):
    """Verify that 5 consecutive failed login attempts lock the user account"""
    # 5 failed login attempts
    for i in range(5):
        resp = await client.post(
            "/api/auth/login",
            data={"username": "teststudent", "password": "WrongPassword123!"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code == 401

    # Verify user is now locked in DB
    result = await test_session.execute(select(User).where(User.username == "teststudent"))
    user = result.scalar_one()
    assert user.failed_login_attempts >= 5
    assert user.locked_until is not None

    # 6th attempt (even with valid password) should be rejected due to account lockout
    locked_resp = await client.post(
        "/api/auth/login",
        data={"username": "teststudent", "password": "Student@123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert locked_resp.status_code == 401
    assert "locked" in locked_resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_session_created_on_successful_login(client: AsyncClient, seeded_user, test_session: AsyncSession):
    """Verify an active UserSession record is stored upon successful authentication"""
    response = await client.post(
        "/api/auth/login",
        data={"username": "teststudent", "password": "Student@123"},
        headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "TestBrowser/1.0"},
    )
    assert response.status_code == 200

    # Query active session
    sess_result = await test_session.execute(
        select(UserSession).where(UserSession.user_id == seeded_user.id)
    )
    sessions = sess_result.scalars().all()
    assert len(sessions) >= 1
    assert sessions[0].is_active is True
    assert sessions[0].user_agent == "TestBrowser/1.0"
