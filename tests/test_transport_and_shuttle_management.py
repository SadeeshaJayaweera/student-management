from datetime import date, datetime
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import User, UserRole, Student
from backend.utils.security import hash_password, create_access_token


@pytest.mark.asyncio
async def test_transport_and_shuttle_management(
    client: AsyncClient,
    test_session: AsyncSession
):
    # 1. Setup Admin and Student users
    admin_user = User(
        email="transport_admin@nsbm.ac.lk",
        username="transport_admin",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Fleet Director Gunawardena",
        role=UserRole.ADMIN,
        is_active=True,
    )
    student_user = User(
        email="commuter_stu@nsbm.ac.lk",
        username="commuter_stu",
        hashed_password=hash_password("StuPass123!"),
        full_name="Ruwan Dissanayake",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add_all([admin_user, student_user])
    await test_session.commit()

    student = Student(
        user_id=student_user.id,
        student_id="STU-BUS-01",
        faculty="Computing",
        department="Information Systems",
        program="BSc Information Systems",
        year_of_study=3,
        semester=1,
        gpa=3.6,
        credits_earned=72,
    )
    test_session.add(student)
    await test_session.commit()

    admin_token = create_access_token({"sub": str(admin_user.id), "role": "admin"})
    student_token = create_access_token({"sub": str(student_user.id), "role": "student"})

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    student_headers = {"Authorization": f"Bearer {student_token}"}

    # 2. Admin registers a transport fleet vehicle
    vehicle_payload = {
        "vehicle_number": "WP ND-4821",
        "vehicle_type": "bus",
        "capacity": 54,
        "driver_name": "K. Somapala",
        "driver_contact": "+94 77 456 7890",
        "status": "active",
    }
    veh_res = await client.post("/api/transport/vehicles", json=vehicle_payload, headers=admin_headers)
    assert veh_res.status_code == 201
    veh_data = veh_res.json()
    assert veh_data["vehicle_number"] == "WP ND-4821"
    assert veh_data["capacity"] == 54
    vehicle_id = veh_data["id"]

    # 3. Admin creates a Shuttle Route with stops
    route_payload = {
        "route_name": "Colombo Fort - NSBM Express Shuttle",
        "route_code": "RT-CMB-01",
        "origin": "Colombo Fort Railway Station",
        "destination": "NSBM Green University, Homagama",
        "distance_km": 28.5,
        "estimated_duration_mins": 55,
        "fare_amount": 180.0,
        "is_active": True,
        "stops": [
            {
                "stop_name": "Nugegoda Supermarket Junction",
                "stop_order": 1,
                "latitude": 6.8715,
                "longitude": 79.8970,
                "estimated_time_offset_mins": 20,
            },
            {
                "stop_name": "Maharagama Clock Tower",
                "stop_order": 2,
                "latitude": 6.8480,
                "longitude": 79.9265,
                "estimated_time_offset_mins": 35,
            },
        ],
    }
    route_res = await client.post("/api/transport/routes", json=route_payload, headers=admin_headers)
    assert route_res.status_code == 201
    route_data = route_res.json()
    assert route_data["route_code"] == "RT-CMB-01"
    assert len(route_data["stops"]) == 2
    route_id = route_data["id"]

    # 4. Admin adds an additional intermediate stop
    new_stop_payload = {
        "stop_name": "Kottawa Highway Interchange",
        "stop_order": 3,
        "latitude": 6.8400,
        "longitude": 79.9650,
        "estimated_time_offset_mins": 45,
    }
    stop_res = await client.post(f"/api/transport/routes/{route_id}/stops", json=new_stop_payload, headers=admin_headers)
    assert stop_res.status_code == 201
    assert stop_res.json()["stop_name"] == new_stop_payload["stop_name"]

    # 5. Admin adds scheduled departures to the timetable
    sched_payload = {
        "route_id": route_id,
        "vehicle_id": vehicle_id,
        "departure_time": "07:15",
        "arrival_time": "08:10",
        "days_of_week": ["monday", "tuesday", "wednesday", "thursday", "friday"],
        "shift_type": "morning_inbound",
        "is_active": True,
    }
    sched_res = await client.post("/api/transport/schedules", json=sched_payload, headers=admin_headers)
    assert sched_res.status_code == 201
    sched_data = sched_res.json()
    assert sched_data["departure_time"] == "07:15"
    assert sched_data["vehicle_number"] == "WP ND-4821"

    # 6. Query routes and schedules
    routes_list = await client.get("/api/transport/routes", headers=student_headers)
    assert routes_list.status_code == 200
    assert any(r["id"] == route_id for r in routes_list.json())

    sched_list = await client.get(f"/api/transport/schedules?route_id={route_id}", headers=student_headers)
    assert sched_list.status_code == 200
    assert len(sched_list.json()) >= 1

    # 7. Update vehicle GPS telemetry
    telemetry_payload = {"current_lat": 6.8450, "current_lng": 79.9300}
    tel_res = await client.put(f"/api/transport/vehicles/{vehicle_id}/telemetry", json=telemetry_payload, headers=admin_headers)
    assert tel_res.status_code == 200
    assert tel_res.json()["current_lat"] == 6.8450

    # 8. Admin issues a digital student transit pass
    pass_payload = {
        "student_id": student.id,
        "route_id": route_id,
        "pass_type": "semester",
        "valid_from": str(date.today()),
        "valid_until": "2027-06-30",
        "fare_paid": 14000.0,
    }
    pass_res = await client.post("/api/transport/passes", json=pass_payload, headers=admin_headers)
    assert pass_res.status_code == 201
    pass_data = pass_res.json()
    assert pass_data["student_id"] == student.id
    assert pass_data["status"] == "active"
    assert pass_data["qr_code_token"].startswith("PASS-")

    # 9. Student queries their active transit pass
    my_pass = await client.get("/api/transport/passes/my", headers=student_headers)
    assert my_pass.status_code == 200
    assert my_pass.json()["route_id"] == route_id
    assert my_pass.json()["route_code"] == "RT-CMB-01"

    # 10. Query fleet operational summary
    summary_res = await client.get("/api/transport/summary", headers=student_headers)
    assert summary_res.status_code == 200
    sum_data = summary_res.json()
    assert sum_data["total_vehicles"] >= 1
    assert sum_data["total_routes"] >= 1
    assert sum_data["active_schedules"] >= 1
    assert sum_data["active_passes"] >= 1
    assert sum_data["fleet_capacity"] >= 54
