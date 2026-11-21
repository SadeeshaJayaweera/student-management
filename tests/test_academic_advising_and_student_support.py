"""
NSBM EduSphere — Academic Advising and Student Support Tests
Validates advisor assignments, advising session workflows, confidentiality masking,
and student support intervention case management.
"""
import pytest
from datetime import datetime, date, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import (
    User, UserRole, Institution, Campus, Program, Faculty, Department,
    Student, Lecturer, AcademicAdvisorAssignment, AdvisingSession,
    StudentSupportCase, SupportCaseNote
)
from backend.utils.security import create_access_token, hash_password


@pytest.fixture
async def advising_infra_fixture(test_session: AsyncSession):
    """Sets up institution, advisor, student, and users for advising tests"""
    inst = Institution(name="NSBM University", code="NSBM-ADV", is_active=True)
    test_session.add(inst)
    await test_session.commit()
    await test_session.refresh(inst)

    # Users: Admin, Lecturer (Advisor), Student 1, Student 2
    admin_u = User(username="admin_adv", email="admin_adv@nsbm.ac.lk", full_name="Dean of Students", hashed_password=hash_password("Pass@123"), role=UserRole.ADMIN, institution_id=inst.id, is_active=True)
    advisor_u = User(username="prof_advisor", email="advisor@nsbm.ac.lk", full_name="Dr. Advisor", hashed_password=hash_password("Pass@123"), role=UserRole.LECTURER, institution_id=inst.id, is_active=True)
    s1_u = User(username="adv_student1", email="student1@nsbm.ac.lk", full_name="Advised Student 1", hashed_password=hash_password("Pass@123"), role=UserRole.STUDENT, institution_id=inst.id, is_active=True)
    s2_u = User(username="adv_student2", email="student2@nsbm.ac.lk", full_name="Other Student 2", hashed_password=hash_password("Pass@123"), role=UserRole.STUDENT, institution_id=inst.id, is_active=True)
    test_session.add_all([admin_u, advisor_u, s1_u, s2_u])
    await test_session.commit()
    for u in [admin_u, advisor_u, s1_u, s2_u]:
        await test_session.refresh(u)

    lec = Lecturer(user_id=advisor_u.id, institution_id=inst.id, lecturer_id="ADV-LEC-01", faculty="Computing", department="SE")
    s1 = Student(user_id=s1_u.id, institution_id=inst.id, student_id="ADV-STU-01", faculty="Computing", department="SE", program="BSc SE", year_of_study=1, semester=1)
    s2 = Student(user_id=s2_u.id, institution_id=inst.id, student_id="ADV-STU-02", faculty="Computing", department="SE", program="BSc SE", year_of_study=1, semester=1)
    test_session.add_all([lec, s1, s2])
    await test_session.commit()
    await test_session.refresh(lec)
    await test_session.refresh(s1)
    await test_session.refresh(s2)

    return {
        "inst": inst,
        "advisor": lec,
        "s1": s1,
        "s2": s2,
        "admin_token": create_access_token({"sub": str(admin_u.id), "role": admin_u.role.value}),
        "advisor_token": create_access_token({"sub": str(advisor_u.id), "role": advisor_u.role.value}),
        "s1_token": create_access_token({"sub": str(s1_u.id), "role": s1_u.role.value}),
        "s2_token": create_access_token({"sub": str(s2_u.id), "role": s2_u.role.value}),
    }


@pytest.mark.asyncio
async def test_advisor_assignment_and_rbac(client: AsyncClient, advising_infra_fixture):
    """Verifies advisor assignments and RBAC restrictions"""
    f = advising_infra_fixture

    payload = {
        "student_id": f["s1"].id,
        "lecturer_id": f["advisor"].id,
        "advising_type": "academic"
    }

    # Student cannot assign advisor -> 403 Forbidden
    res = await client.post(
        "/api/advising/assignments",
        json=payload,
        headers={"Authorization": f"Bearer {f['s1_token']}"}
    )
    assert res.status_code == 403

    # Admin assigns advisor -> 201 Created
    res = await client.post(
        "/api/advising/assignments",
        json=payload,
        headers={"Authorization": f"Bearer {f['admin_token']}"}
    )
    assert res.status_code == 201
    assert res.json()["advising_type"] == "academic"

    # Student queries assignments -> receives their assigned advisor
    list_res = await client.get(
        "/api/advising/assignments",
        headers={"Authorization": f"Bearer {f['s1_token']}"}
    )
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1
    assert list_res.json()[0]["lecturer_id"] == f["advisor"].id


