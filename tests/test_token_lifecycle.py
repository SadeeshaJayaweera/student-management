"""
NSBM EduSphere — Token & Session Lifecycle Unit & Integration Tests
Tests cryptographic refresh token rotation, replay detection attack defense,
active session tracking, and single/all session termination.
"""
from datetime import datetime, timedelta, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import User, UserSession, RefreshToken
from backend.utils.security import create_refresh_token, hash_token


@pytest.mark.asyncio
async def test_login_returns_token_pair_with_refresh_token(client: AsyncClient, seeded_user):
    """Verify login provides access_token and refresh_token with expiration info"""
    response = await client.post(
        "/api/auth/login",
        data={"username": "teststudent", "password": "Student@123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0
    assert data["role"] == "student"


@pytest.mark.asyncio
async def test_refresh_token_rotation_success(client: AsyncClient, seeded_user, test_session: AsyncSession):
    """Verify refresh token rotation returns a new token pair and revokes the old refresh token"""
    # 1. Login to get initial tokens
    login_resp = await client.post(
        "/api/auth/login",
        data={"username": "teststudent", "password": "Student@123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    initial_tokens = login_resp.json()
    first_refresh = initial_tokens["refresh_token"]

    # 2. Use refresh token to rotate
    refresh_resp = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": first_refresh},
    )
    assert refresh_resp.status_code == 200
    rotated_tokens = refresh_resp.json()
    second_refresh = rotated_tokens["refresh_token"]
    assert second_refresh != first_refresh
    assert "access_token" in rotated_tokens

    # 3. Check DB state: first token must be revoked and have replaced_by set
    first_hash = hash_token(first_refresh)
    res = await test_session.execute(
        select(RefreshToken).where(RefreshToken.token_hash == first_hash)
    )
    first_record = res.scalar_one()
    assert first_record.is_revoked is True
    assert first_record.replaced_by is not None


@pytest.mark.asyncio
async def test_replay_attack_detection_invalidates_token_family(
    client: AsyncClient, seeded_user, test_session: AsyncSession
):
    """
    CRITICAL SECURITY TEST:
    If an attacker or rogue client reuses an already-rotated (revoked) refresh token,
    EduSphere must detect the replay attack, immediately invalidate all tokens
    in that token family, and deactivate associated sessions.
    """
    # 1. Login
    login_resp = await client.post(
        "/api/auth/login",
        data={"username": "teststudent", "password": "Student@123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    initial_tokens = login_resp.json()
    stolen_first_token = initial_tokens["refresh_token"]

    # 2. Legitimate user rotates token
    legit_refresh_resp = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": stolen_first_token},
    )
    assert legit_refresh_resp.status_code == 200
    second_tokens = legit_refresh_resp.json()
    legit_second_token = second_tokens["refresh_token"]

    # 3. Attacker attempts to replay the stolen (already rotated) first token!
    replay_resp = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": stolen_first_token},
    )
    assert replay_resp.status_code == 401
    assert "reuse detected" in replay_resp.json()["detail"].lower()

    # 4. Verify that the entire family (including legitimate second token) is now revoked
    second_hash = hash_token(legit_second_token)
    res = await test_session.execute(
        select(RefreshToken).where(RefreshToken.token_hash == second_hash)
    )
    second_record = res.scalar_one()
    assert second_record.is_revoked is True

    # 5. Subsequent attempts by anyone in this family must fail
    fail_resp = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": legit_second_token},
    )
    assert fail_resp.status_code == 401


@pytest.mark.asyncio
async def test_active_sessions_listing_and_revocation(
    client: AsyncClient, seeded_user, test_session: AsyncSession
):
    """Verify session management: listing active sessions and terminating a specific session"""
    # 1. Login to establish session
    login_resp = await client.post(
        "/api/auth/login",
        data={"username": "teststudent", "password": "Student@123"},
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "MacChrome/120.0",
        },
    )
    token = login_resp.json()["access_token"]
    auth_header = {"Authorization": f"Bearer {token}"}

    # 2. List sessions
    sessions_resp = await client.get("/api/auth/sessions", headers=auth_header)
    assert sessions_resp.status_code == 200
    sessions = sessions_resp.json()
    assert len(sessions) >= 1
    session_id = sessions[0]["id"]
    assert sessions[0]["is_active"] is True

    # 3. Terminate the session
    delete_resp = await client.delete(f"/api/auth/sessions/{session_id}", headers=auth_header)
    assert delete_resp.status_code == 200

    # 4. Verify in DB that session is inactive
    db_sess = await test_session.execute(
        select(UserSession).where(UserSession.id == session_id)
    )
    record = db_sess.scalar_one()
    assert record.is_active is False


@pytest.mark.asyncio
async def test_logout_and_logout_all(client: AsyncClient, seeded_user, test_session: AsyncSession):
    """Verify logout revokes current session and logout-all terminates all user sessions"""
    # 1. Login twice to create 2 active sessions
    login1 = await client.post(
        "/api/auth/login",
        data={"username": "teststudent", "password": "Student@123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token1 = login1.json()["access_token"]

    login2 = await client.post(
        "/api/auth/login",
        data={"username": "teststudent", "password": "Student@123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token2 = login2.json()["access_token"]
    refresh2 = login2.json()["refresh_token"]

    # 2. Call logout for session 2
    logout_resp = await client.post(
        "/api/auth/logout",
        json={"refresh_token": refresh2},
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert logout_resp.status_code == 200

    # Verify refresh2 is revoked
    h2 = hash_token(refresh2)
    res = await test_session.execute(
        select(RefreshToken).where(RefreshToken.token_hash == h2)
    )
    assert res.scalar_one().is_revoked is True

    # 3. Call logout-all
    logout_all_resp = await client.post(
        "/api/auth/logout-all",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert logout_all_resp.status_code == 200

    # Verify all sessions for this user are inactive
    all_sess = await test_session.execute(
        select(UserSession).where(
            UserSession.user_id == seeded_user.id,
            UserSession.is_active == True,
        )
    )
    assert len(all_sess.scalars().all()) == 0
