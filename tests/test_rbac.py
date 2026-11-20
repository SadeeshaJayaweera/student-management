"""
NSBM EduSphere — Role-Based Access Control (RBAC) Unit & Integration Tests
Tests permission resolution, default institutional role mappings,
dynamic role assignments, FastAPI permission dependency enforcement,
and RBAC management endpoints.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import User, UserRole, Role, Permission, RolePermission, UserRoleAssignment
from backend.core.rbac import (
    StandardPermissions,
    DEFAULT_ROLE_PERMISSIONS,
    get_user_permissions,
    has_permission,
)


@pytest.mark.asyncio
async def test_default_role_permissions_resolution(test_session: AsyncSession):
    """Verify built-in institutional roles receive their designed permissions"""
    student_user = User(
        email="rbac_student@nsbm.ac.lk",
        username="rbac_student",
        hashed_password="dummy",
        full_name="RBAC Student",
        role=UserRole.STUDENT,
    )
    test_session.add(student_user)
    await test_session.commit()

    # Student has courses:read and grades:read
    assert await has_permission(student_user, StandardPermissions.COURSES_READ, test_session) is True
    assert await has_permission(student_user, StandardPermissions.GRADES_READ, test_session) is True

    # Student lacks administrative and teaching permissions
    assert await has_permission(student_user, StandardPermissions.COURSES_WRITE, test_session) is False
    assert await has_permission(student_user, StandardPermissions.STUDENTS_WRITE, test_session) is False
    assert await has_permission(student_user, StandardPermissions.USERS_DELETE, test_session) is False

    # Lecturer has courses:write and grades:enter
    lecturer_user = User(
        email="rbac_lecturer@nsbm.ac.lk",
        username="rbac_lecturer",
        hashed_password="dummy",
        full_name="RBAC Lecturer",
        role=UserRole.LECTURER,
    )
    test_session.add(lecturer_user)
    await test_session.commit()

    assert await has_permission(lecturer_user, StandardPermissions.COURSES_WRITE, test_session) is True
    assert await has_permission(lecturer_user, StandardPermissions.GRADES_ENTER, test_session) is True
    assert await has_permission(lecturer_user, StandardPermissions.USERS_DELETE, test_session) is False


@pytest.mark.asyncio
async def test_admin_has_unconditional_access(test_session: AsyncSession):
    """Verify Admin role passes any permission check unconditionally"""
    admin_user = User(
        email="rbac_admin@nsbm.ac.lk",
        username="rbac_admin",
        hashed_password="dummy",
        full_name="RBAC Admin",
        role=UserRole.ADMIN,
    )
    test_session.add(admin_user)
    await test_session.commit()

    assert await has_permission(admin_user, StandardPermissions.USERS_DELETE, test_session) is True
    assert await has_permission(admin_user, StandardPermissions.RBAC_MANAGE, test_session) is True
    assert await has_permission(admin_user, "any:arbitrary:permission", test_session) is True


@pytest.mark.asyncio
async def test_dynamic_custom_role_assignment(test_session: AsyncSession):
    """Verify a user can be granted extra permissions via dynamic database role assignments"""
    user = User(
        email="advisor@nsbm.ac.lk",
        username="advisor_user",
        hashed_password="dummy",
        full_name="Academic Advisor",
        role=UserRole.STUDENT,  # Base student role
    )
    test_session.add(user)
    await test_session.commit()

    # Initially cannot export students
    assert await has_permission(user, StandardPermissions.STUDENTS_EXPORT, test_session) is False

    # Create dynamic role with students:export permission
    perm = Permission(
        code=StandardPermissions.STUDENTS_EXPORT,
        name="Export Student Data",
        module="students",
    )
    role = Role(
        name="academic_advisor",
        description="Assigned advisors with data export rights",
        is_system=False,
    )
    test_session.add_all([perm, role])
    await test_session.commit()

    # Link permission to role
    rp = RolePermission(role_id=role.id, permission_id=perm.id)
    # Link role to user
    ura = UserRoleAssignment(user_id=user.id, role_id=role.id)
    test_session.add_all([rp, ura])
    await test_session.commit()

    # User now has students:export via dynamic role
    user_perms = await get_user_permissions(user, test_session)
    assert StandardPermissions.STUDENTS_EXPORT in user_perms
    assert await has_permission(user, StandardPermissions.STUDENTS_EXPORT, test_session) is True


@pytest.mark.asyncio
async def test_rbac_api_endpoints_and_authorization(client: AsyncClient, seeded_user, test_session: AsyncSession):
    """Verify RBAC endpoints enforce proper permissions and return correct listings"""
    # 1. Login as student
    student_login = await client.post(
        "/api/auth/login",
        data={"username": "teststudent", "password": "Student@123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    student_token = student_login.json()["access_token"]
    student_headers = {"Authorization": f"Bearer {student_token}"}

    # 2. Check my-permissions endpoint for student
    my_perms_resp = await client.get("/api/rbac/my-permissions", headers=student_headers)
    assert my_perms_resp.status_code == 200
    perms_data = my_perms_resp.json()
    assert perms_data["role"] == "student"
    assert StandardPermissions.COURSES_READ in perms_data["permissions"]
    assert StandardPermissions.STUDENTS_WRITE not in perms_data["permissions"]

    # 3. Student attempting to create custom role is rejected (403 Forbidden)
    forbidden_resp = await client.post(
        "/api/rbac/roles",
        json={"name": "illegal_role", "permission_codes": ["users:delete"]},
        headers=student_headers,
    )
    assert forbidden_resp.status_code == 403
    assert "access denied" in forbidden_resp.json()["detail"].lower()

    # 4. Create admin user and verify admin can create custom role
    from backend.utils.security import hash_password
    admin = User(
        email="superadmin@nsbm.ac.lk",
        username="superadmin",
        hashed_password=hash_password("SuperAdmin@123"),
        full_name="Super Admin",
        role=UserRole.ADMIN,
        is_active=True,
    )
    test_session.add(admin)
    await test_session.commit()

    admin_login = await client.post(
        "/api/auth/login",
        data={"username": "superadmin", "password": "SuperAdmin@123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    create_role_resp = await client.post(
        "/api/rbac/roles",
        json={"name": "department_lead", "description": "Lead faculty coordinator", "permission_codes": []},
        headers=admin_headers,
    )
    assert create_role_resp.status_code == 201
    assert create_role_resp.json()["name"] == "department_lead"