@pytest.mark.asyncio
async def test_advising_sessions_and_confidential_notes_masking(client: AsyncClient, advising_infra_fixture):
    """
    Verifies:
    - Scheduling advising sessions.
    - Confidential notes are visible to the advisor/admin.
    - Confidential notes are masked (None) when viewed by the student.
    - Unauthorized students cannot view peer advising sessions (403).
    """
    f = advising_infra_fixture

    sched_time = (datetime.utcnow() + timedelta(days=2)).isoformat()
    session_payload = {
        "student_id": f["s1"].id,
        "lecturer_id": f["advisor"].id,
        "scheduled_at": sched_time,
        "duration_minutes": 45,
        "session_type": "one_on_one",
        "topic": "Academic Progress & Specialization Selection",
        "student_notes": "Discussed choosing Software Architecture as elective.",
        "confidential_notes": "Student struggling with math module; monitor for probation warning.",
        "action_items": [{"task": "Register for tutoring", "due": "2026-03-01"}]
    }

    # Advisor schedules session with confidential notes -> 201 Created
    res = await client.post(
        "/api/advising/sessions",
        json=session_payload,
        headers={"Authorization": f"Bearer {f['advisor_token']}"}
    )
    assert res.status_code == 201
    session_id = res.json()["id"]

    # 1. Advisor queries session -> confidential_notes is present
    advisor_view = await client.get(
        f"/api/advising/sessions/{session_id}",
        headers={"Authorization": f"Bearer {f['advisor_token']}"}
    )
    assert advisor_view.status_code == 200
    assert advisor_view.json()["confidential_notes"] == "Student struggling with math module; monitor for probation warning."
    assert advisor_view.json()["student_notes"] == "Discussed choosing Software Architecture as elective."

    # 2. Student queries their own session -> confidential_notes is None (masked)
    student_view = await client.get(
        f"/api/advising/sessions/{session_id}",
        headers={"Authorization": f"Bearer {f['s1_token']}"}
    )
    assert student_view.status_code == 200
    assert student_view.json()["confidential_notes"] is None
    assert student_view.json()["student_notes"] == "Discussed choosing Software Architecture as elective."

    # 3. Unrelated student tries to view session -> 403 Forbidden
    other_view = await client.get(
        f"/api/advising/sessions/{session_id}",
        headers={"Authorization": f"Bearer {f['s2_token']}"}
    )
    assert other_view.status_code == 403


@pytest.mark.asyncio
async def test_student_support_cases_and_notes(client: AsyncClient, advising_infra_fixture):
    """
    Verifies:
    - Staff creates support intervention case.
    - Confidential notes are excluded when student lists notes.
    - Status transitions and resolution tracking.
    """
    f = advising_infra_fixture

    case_payload = {
        "student_id": f["s1"].id,
        "category": "academic_probation",
        "priority": "high",
        "title": "Attendance Warning & Academic Probation Alert",
        "description": "Student attendance in SE101 dropped below 75% threshold."
    }

    # Staff opens support case
    res = await client.post(
        "/api/advising/cases",
        json=case_payload,
        headers={"Authorization": f"Bearer {f['advisor_token']}"}
    )
    assert res.status_code == 201
    case_data = res.json()
    assert case_data["status"] == "open"
    assert case_data["priority"] == "high"
    case_id = case_data["id"]

    # Staff adds a public note
    await client.post(
        f"/api/advising/cases/{case_id}/notes",
        json={"content": "Sent official attendance warning email to student.", "is_confidential": False},
        headers={"Authorization": f"Bearer {f['advisor_token']}"}
    )

    # Staff adds a confidential note
    await client.post(
        f"/api/advising/cases/{case_id}/notes",
        json={"content": "Confidential: Referred to student counselling center for personal stress.", "is_confidential": True},
        headers={"Authorization": f"Bearer {f['advisor_token']}"}
    )

    # 1. Staff queries notes -> sees both (2 notes)
    staff_notes = await client.get(
        f"/api/advising/cases/{case_id}/notes",
        headers={"Authorization": f"Bearer {f['advisor_token']}"}
    )
    assert staff_notes.status_code == 200
    assert len(staff_notes.json()) == 2

    # 2. Student queries notes -> confidential note is filtered out (1 note)
    student_notes = await client.get(
        f"/api/advising/cases/{case_id}/notes",
        headers={"Authorization": f"Bearer {f['s1_token']}"}
    )
    assert student_notes.status_code == 200
    assert len(student_notes.json()) == 1
    assert student_notes.json()[0]["is_confidential"] is False

    # 3. Staff resolves case
    resolve_res = await client.patch(
        f"/api/advising/cases/{case_id}",
        json={"status": "resolved", "resolution_summary": "Student agreed to attendance recovery contract."},
        headers={"Authorization": f"Bearer {f['admin_token']}"}
    )
    assert resolve_res.status_code == 200
    assert resolve_res.json()["status"] == "resolved"
    assert resolve_res.json()["resolved_at"] is not None
