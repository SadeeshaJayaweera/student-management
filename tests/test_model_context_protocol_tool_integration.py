from datetime import datetime, time
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import (
    User,
    UserRole,
    Student,
    Course,
    Grade,
    Attendance,
    AttendanceStatus,
    TimetableSlot,
)
from backend.utils.security import hash_password, create_access_token


@pytest.mark.asyncio
async def test_model_context_protocol_tool_integration(
    client: AsyncClient,
    test_session: AsyncSession
):
    # 1. Setup Admin, Student 1, and Student 2
    admin_user = User(
        email="mcp_admin@nsbm.ac.lk",
        username="mcp_admin",
        hashed_password=hash_password("AdminPass123!"),
        full_name="MCP Platform Director",
        role=UserRole.ADMIN,
        is_active=True,
    )
    student1_user = User(
        email="mcp_stu1@nsbm.ac.lk",
        username="mcp_stu1",
        hashed_password=hash_password("Stu1Pass123!"),
        full_name="Donald Knuth",
        role=UserRole.STUDENT,
        is_active=True,
    )
    student2_user = User(
        email="mcp_stu2@nsbm.ac.lk",
        username="mcp_stu2",
        hashed_password=hash_password("Stu2Pass123!"),
        full_name="Claude Shannon",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add_all([admin_user, student1_user, student2_user])
    await test_session.commit()

    stu1 = Student(
        user_id=student1_user.id,
        student_id="STU-MCP-01",
        faculty="Computing",
        department="Software Engineering",
        program="BSc (Hons) Software Engineering",
        year_of_study=3,
        semester=1,
        gpa=3.92,
        credits_earned=75,
    )
    stu2 = Student(
        user_id=student2_user.id,
        student_id="STU-MCP-02",
        faculty="Computing",
        department="Computer Science",
        program="BSc (Hons) Computer Science",
        year_of_study=3,
        semester=1,
        gpa=3.45,
        credits_earned=70,
    )
    test_session.add_all([stu1, stu2])
    await test_session.commit()

    # 2. Setup Course, Grade, Attendance, and Timetable
    course = Course(
        course_code="CS308",
        title="Distributed Systems & Cloud Computing",
        description="Scalable distributed architectures, RPC, consensus, and fault tolerance.",
        faculty="Computing",
        department="Software Engineering",
        credits=3,
        semester=1,
        year=3,
        is_active=True,
    )
    test_session.add(course)
    await test_session.commit()

    grade = Grade(
        student_id=stu1.id,
        course_id=course.id,
        midterm=38.0,
        final=55.0,
        assignments_avg=10.0,
        total=93.0,
        letter_grade="A+",
        grade_points=4.0,
        credits_earned=3,
        is_final=True,
    )
    attendance1 = Attendance(
        student_id=stu1.id,
        course_id=course.id,
        date=datetime.utcnow().date(),
        status=AttendanceStatus.PRESENT,
    )
    attendance2 = Attendance(
        student_id=stu1.id,
        course_id=course.id,
        date=datetime.utcnow().date(),
        status=AttendanceStatus.PRESENT,
    )
    timetable_slot = TimetableSlot(
        course_id=course.id,
        day_of_week=0,
        start_time="09:00",
        end_time="11:00",
        title="Distributed Systems Lecture",
        room="Lab C-302",
        slot_type="lecture",
        is_active=True,
    )
    test_session.add_all([grade, attendance1, attendance2, timetable_slot])
    await test_session.commit()

    admin_token = create_access_token({"sub": str(admin_user.id), "role": "admin"})
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    stu1_token = create_access_token({"sub": str(student1_user.id), "role": "student"})
    stu1_headers = {"Authorization": f"Bearer {stu1_token}"}

    # 3. List Registered MCP Tools
    res_tools = await client.get("/api/mcp/tools", headers=stu1_headers)
    assert res_tools.status_code == 200
    tools = res_tools.json()
    assert len(tools) >= 8
    tool_names = [t["name"] for t in tools]
    assert "lookup_student_timetable" in tool_names
    assert "get_academic_grade_summary" in tool_names
    assert "verify_student_attendance" in tool_names
    assert "check_facility_availability" in tool_names

    # 4. Student 1 executes timetable lookup for own student ID
    res_tt = await client.post(
        "/api/mcp/tools/lookup_student_timetable/execute",
        json={"arguments": {"student_id": "STU-MCP-01"}},
        headers=stu1_headers
    )
    assert res_tt.status_code == 200
    tt_data = res_tt.json()
    assert tt_data["status"] == "success"
    assert tt_data["result"]["slots_count"] >= 1
    assert tt_data["result"]["timetable"][0]["room"] == "Lab C-302"

    # 5. Student 1 executes academic grade summary for own student ID
    res_grade = await client.post(
        "/api/mcp/tools/get_academic_grade_summary/execute",
        json={"arguments": {"student_id": "STU-MCP-01"}},
        headers=stu1_headers
    )
    assert res_grade.status_code == 200
    grade_data = res_grade.json()
    assert grade_data["status"] == "success"
    assert grade_data["result"]["gpa"] == 4.0
    assert len(grade_data["result"]["records"]) == 1

    # 6. Student 1 executes attendance verification
    res_att = await client.post(
        "/api/mcp/tools/verify_student_attendance/execute",
        json={"arguments": {"student_id": "STU-MCP-01"}},
        headers=stu1_headers
    )
    assert res_att.status_code == 200
    att_data = res_att.json()
    assert att_data["status"] == "success"
    assert att_data["result"]["attendance_rate"] == 100.0
    assert att_data["result"]["eligible_for_exams"] is True

    # 7. Privacy Boundary Violation: Student 1 attempts to inspect Student 2's grades
    res_violation = await client.post(
        "/api/mcp/tools/get_academic_grade_summary/execute",
        json={"arguments": {"student_id": "STU-MCP-02"}},
        headers=stu1_headers
    )
    assert res_violation.status_code == 403
    assert "Access denied" in res_violation.json()["detail"]

    # 8. Admin executes GPA calculation utility tool
    res_calc = await client.post(
        "/api/mcp/tools/calculate_gpa/execute",
        json={
            "arguments": {
                "grades": [
                    {"letter_grade": "A+", "credits": 4},
                    {"letter_grade": "A", "credits": 3},
                    {"letter_grade": "B+", "credits": 3}
                ]
            }
        },
        headers=admin_headers
    )
    assert res_calc.status_code == 200
    calc_data = res_calc.json()
    assert calc_data["result"]["gpa"] >= 3.8
    assert "First Class" in calc_data["result"]["classification"]

    # 9. Audit Invocations Log Check
    # Student cannot view global audit log
    res_forbidden_log = await client.get("/api/mcp/invocations", headers=stu1_headers)
    assert res_forbidden_log.status_code == 403

    # Admin can view audit log
    res_admin_log = await client.get("/api/mcp/invocations", headers=admin_headers)
    assert res_admin_log.status_code == 200
    logs = res_admin_log.json()
    assert len(logs) >= 4
    tool_logged_names = [l["tool_name"] for l in logs]
    assert "lookup_student_timetable" in tool_logged_names
    assert "get_academic_grade_summary" in tool_logged_names
