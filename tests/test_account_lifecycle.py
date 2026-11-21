"""
NSBM EduSphere — Account Lifecycle Management Unit & Integration Tests
Tests invitation issuance, token-based account activation, password reset workflows,
session invalidation upon password reset, and administrative account suspension/reactivation.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import User, UserRole, UserSession, UserAccountStatus
from backend.utils.security import hash_password


@pytest.fixture
async def seeded_admin(test_session: AsyncSession):
    admin = User(
        email="lifecycle_admin@nsbm.ac.lk",
        username="lifecycle_admin",
        hashed_password=hash_password("AdminLifecycle@123"),
        full_name="Lifecycle Admin",
        role=UserRole.ADMIN,
        is_active=True,
    )
    test_session.add(admin)
    await test_session.commit()
    await test_session.refresh(admin)
    return admin


@pytest.mark.asyncio
async def test_invitation_issuance_and_acceptance_flow(client: AsyncClient, seeded_admin):
    """Verify admin can invite a user and user can activate their account with invitation token"""
    # 1. Admin login
    login_resp = await client.post(
        "/api/auth/login",
        data={"username": "lifecycle_admin", "password": "AdminLifecycle@123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    admin_token = login_resp.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Issue invitation
    invite_resp = await client.post(
        "/api/accounts/invite",
        json={"email": "new_faculty@nsbm.ac.lk", "role": "lecturer"},
        headers=admin_headers,
    )
    assert invite_resp.status_code == 201
    invite_data = invite_resp.json()
    assert invite_data["email"] == "new_faculty@nsbm.ac.lk"
    assert invite_data["status"] == "pending"
    invitation_token = invite_data["invitation_token"]
    assert invitation_token is not None

    # 3. User accepts invitation
    accept_resp = await client.post(
        "/api/accounts/accept-invitation",
        json={
            "token": invitation_token,
            "username": "new_lecturer_user",
            "password": "FacultyPassword@123",
            "full_name": "Dr. Alan Turing",
        },
    )
    assert accept_resp.status_code == 201
    user_data = accept_resp.json()
    assert user_data["username"] == "new_lecturer_user"
    assert user_data["role"] == "lecturer"
    assert user_data["is_active"] is True

    # 4. User can log in
    user_login = await client.post(
        "/api/auth/login",
        data={"username": "new_lecturer_user", "password": "FacultyPassword@123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert user_login.status_code == 200

    # 5. Attempting to accept the same invitation again fails (token already used)
    reuse_resp = await client.post(
        "/api/accounts/accept-invitation",
        json={
            "token": invitation_token,
            "username": "new_lecturer_user2",
            "password": "FacultyPassword@123",
            "full_name": "Duplicate Attempt",
        },
    )
    assert reuse_resp.status_code == 400


@pytest.mark.asyncio
async def test_password_reset_flow_and_session_invalidation(client: AsyncClient, test_session: AsyncSession):
    """Verify password reset workflow invalidates previous sessions and requires new password"""
    # 1. Create a user
    user = User(
        email="reset_target@nsbm.ac.lk",
        username="reset_target",
        hashed_password=hash_password("OldPassword@123"),
        full_name="Reset Target User",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add(user)
    await test_session.commit()

    # 2. Login to establish active session
    login1 = await client.post(
        "/api/auth/login",
        data={"username": "reset_target", "password": "OldPassword@123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    old_token = login1.json()["access_token"]
    old_headers = {"Authorization": f"Bearer {old_token}"}

    # 3. Request password reset
    forgot_resp = await client.post(
        "/api/accounts/forgot-password",
        json={"email": "reset_target@nsbm.ac.lk"},
    )
    assert forgot_resp.status_code == 200
    reset_token = forgot_resp.json()["reset_token"]

    # 4. Confirm password reset
    confirm_resp = await client.post(
        "/api/accounts/reset-password",
        json={"token": reset_token, "new_password": "NewStrongPassword@456"},
    )
    assert confirm_resp.status_code == 200

    # 5. Verify old session token no longer functions (sessions invalidated)
    sessions_check = await test_session.execute(
        select(UserSession).where(UserSession.user_id == user.id, UserSession.is_active == True)
    )
    assert len(sessions_check.scalars().all()) == 0

    # 6. Verify old password is rejected
    bad_login = await client.post(
        "/api/auth/login",
        data={"username": "reset_target", "password": "OldPassword@123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert bad_login.status_code == 401

    # 7. Login with new password succeeds
    good_login = await client.post(
        "/api/auth/login",
        data={"username": "reset_target", "password": "NewStrongPassword@456"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert good_login.status_code == 200


@pytest.mark.asyncio
async def test_account_suspension_and_reactivation_flow(
    client: AsyncClient, seeded_admin, test_session: AsyncSession
):
    """Verify administrator can suspend an account, blocking authentication, and later reactivate it"""
    # 1. Admin login
    admin_login = await client.post(
        "/api/auth/login",
        data={"username": "lifecycle_admin", "password": "AdminLifecycle@123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    # 2. Create student
    student = User(
        email="suspend_me@nsbm.ac.lk",
        username="suspend_target",
        hashed_password=hash_password("StudentPass@123"),
        full_name="Suspension Target",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add(student)
    await test_session.commit()
    await test_session.refresh(student)

    # 3. Admin suspends student
    suspend_resp = await client.post(
        f"/api/accounts/{student.id}/suspend",
        json={"reason": "Policy violation investigation"},
        headers=admin_headers,
    )
    assert suspend_resp.status_code == 200
    assert suspend_resp.json()["account_status"] == "suspended"
    assert suspend_resp.json()["is_active"] is False

    # 4. Student attempts to login -> 401 Forbidden with suspension message
    blocked_login = await client.post(
        "/api/auth/login",
        data={"username": "suspend_target", "password": "StudentPass@123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert blocked_login.status_code == 401
    assert "suspended" in blocked_login.json()["detail"].lower()

    # 5. Admin reactivates student
    reactivate_resp = await client.post(
        f"/api/accounts/{student.id}/reactivate",
        headers=admin_headers,
    )
    assert reactivate_resp.status_code == 200
    assert reactivate_resp.json()["account_status"] == "active"
    assert reactivate_resp.json()["is_active"] is True

    # 6. Student can now log in again
    ok_login = await client.post(
        "/api/auth/login",
        data={"username": "suspend_target", "password": "StudentPass@123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert ok_login.status_code == 200
