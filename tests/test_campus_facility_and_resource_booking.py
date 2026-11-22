from datetime import datetime, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import User, UserRole, Student
from backend.utils.security import hash_password, create_access_token


@pytest.mark.asyncio
async def test_campus_facility_and_resource_booking(
    client: AsyncClient,
    test_session: AsyncSession
):
    # 1. Setup Admin, Lecturer, and Student users
    admin_user = User(
        email="facilities_admin@nsbm.ac.lk",
        username="facilities_admin",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Estate & Facilities Director",
        role=UserRole.ADMIN,
        is_active=True,
    )
    lecturer_user = User(
        email="prof_turing@nsbm.ac.lk",
        username="prof_turing",
        hashed_password=hash_password("LecPass123!"),
        full_name="Prof. Alan Turing",
        role=UserRole.LECTURER,
        is_active=True,
    )
    student_user = User(
        email="club_president@nsbm.ac.lk",
        username="club_president",
        hashed_password=hash_password("StuPass123!"),
        full_name="IEEE Student Chair",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add_all([admin_user, lecturer_user, student_user])
    await test_session.commit()

    student = Student(
        user_id=student_user.id,
        student_id="STU-FAC-01",
        faculty="Computing",
        department="Software Engineering",
        program="BSc Software Engineering",
        year_of_study=3,
        semester=1,
        gpa=3.8,
        credits_earned=75,
    )
    test_session.add(student)
    await test_session.commit()

    admin_token = create_access_token({"sub": str(admin_user.id), "role": "admin"})
    lecturer_token = create_access_token({"sub": str(lecturer_user.id), "role": "lecturer"})
    student_token = create_access_token({"sub": str(student_user.id), "role": "student"})

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    lecturer_headers = {"Authorization": f"Bearer {lecturer_token}"}
    student_headers = {"Authorization": f"Bearer {student_token}"}

    # 2. Admin creates Campus Facilities
    auditorium_payload = {
        "name": "NSBM Grand Convocation Auditorium",
        "facility_code": "FAC-AUD-01",
        "facility_type": "auditorium",
        "building_name": "Main Administration & Performing Arts Complex",
        "floor": 1,
        "capacity": 800,
        "hourly_rate": 0.0,
        "amenities": ["Surround Sound", "Dual 4K Laser Displays", "Stage Lighting", "AC"],
        "is_active": True,
    }
    aud_res = await client.post("/api/facilities", json=auditorium_payload, headers=admin_headers)
    assert aud_res.status_code == 201
    aud_data = aud_res.json()
    assert aud_data["facility_code"] == "FAC-AUD-01"
    auditorium_id = aud_data["id"]

    lab_payload = {
        "name": "Ada Lovelace AI & Robotics Laboratory",
        "facility_code": "FAC-LAB-02",
        "facility_type": "computer_lab",
        "building_name": "Faculty of Computing Complex",
        "floor": 3,
        "capacity": 60,
        "hourly_rate": 0.0,
        "amenities": ["GPU Workstations", "Smart Board", "Fiber LAN"],
        "is_active": True,
    }
    lab_res = await client.post("/api/facilities", json=lab_payload, headers=admin_headers)
    assert lab_res.status_code == 201
    lab_id = lab_res.json()["id"]

    # 3. Admin catalogs Facility Equipment
    equip_payload = {
        "facility_id": auditorium_id,
        "name": "Sennheiser Wireless Mic Rig",
        "asset_tag": "EQ-MIC-001",
        "equipment_type": "wireless_mic",
        "status": "available",
    }
    eq_res = await client.post("/api/facilities/equipment", json=equip_payload, headers=admin_headers)
    assert eq_res.status_code == 201
    assert eq_res.json()["asset_tag"] == "EQ-MIC-001"

    # 4. Lecturer reserves Auditorium tomorrow from 10:00 to 12:00 -> auto confirmed
    base_time = datetime.utcnow().replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=1)
    lec_start = base_time.isoformat()
    lec_end = (base_time + timedelta(hours=2)).isoformat()

    lec_booking_payload = {
        "facility_id": auditorium_id,
        "start_time": lec_start,
        "end_time": lec_end,
        "purpose": "Faculty Research Symposium Keynote Presentation",
        "attendee_count": 250,
        "equipment_requested": ["Sennheiser Wireless Mic Rig"],
    }
    lec_res = await client.post("/api/facilities/reservations", json=lec_booking_payload, headers=lecturer_headers)
    assert lec_res.status_code == 201
    lec_data = lec_res.json()
    assert lec_data["status"] == "confirmed"
    lec_booking_id = lec_data["id"]

    # 5. Student attempts to reserve overlapping slot (11:00 to 13:00) -> 409 Conflict
    conflict_start = (base_time + timedelta(hours=1)).isoformat()
    conflict_end = (base_time + timedelta(hours=3)).isoformat()
    conflict_payload = {
        "facility_id": auditorium_id,
        "start_time": conflict_start,
        "end_time": conflict_end,
        "purpose": "Student Film Guild Screening",
        "attendee_count": 100,
    }
    conflict_res = await client.post("/api/facilities/reservations", json=conflict_payload, headers=student_headers)
    assert conflict_res.status_code == 409
    assert "conflict" in conflict_res.json()["detail"].lower()

    # 6. Student reserves Computing Lab -> status='pending'
    stu_start = (base_time + timedelta(hours=4)).isoformat()
    stu_end = (base_time + timedelta(hours=6)).isoformat()
    stu_booking_payload = {
        "facility_id": lab_id,
        "start_time": stu_start,
        "end_time": stu_end,
        "purpose": "IEEE Student Branch Machine Learning Hackathon",
        "attendee_count": 45,
    }
    stu_res = await client.post("/api/facilities/reservations", json=stu_booking_payload, headers=student_headers)
    assert stu_res.status_code == 201
    stu_data = stu_res.json()
    assert stu_data["status"] == "pending"
    stu_booking_id = stu_data["id"]

    # 7. Lecturer or Admin approves the student's booking
    appr_res = await client.put(f"/api/facilities/reservations/{stu_booking_id}", json={"status": "confirmed"}, headers=lecturer_headers)
    assert appr_res.status_code == 200
    assert appr_res.json()["status"] == "confirmed"

    # 8. Query Facilities and My Reservations
    fac_list = await client.get("/api/facilities", headers=student_headers)
    assert fac_list.status_code == 200
    assert len(fac_list.json()) >= 2

    my_res = await client.get("/api/facilities/reservations/my", headers=student_headers)
    assert my_res.status_code == 200
    assert any(r["id"] == stu_booking_id for r in my_res.json())

    # 9. Cancel a booking
    cancel_res = await client.put(f"/api/facilities/reservations/{lec_booking_id}", json={"status": "cancelled"}, headers=lecturer_headers)
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelled"

    # 10. Query facility summary
    summary_res = await client.get("/api/facilities/summary", headers=student_headers)
    assert summary_res.status_code == 200
    sum_data = summary_res.json()
    assert sum_data["total_facilities"] >= 2
    assert sum_data["total_capacity"] >= 860
    assert sum_data["total_equipment"] >= 1
