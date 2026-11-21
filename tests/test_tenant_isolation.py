"""
NSBM EduSphere — Multi-Tenant Institution Isolation Unit & Integration Tests
Tests context-var tenant resolution, middleware header propagation,
institutional CRUD operations, and cross-tenant data isolation.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import User, UserRole, Institution, Student
from backend.core.tenant import apply_tenant_filter
from backend.utils.security import hash_password


@pytest.fixture
async def seed_institutions(test_session: AsyncSession):
    nsbm = Institution(
        code="NSBM",
        name="NSBM Green University",
        subdomain="nsbm",
        domain="nsbm.ac.lk",
        is_active=True,
        settings={"primary_color": "#006400"},
    )
    sliit = Institution(
        code="SLIIT",
        name="SLIIT Campus",
        subdomain="sliit",
        domain="sliit.lk",
        is_active=True,
        settings={"primary_color": "#000080"},
    )
    test_session.add_all([nsbm, sliit])
    await test_session.commit()
    await test_session.refresh(nsbm)
    await test_session.refresh(sliit)
    return nsbm, sliit


@pytest.mark.asyncio
async def test_tenant_middleware_resolves_and_propagates_headers(client: AsyncClient, seed_institutions):
    """Verify middleware extracts X-Institution-Code and resolves the active tenant"""
    nsbm, _ = seed_institutions

    response = await client.get(
        "/api/tenants/current",
        headers={"X-Institution-Code": "NSBM"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data is not None
    assert data["code"] == "NSBM"
    assert data["name"] == "NSBM Green University"
    assert response.headers.get("x-institution-code") == "NSBM"


@pytest.mark.asyncio
async def test_tenant_crud_and_superadmin_authorization(client: AsyncClient, test_session: AsyncSession):
    """Verify tenant provisioning is strictly guarded by Superadmin privileges"""
    # 1. Create a regular student
    student = User(
        email="tenant_student@domain.com",
        username="tenant_student",
        hashed_password=hash_password("StudentPass@123"),
        full_name="Tenant Student",
        role=UserRole.STUDENT,
        is_active=True,
    )
    # 2. Create a superadmin
    admin = User(
        email="tenant_admin@domain.com",
        username="tenant_admin",
        hashed_password=hash_password("AdminPass@123"),
        full_name="Tenant Admin",
        role=UserRole.ADMIN,
        is_active=True,
    )
    test_session.add_all([student, admin])
    await test_session.commit()

    # Student login
    stud_login = await client.post(
        "/api/auth/login",
        data={"username": "tenant_student", "password": "StudentPass@123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    stud_token = stud_login.json()["access_token"]

    # Student attempting to provision a new institution is rejected (403 Forbidden)
    forbidden_resp = await client.post(
        "/api/tenants",
        json={"code": "UOC", "name": "University of Colombo"},
        headers={"Authorization": f"Bearer {stud_token}"},
    )
    assert forbidden_resp.status_code == 403

    # Admin login
    admin_login = await client.post(
        "/api/auth/login",
        data={"username": "tenant_admin", "password": "AdminPass@123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Admin provisions a new institution -> 201 Created
    create_resp = await client.post(
        "/api/tenants",
        json={"code": "UOC", "name": "University of Colombo", "subdomain": "uoc"},
        headers=admin_headers,
    )
    assert create_resp.status_code == 201
    assert create_resp.json()["code"] == "UOC"


@pytest.mark.asyncio
async def test_tenant_data_isolation_filter(test_session: AsyncSession, seed_institutions):
    """Verify apply_tenant_filter restricts data retrieval exclusively to designated institution"""
    nsbm, sliit = seed_institutions

    # User 1 at NSBM
    u1 = User(
        email="user_nsbm@nsbm.ac.lk",
        username="user_nsbm",
        hashed_password="pw",
        full_name="NSBM Student",
        institution_id=nsbm.id,
    )
    # User 2 at SLIIT
    u2 = User(
        email="user_sliit@sliit.lk",
        username="user_sliit",
        hashed_password="pw",
        full_name="SLIIT Student",
        institution_id=sliit.id,
    )
    test_session.add_all([u1, u2])
    await test_session.commit()

    # Query with NSBM tenant filter
    nsbm_query = apply_tenant_filter(select(User), User, tenant_id=nsbm.id)
    nsbm_results = (await test_session.execute(nsbm_query)).scalars().all()
    nsbm_usernames = [u.username for u in nsbm_results]
    assert "user_nsbm" in nsbm_usernames
    assert "user_sliit" not in nsbm_usernames

    # Query with SLIIT tenant filter
    sliit_query = apply_tenant_filter(select(User), User, tenant_id=sliit.id)
    sliit_results = (await test_session.execute(sliit_query)).scalars().all()
    sliit_usernames = [u.username for u in sliit_results]
    assert "user_sliit" in sliit_usernames
    assert "user_nsbm" not in sliit_usernames
