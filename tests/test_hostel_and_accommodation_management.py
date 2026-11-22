from datetime import date, datetime
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import User, UserRole, Student
from backend.utils.security import hash_password, create_access_token


@pytest.mark.asyncio
async def test_hostel_and_accommodation_management(
    client: AsyncClient,
    test_session: AsyncSession
):
    # 1. Setup Admin and Student users
    admin_user = User(
        email="hostel_warden@nsbm.ac.lk",
        username="hostel_warden",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Chief Warden Jayawardena",
        role=UserRole.ADMIN,
        is_active=True,
    )
    student1_user = User(
        email="hostel_stu1@nsbm.ac.lk",
        username="hostel_stu1",
        hashed_password=hash_password("StuPass123!"),
        full_name="Nimal Senanayake",
        role=UserRole.STUDENT,
        is_active=True,
    )
    student2_user = User(
        email="hostel_stu2@nsbm.ac.lk",
        username="hostel_stu2",
        hashed_password=hash_password("StuPass123!"),
        full_name="Sunil Perera",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add_all([admin_user, student1_user, student2_user])
    await test_session.commit()

    student1 = Student(
        user_id=student1_user.id,
        student_id="STU-HST-01",
        faculty="Computing",
        department="Software Engineering",
        program="BSc Software Engineering",
        year_of_study=2,
        semester=1,
        gpa=3.7,
        credits_earned=60,
    )
    student2 = Student(
        user_id=student2_user.id,
        student_id="STU-HST-02",
        faculty="Computing",
        department="Computer Science",
        program="BSc Computer Science",
        year_of_study=2,
        semester=1,
        gpa=3.5,
        credits_earned=58,
    )
    test_session.add_all([student1, student2])
    await test_session.commit()

    admin_token = create_access_token({"sub": str(admin_user.id), "role": "admin"})
    student1_token = create_access_token({"sub": str(student1_user.id), "role": "student"})

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    student1_headers = {"Authorization": f"Bearer {student1_token}"}

    # 2. Admin creates a Hostel Building
    bldg_payload = {
        "name": "Sigiriya Male Student Residence",
        "code": "BLD-SIG",
        "gender_type": "male",
        "total_floors": 4,
        "warden_name": "Chief Warden Jayawardena",
        "warden_contact": "+94 77 123 4567",
        "campus_location": "North Campus Quadrangle",
        "amenities": ["Wi-Fi", "Gym", "Study Lounge", "Cafeteria"],
        "is_active": True,
    }
    bldg_res = await client.post("/api/hostels/buildings", json=bldg_payload, headers=admin_headers)
    assert bldg_res.status_code == 201
    bldg_data = bldg_res.json()
    assert bldg_data["name"] == bldg_payload["name"]
    assert bldg_data["code"] == "BLD-SIG"
    bldg_id = bldg_data["id"]

    # 3. Admin creates Rooms in the building
    # Single bed room
    room1_payload = {
        "building_id": bldg_id,
        "room_number": "S-101",
        "floor": 1,
        "room_type": "single",
        "capacity": 1,
        "monthly_fee": 22000.0,
        "status": "available",
    }
    r1_res = await client.post("/api/hostels/rooms", json=room1_payload, headers=admin_headers)
    assert r1_res.status_code == 201
    room1_id = r1_res.json()["id"]

    # Double bed room
    room2_payload = {
        "building_id": bldg_id,
        "room_number": "D-201",
        "floor": 2,
        "room_type": "double",
        "capacity": 2,
        "monthly_fee": 16000.0,
        "status": "available",
    }
    r2_res = await client.post("/api/hostels/rooms", json=room2_payload, headers=admin_headers)
    assert r2_res.status_code == 201
    room2_id = r2_res.json()["id"]

    # 4. List Buildings and Rooms
    bldgs_list = await client.get("/api/hostels/buildings", headers=student1_headers)
    assert bldgs_list.status_code == 200
    assert any(b["id"] == bldg_id for b in bldgs_list.json())

    rooms_list = await client.get(f"/api/hostels/rooms?building_id={bldg_id}", headers=student1_headers)
    assert rooms_list.status_code == 200
    assert len(rooms_list.json()) == 2

    # 5. Allocate Student 1 to Single Room (S-101)
    alloc_payload = {
        "student_id": student1.id,
        "room_id": room1_id,
        "academic_year": "2025/2026",
        "semester": 1,
        "check_in_date": str(date.today()),
        "deposit_paid": 25000.0,
        "emergency_contact": "+94 71 987 6543",
        "notes": "Allocated via scholarship priority",
    }
    alloc_res = await client.post("/api/hostels/allocations", json=alloc_payload, headers=admin_headers)
    assert alloc_res.status_code == 201
    alloc_data = alloc_res.json()
    assert alloc_data["student_id"] == student1.id
    assert alloc_data["room_id"] == room1_id
    assert alloc_data["status"] == "active"
    allocation_id = alloc_data["id"]

    # Verify room is now full
    r1_check = await client.get("/api/hostels/rooms?status_filter=full", headers=admin_headers)
    assert r1_check.status_code == 200
    assert any(r["id"] == room1_id for r in r1_check.json())

    # 6. Student 1 queries own allocation
    my_alloc = await client.get("/api/hostels/allocations/my", headers=student1_headers)
    assert my_alloc.status_code == 200
    assert my_alloc.json()["room_id"] == room1_id
    assert my_alloc.json()["room_number"] == "S-101"

    # 7. Prevent double active allocation for student 1
    dup_alloc_res = await client.post("/api/hostels/allocations", json=alloc_payload, headers=admin_headers)
    assert dup_alloc_res.status_code == 400

    # 8. Prevent allocating another student to now full Single Room (S-101)
    full_alloc_payload = {
        "student_id": student2.id,
        "room_id": room1_id,
        "academic_year": "2025/2026",
        "semester": 1,
        "check_in_date": str(date.today()),
    }
    full_alloc_res = await client.post("/api/hostels/allocations", json=full_alloc_payload, headers=admin_headers)
    assert full_alloc_res.status_code == 400

    # 9. Student 1 reports maintenance ticket
    maint_payload = {
        "room_id": room1_id,
        "issue_type": "plumbing",
        "description": "Bathroom water heater thermostat not engaging",
        "priority": "high",
    }
    maint_res = await client.post("/api/hostels/maintenance", json=maint_payload, headers=student1_headers)
    assert maint_res.status_code == 201
    maint_data = maint_res.json()
    assert maint_data["room_id"] == room1_id
    assert maint_data["status"] == "reported"
    maint_id = maint_data["id"]

    # 10. Admin resolves maintenance ticket
    resolve_payload = {
        "status": "resolved",
        "resolution_notes": "Thermostat element replaced by campus electrical maintenance",
    }
    res_maint = await client.put(f"/api/hostels/maintenance/{maint_id}", json=resolve_payload, headers=admin_headers)
    assert res_maint.status_code == 200
    assert res_maint.json()["status"] == "resolved"
    assert res_maint.json()["resolved_at"] is not None

    # 11. Admin processes check-out for Student 1
    checkout_res = await client.put(f"/api/hostels/allocations/{allocation_id}", json={"status": "checked_out"}, headers=admin_headers)
    assert checkout_res.status_code == 200
    assert checkout_res.json()["status"] == "checked_out"

    # Room 1 should be vacant again
    r1_vacant = await client.get(f"/api/hostels/rooms?available_only=true", headers=admin_headers)
    assert r1_vacant.status_code == 200
    assert any(r["id"] == room1_id for r in r1_vacant.json())

    # 12. Check occupancy summary
    summary_res = await client.get("/api/hostels/summary", headers=student1_headers)
    assert summary_res.status_code == 200
    summary_data = summary_res.json()
    assert summary_data["total_buildings"] >= 1
    assert summary_data["total_rooms"] >= 2
    assert summary_data["total_capacity"] >= 3
