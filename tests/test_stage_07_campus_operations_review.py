from datetime import date, datetime, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import (
    User,
    UserRole,
    Student,
    HostelBuilding,
    HostelRoom,
    TransportVehicle,
    ShuttleRoute,
    CampusFacility,
    DigitalLibraryResource,
    AthleticTeam,
    News,
    NewsCategory,
)
from backend.utils.security import hash_password, create_access_token


@pytest.mark.asyncio
async def test_stage_07_campus_operations_review(
    client: AsyncClient,
    test_session: AsyncSession
):
    # 1. Setup Administrative Executive and Student user
    admin_user = User(
        email="vice_chancellor@nsbm.ac.lk",
        username="vice_chancellor",
        hashed_password=hash_password("ExecutivePass123!"),
        full_name="Prof. E. A. Weerasinghe",
        role=UserRole.ADMIN,
        is_active=True,
    )
    student_user = User(
        email="stage7_stu@nsbm.ac.lk",
        username="stage7_stu",
        hashed_password=hash_password("StuPass123!"),
        full_name="Anura Kumara",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add_all([admin_user, student_user])
    await test_session.commit()

    student = Student(
        user_id=student_user.id,
        student_id="STU-S07-01",
        faculty="Computing",
        department="Software Engineering",
        program="BSc Software Engineering",
        year_of_study=3,
        semester=2,
        gpa=3.9,
        credits_earned=90,
    )
    test_session.add(student)
    await test_session.commit()

    admin_token = create_access_token({"sub": str(admin_user.id), "role": "admin"})
    student_token = create_access_token({"sub": str(student_user.id), "role": "student"})

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    student_headers = {"Authorization": f"Bearer {student_token}"}

    # 2. Seed Data Across Stage 07 Domains
    # Domain A: Digital Library Resource
    dig_res = DigitalLibraryResource(
        title="Autonomous Systems & Distributed Edge Networks",
        author="IEEE Computer Society",
        subject_category="Computer Science",
        resource_type="journal_article",
        file_url="https://nsbm.ac.lk/library/edge-networks.pdf",
        is_open_access=True,
        view_count=150,
        download_count=45,
    )
    test_session.add(dig_res)

    # Domain B: Athletic Team
    team = AthleticTeam(
        name="NSBM Green Dragons Rugby",
        sport_type="rugby",
        coach_name="Coach Sanath",
        captain_name="Sudeera",
        division="Inter-University Cup",
        is_active=True,
    )
    test_session.add(team)

    # Domain C: Campus News
    news = News(
        title="NSBM Smart Green Grid Recognized at World University Summit",
        slug="nsbm-smart-green-grid-summit-2026",
        content="Detailed coverage of the university zero-emission environmental campus initiatives.",
        summary="Global summit awards NSBM top honours in regional sustainability.",
        category=NewsCategory.GENERAL,
        author_id=admin_user.id,
        views=450,
        likes_count=120,
        is_published=True,
        status="published",
        target_audience="all",
        published_at=datetime.utcnow(),
    )
    test_session.add(news)

    # Domain D: Hostel Building & Room
    bldg = HostelBuilding(
        name="Anuradhapura Residence Complex",
        code="BLD-ANU",
        gender_type="mixed",
        total_floors=5,
        warden_name="Dr. Gamini",
        warden_contact="+94 77 999 8888",
        campus_location="South Residential Boulevard",
        is_active=True,
    )
    test_session.add(bldg)
    await test_session.flush()

    room = HostelRoom(
        building_id=bldg.id,
        room_number="R-302",
        floor=3,
        room_type="double",
        capacity=2,
        occupied_count=1,
        monthly_fee=18000.0,
        status="available",
    )
    test_session.add(room)

    # Domain E: Transport Vehicle & Route
    veh = TransportVehicle(
        vehicle_number="WP NB-9900",
        vehicle_type="bus",
        capacity=60,
        driver_name="Sunil Perera",
        driver_contact="+94 71 222 3333",
        status="active",
        current_lat=6.8211,
        current_lng=80.0416,
    )
    test_session.add(veh)

    route = ShuttleRoute(
        route_name="Gampaha - NSBM Express Route",
        route_code="RT-GMP-01",
        origin="Gampaha Central Bus Terminal",
        destination="NSBM Green University, Homagama",
        distance_km=42.0,
        estimated_duration_mins=70,
        fare_amount=220.0,
        is_active=True,
    )
    test_session.add(route)

    # Domain F: Campus Facility
    facility = CampusFacility(
        name="Sir Arthur C. Clarke Auditorium",
        facility_code="FAC-CLARKE-01",
        facility_type="auditorium",
        building_name="Faculty of Science & Computing",
        floor=1,
        capacity=400,
        hourly_rate=0.0,
        amenities=["High-fidelity Audio", "Projector Array"],
        is_active=True,
    )
    test_session.add(facility)
    await test_session.commit()

    # 3. Query the Unified Command Center Overview
    overview_res = await client.get("/api/campus-operations/overview", headers=admin_headers)
    assert overview_res.status_code == 200
    data = overview_res.json()
    assert data["institution_name"] == "NSBM Green University"

    # Verify Domain Telemetry Integration
    assert data["library"]["total_digital_resources"] >= 1
    assert data["athletics"]["active_teams"] >= 1
    assert data["media"]["published_articles"] >= 1
    assert data["accommodation"]["total_capacity"] >= 2
    assert data["accommodation"]["occupied_beds"] >= 1
    assert data["transport"]["fleet_vehicles"] >= 1
    assert data["transport"]["active_routes"] >= 1
    assert data["facilities"]["total_venues"] >= 1
    assert data["facilities"]["combined_capacity"] >= 400

    # 4. Query Real-Time Operational Alerts
    alerts_res = await client.get("/api/campus-operations/alerts", headers=admin_headers)
    assert alerts_res.status_code == 200
    alerts = alerts_res.json()
    assert len(alerts) >= 1
    assert any(a["id"] == "alert-system-nominal" for a in alerts)
