"""
NSBM EduSphere — Multi-Factor Authentication (MFA) Unit & Integration Tests
Tests RFC 6238 TOTP generation, authenticator app URI provisioning,
MFA activation, backup code generation & single-use consumption,
two-step login flow, and MFA deactivation.
"""
import pyotp
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import User, UserSession


@pytest.mark.asyncio
async def test_mfa_setup_and_enable_flow(client: AsyncClient, seeded_user, test_session: AsyncSession):
    """Verify MFA setup generates secret/URI and enable activates MFA with backup codes"""
    # 1. Login to get auth token
    login_resp = await client.post(
        "/api/auth/login",
        data={"username": "teststudent", "password": "Student@123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = login_resp.json()["access_token"]
    auth_header = {"Authorization": f"Bearer {token}"}

    # 2. Setup MFA
    setup_resp = await client.post("/api/auth/mfa/setup", headers=auth_header)
    assert setup_resp.status_code == 200
    setup_data = setup_resp.json()
    assert "secret" in setup_data
    assert "otpauth://" in setup_data["provisioning_uri"]
    secret = setup_data["secret"]

    # User MFA is not active yet
    db_user = await test_session.execute(select(User).where(User.id == seeded_user.id))
    user_record = db_user.scalar_one()
    assert user_record.is_mfa_enabled is False

    # 3. Attempt enable with invalid code
    bad_enable = await client.post(
        "/api/auth/mfa/enable",
        json={"code": "000000"},
        headers=auth_header,
    )
    assert bad_enable.status_code == 400
    assert "invalid" in bad_enable.json()["detail"].lower()

    # 4. Enable with valid TOTP code
    totp = pyotp.TOTP(secret)
    valid_code = totp.now()

    enable_resp = await client.post(
        "/api/auth/mfa/enable",
        json={"code": valid_code},
        headers=auth_header,
    )
    assert enable_resp.status_code == 200
    enable_data = enable_resp.json()
    assert "backup_codes" in enable_data
    backup_codes = enable_data["backup_codes"]
    assert len(backup_codes) == 10

    # User MFA is now active
    await test_session.refresh(user_record)
    assert user_record.is_mfa_enabled is True
    assert len(user_record.mfa_backup_codes) == 10


@pytest.mark.asyncio
async def test_mfa_login_two_step_flow(client: AsyncClient, seeded_user, test_session: AsyncSession):
    """Verify login for MFA-enabled user prompts for second factor and completes with TOTP"""
    # 1. Enable MFA directly on user
    secret = pyotp.random_base32()
    seeded_user.is_mfa_enabled = True
    seeded_user.mfa_secret = secret
    seeded_user.mfa_backup_codes = []
    await test_session.commit()

    # 2. First step: login with credentials
    login_resp = await client.post(
        "/api/auth/login",
        data={"username": "teststudent", "password": "Student@123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert login_data["mfa_required"] is True
    assert "mfa_token" in login_data
    assert login_data["access_token"] is None
    mfa_token = login_data["mfa_token"]

    # 3. Second step: verify with invalid TOTP code
    bad_verify = await client.post(
        "/api/auth/mfa/verify",
        json={"mfa_token": mfa_token, "code": "999999"},
    )
    assert bad_verify.status_code == 401

    # 4. Second step: verify with valid TOTP code
    totp = pyotp.TOTP(secret)
    valid_code = totp.now()

    good_verify = await client.post(
        "/api/auth/mfa/verify",
        json={"mfa_token": mfa_token, "code": valid_code},
        headers={"User-Agent": "MFA-Client/1.0"},
    )
    assert good_verify.status_code == 200
    tokens = good_verify.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["role"] == "student"


@pytest.mark.asyncio
async def test_mfa_backup_code_login_and_single_use(
    client: AsyncClient, seeded_user, test_session: AsyncSession
):
    """Verify emergency backup recovery code allows login and is consumed upon use"""
    # 1. Setup and enable MFA via API to get real backup codes
    login_resp = await client.post(
        "/api/auth/login",
        data={"username": "teststudent", "password": "Student@123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    auth_header = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    setup_resp = await client.post("/api/auth/mfa/setup", headers=auth_header)
    secret = setup_resp.json()["secret"]

    totp = pyotp.TOTP(secret)
    enable_resp = await client.post(
        "/api/auth/mfa/enable",
        json={"code": totp.now()},
        headers=auth_header,
    )
    backup_codes = enable_resp.json()["backup_codes"]
    emergency_code = backup_codes[0]

    # 2. Login step 1: credentials
    login_step1 = await client.post(
        "/api/auth/login",
        data={"username": "teststudent", "password": "Student@123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    mfa_token = login_step1.json()["mfa_token"]

    # 3. Login step 2: use emergency backup recovery code
    verify_resp = await client.post(
        "/api/auth/mfa/verify",
        json={"mfa_token": mfa_token, "code": emergency_code},
    )
    assert verify_resp.status_code == 200
    assert "access_token" in verify_resp.json()

    # 4. Attempt to reuse the SAME backup code on next login
    login_step1_again = await client.post(
        "/api/auth/login",
        data={"username": "teststudent", "password": "Student@123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    mfa_token_again = login_step1_again.json()["mfa_token"]

    reuse_resp = await client.post(
        "/api/auth/mfa/verify",
        json={"mfa_token": mfa_token_again, "code": emergency_code},
    )
    assert reuse_resp.status_code == 401
    assert "invalid" in reuse_resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_mfa_disable_flow(client: AsyncClient, seeded_user, test_session: AsyncSession):
    """Verify disabling MFA requires password and TOTP, and restores single-factor login"""
    # 1. Enable MFA
    secret = pyotp.random_base32()
    seeded_user.is_mfa_enabled = True
    seeded_user.mfa_secret = secret
    await test_session.commit()

    # Login via MFA verify
    totp = pyotp.TOTP(secret)
    login1 = await client.post(
        "/api/auth/login",
        data={"username": "teststudent", "password": "Student@123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    mfa_tok = login1.json()["mfa_token"]
    verify = await client.post("/api/auth/mfa/verify", json={"mfa_token": mfa_tok, "code": totp.now()})
    access_token = verify.json()["access_token"]
    auth_header = {"Authorization": f"Bearer {access_token}"}

    # 2. Disable MFA with incorrect password
    bad_pw_resp = await client.post(
        "/api/auth/mfa/disable",
        json={"password": "WrongPassword123!", "code": totp.now()},
        headers=auth_header,
    )
    assert bad_pw_resp.status_code == 400

    # 3. Disable MFA with correct password and TOTP
    disable_resp = await client.post(
        "/api/auth/mfa/disable",
        json={"password": "Student@123", "code": totp.now()},
        headers=auth_header,
    )
    assert disable_resp.status_code == 200

    # 4. Verify user can now log in directly without second factor
    direct_login = await client.post(
        "/api/auth/login",
        data={"username": "teststudent", "password": "Student@123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert direct_login.status_code == 200
    data = direct_login.json()
    assert data["mfa_required"] is False
    assert data["access_token"] is not None
