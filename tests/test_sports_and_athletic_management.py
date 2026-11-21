from datetime import datetime, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import User, UserRole, Student
from backend.utils.security import hash_password, create_access_token


@pytest.mark.asyncio
async def test_sports_and_athletic_management(
    client: AsyncClient,
    test_session: AsyncSession
):
    # 1. Setup Student and Coach/Admin users
    student_user = User(
        email="athlete_stu@nsbm.ac.lk",
        username="athlete_stu",
        hashed_password=hash_password("Pass123!"),
        full_name="Charith Asalanka",
        role=UserRole.STUDENT,
        is_active=True,
    )
    coach_user = User(
        email="sports_coach@nsbm.ac.lk",
        username="sports_coach",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Head Coach Jayawardene",
        role=UserRole.ADMIN,
        is_active=True,
    )
    test_session.add_all([student_user, coach_user])
    await test_session.commit()

    student = Student(
        user_id=student_user.id,
        student_id="STU-ATH-01",
        faculty="Computing",
        department="Software Engineering",
        program="BSc Software Engineering",
        year_of_study=3,
        semester=1,
        gpa=3.6,
        credits_earned=75,
    )
    test_session.add(student)
    await test_session.commit()

    student_token = create_access_token({"sub": str(student_user.id), "role": "student"})
    coach_token = create_access_token({"sub": str(coach_user.id), "role": "admin"})

    student_headers = {"Authorization": f"Bearer {student_token}"}
    coach_headers = {"Authorization": f"Bearer {coach_token}"}

    # 2. Coach creates an Athletic Team
    team_payload = {
        "name": "NSBM Green Dragons Cricket",
        "sport_type": "cricket",
        "coach_name": "Head Coach Jayawardene",
        "captain_name": "Charith Asalanka",
        "division": "Division 1",
        "home_venue": "NSBM Green Cricket Grounds",
    }
    res = await client.post("/api/athletics/teams", json=team_payload, headers=coach_headers)
    assert res.status_code == 201
    team_data = res.json()
    team_id = team_data["id"]
    assert team_data["name"] == "NSBM Green Dragons Cricket"

    # 3. Coach enlists Student Athlete into team roster
    roster_payload = {
        "student_id": student.id,
        "jersey_number": 7,
        "position_or_role": "Middle Order Batsman / Off-spin",
        "fitness_status": "fit",
    }
    res = await client.post(f"/api/athletics/teams/{team_id}/roster", json=roster_payload, headers=coach_headers)
    assert res.status_code == 201
    athlete_data = res.json()
    athlete_id = athlete_data["id"]
    assert athlete_data["jersey_number"] == 7
    assert athlete_data["student_name"] == "Charith Asalanka"

    # 4. Coach updates athlete stats after a match
    res = await client.put(
        f"/api/athletics/athletes/{athlete_id}/fitness?fitness_status=fit&matches_increment=1&points_increment=68&mvp_increment=1",
        headers=coach_headers
    )
    assert res.status_code == 200
    updated_athlete = res.json()
    assert updated_athlete["matches_played"] == 1
    assert updated_athlete["points_or_goals"] == 68
    assert updated_athlete["mvp_awards"] == 1

    # 5. Coach schedules a sports fixture
    scheduled_time = (datetime.utcnow() + timedelta(days=5)).isoformat()
    fixture_payload = {
        "team_id": team_id,
        "tournament_name": "SLUG 2026 Inter-University Championship",
        "opponent_name": "University of Colombo",
        "scheduled_time": scheduled_time,
        "venue": "NSBM Green Cricket Grounds",
        "fixture_type": "tournament",
    }
    res = await client.post("/api/athletics/fixtures", json=fixture_payload, headers=coach_headers)
    assert res.status_code == 201
    fixture_data = res.json()
    fixture_id = fixture_data["id"]
    assert fixture_data["status"] == "upcoming"

    # 6. Coach logs fixture result
    result_payload = {
        "status": "completed",
        "our_score": "184/5 (20.0 ov)",
        "opponent_score": "142/9 (20.0 ov)",
        "match_result": "won",
        "highlights": "Charith Asalanka scored 68 runs and took 2 wickets.",
    }
    res = await client.put(f"/api/athletics/fixtures/{fixture_id}/result", json=result_payload, headers=coach_headers)
    assert res.status_code == 200
    completed_fix = res.json()
    assert completed_fix["status"] == "completed"
    assert completed_fix["match_result"] == "won"

    # 7. Student books a sports facility
    start_t = datetime.utcnow() + timedelta(days=2, hours=10)
    end_t = start_t + timedelta(hours=2)
    booking_payload = {
        "facility_name": "Indoor Sports Complex",
        "team_id": team_id,
        "start_time": start_t.isoformat(),
        "end_time": end_t.isoformat(),
        "purpose": "Badminton & Conditioning Drill",
    }
    res = await client.post("/api/athletics/facility-bookings", json=booking_payload, headers=student_headers)
    assert res.status_code == 201
    b_data = res.json()
    assert b_data["facility_name"] == "Indoor Sports Complex"
    assert b_data["status"] == "confirmed"

    # 8. Test Conflict Detection: second booking on same facility and overlapping time -> 409
    overlap_payload = {
        "facility_name": "Indoor Sports Complex",
        "start_time": (start_t + timedelta(minutes=30)).isoformat(),
        "end_time": (end_t + timedelta(minutes=30)).isoformat(),
        "purpose": "Conflicting Match",
    }
    res = await client.post("/api/athletics/facility-bookings", json=overlap_payload, headers=student_headers)
    assert res.status_code == 409
    assert "Facility conflict" in res.json()["detail"]

    # 9. Query Athletic Department Statistics
    res = await client.get("/api/athletics/stats", headers=student_headers)
    assert res.status_code == 200
    stats = res.json()
    assert stats["total_teams"] >= 1
    assert stats["total_athletes"] >= 1
    assert stats["matches_won"] >= 1
    assert stats["facilities_booked_count"] >= 1
