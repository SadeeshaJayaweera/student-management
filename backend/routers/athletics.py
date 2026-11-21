"""backend/routers/athletics.py
Sports and Athletic Management Router
Manages university athletic teams, student athlete rosters, inter-university fixtures,
SLUG tournament scheduling, match scoring, and sports facility reservations.
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.models import (
    User,
    Student,
    AthleticTeam,
    AthleteProfile,
    SportsFixture,
    SportsFacilityBooking,
)
from backend.schemas import (
    AthleticTeamCreate,
    AthleticTeamOut,
    AthleteProfileCreate,
    AthleteProfileOut,
    SportsFixtureCreate,
    SportsFixtureResultUpdate,
    SportsFixtureOut,
    SportsFacilityBookingCreate,
    SportsFacilityBookingOut,
    AthleticStatsOut,
)
from backend.utils.security import get_current_user, require_roles

router = APIRouter(prefix="/api/athletics", tags=["Sports & Athletic Management"])


def serialize_athlete(a: AthleteProfile) -> AthleteProfileOut:
    s_name = a.student.user.full_name if (a.student and a.student.user) else None
    s_reg = a.student.student_id if a.student else None
    return AthleteProfileOut(
        id=a.id,
        student_id=a.student_id,
        student_name=s_name,
        student_reg_number=s_reg,
        team_id=a.team_id,
        jersey_number=a.jersey_number,
        position_or_role=a.position_or_role,
        fitness_status=a.fitness_status,
        matches_played=a.matches_played,
        points_or_goals=a.points_or_goals,
        mvp_awards=a.mvp_awards,
        joined_date=a.joined_date,
        created_at=a.created_at,
    )


def serialize_fixture(f: SportsFixture) -> SportsFixtureOut:
    t_name = f.team.name if f.team else None
    s_type = f.team.sport_type if f.team else None
    return SportsFixtureOut(
        id=f.id,
        team_id=f.team_id,
        team_name=t_name,
        sport_type=s_type,
        tournament_name=f.tournament_name,
        opponent_name=f.opponent_name,
        scheduled_time=f.scheduled_time,
        venue=f.venue,
        fixture_type=f.fixture_type,
        status=f.status,
        our_score=f.our_score,
        opponent_score=f.opponent_score,
        match_result=f.match_result,
        highlights=f.highlights,
        created_at=f.created_at,
    )


# ─── Athletic Teams & Rosters ────────────────────────────────────────────────

@router.get("/teams", response_model=List[AthleticTeamOut])
async def list_athletic_teams(
    sport_type: Optional[str] = Query(None),
    division: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """List all university athletic teams and sports clubs."""
    query = (
        select(AthleticTeam)
        .options(
            selectinload(AthleticTeam.roster).selectinload(AthleteProfile.student).selectinload(Student.user),
            selectinload(AthleticTeam.fixtures),
        )
        .where(AthleticTeam.is_active == True)
        .order_by(AthleticTeam.sport_type.asc(), AthleticTeam.name.asc())
    )
    if sport_type and sport_type != "all":
        query = query.where(AthleticTeam.sport_type == sport_type)
    if division:
        query = query.where(AthleticTeam.division == division)

    res = await db.execute(query)
    teams = res.scalars().all()

    out = []
    for t in teams:
        roster_out = [serialize_athlete(a) for a in (t.roster or [])]
        fixtures_out = [serialize_fixture(f) for f in (t.fixtures or [])]
        out.append(
            AthleticTeamOut(
                id=t.id,
                name=t.name,
                sport_type=t.sport_type,
                coach_name=t.coach_name,
                captain_name=t.captain_name,
                division=t.division,
                home_venue=t.home_venue,
                logo_url=t.logo_url,
                is_active=t.is_active,
                roster=roster_out,
                fixtures=fixtures_out,
                created_at=t.created_at,
            )
        )
    return out


@router.post("/teams", response_model=AthleticTeamOut, status_code=status.HTTP_201_CREATED)
async def create_athletic_team(
    payload: AthleticTeamCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "lecturer")),
):
    """Form and register an institutional university sports squad."""
    team = AthleticTeam(
        name=payload.name,
        sport_type=payload.sport_type,
        coach_name=payload.coach_name,
        captain_name=payload.captain_name,
        division=payload.division,
        home_venue=payload.home_venue,
        logo_url=payload.logo_url,
        is_active=True,
        created_at=datetime.utcnow(),
    )
    db.add(team)
    await db.commit()
    await db.refresh(team)

    return AthleticTeamOut(
        id=team.id,
        name=team.name,
        sport_type=team.sport_type,
        coach_name=team.coach_name,
        captain_name=team.captain_name,
        division=team.division,
        home_venue=team.home_venue,
        logo_url=team.logo_url,
        is_active=team.is_active,
        roster=[],
        fixtures=[],
        created_at=team.created_at,
    )


@router.get("/teams/{team_id}", response_model=AthleticTeamOut)
async def get_team_detail(
    team_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Retrieve full team profile, roster, and scheduled fixtures."""
    res = await db.execute(
        select(AthleticTeam)
        .options(
            selectinload(AthleticTeam.roster).selectinload(AthleteProfile.student).selectinload(Student.user),
            selectinload(AthleticTeam.fixtures),
        )
        .where(AthleticTeam.id == team_id)
    )
    team = res.scalars().first()
    if not team:
        raise HTTPException(status_code=404, detail="Athletic team not found.")

    roster_out = [serialize_athlete(a) for a in (team.roster or [])]
    fixtures_out = [serialize_fixture(f) for f in (team.fixtures or [])]
    return AthleticTeamOut(
        id=team.id,
        name=team.name,
        sport_type=team.sport_type,
        coach_name=team.coach_name,
        captain_name=team.captain_name,
        division=team.division,
        home_venue=team.home_venue,
        logo_url=team.logo_url,
        is_active=team.is_active,
        roster=roster_out,
        fixtures=fixtures_out,
        created_at=team.created_at,
    )


@router.post("/teams/{team_id}/roster", response_model=AthleteProfileOut, status_code=status.HTTP_201_CREATED)
async def add_athlete_to_roster(
    team_id: int,
    payload: AthleteProfileCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "lecturer")),
):
    """Enlist a student athlete into an athletic team roster."""
    team_res = await db.execute(select(AthleticTeam).where(AthleticTeam.id == team_id))
    team = team_res.scalars().first()
    if not team:
        raise HTTPException(status_code=404, detail="Athletic team not found.")

    stu_res = await db.execute(select(Student).where(Student.id == payload.student_id))
    student = stu_res.scalars().first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    # Check existing membership in this team
    exist = await db.execute(
        select(AthleteProfile).where(
            and_(
                AthleteProfile.team_id == team_id,
                AthleteProfile.student_id == payload.student_id,
            )
        )
    )
    if exist.scalars().first():
        raise HTTPException(status_code=400, detail="Student is already in this team roster.")

    athlete = AthleteProfile(
        student_id=payload.student_id,
        team_id=team_id,
        jersey_number=payload.jersey_number,
        position_or_role=payload.position_or_role,
        fitness_status=payload.fitness_status,
        matches_played=0,
        points_or_goals=0,
        mvp_awards=0,
        joined_date=payload.joined_date or datetime.utcnow().date(),
        created_at=datetime.utcnow(),
    )
    db.add(athlete)
    await db.commit()

    reload_res = await db.execute(
        select(AthleteProfile)
        .options(selectinload(AthleteProfile.student).selectinload(Student.user))
        .where(AthleteProfile.id == athlete.id)
    )
    loaded = reload_res.scalars().first()
    return serialize_athlete(loaded)


@router.put("/athletes/{athlete_id}/fitness", response_model=AthleteProfileOut)
async def update_athlete_status(
    athlete_id: int,
    fitness_status: str = Query(..., pattern="^(fit|injured|resting|convalescing)$"),
    matches_increment: int = Query(0, ge=0),
    points_increment: int = Query(0, ge=0),
    mvp_increment: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "lecturer")),
):
    """Update medical fitness status and game performance metrics for an athlete."""
    res = await db.execute(
        select(AthleteProfile)
        .options(selectinload(AthleteProfile.student).selectinload(Student.user))
        .where(AthleteProfile.id == athlete_id)
    )
    athlete = res.scalars().first()
    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete profile not found.")

    athlete.fitness_status = fitness_status
    athlete.matches_played += matches_increment
    athlete.points_or_goals += points_increment
    athlete.mvp_awards += mvp_increment
    await db.commit()
    await db.refresh(athlete)

    return serialize_athlete(athlete)


# ─── Fixtures & Tournament Matches ───────────────────────────────────────────

@router.get("/fixtures", response_model=List[SportsFixtureOut])
async def list_sports_fixtures(
    team_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None),
    tournament: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Retrieve schedule of matches, inter-university tournaments, and results."""
    query = (
        select(SportsFixture)
        .options(selectinload(SportsFixture.team))
        .order_by(SportsFixture.scheduled_time.desc())
        .offset(offset)
        .limit(limit)
    )
    filters = []
    if team_id:
        filters.append(SportsFixture.team_id == team_id)
    if status_filter and status_filter != "all":
        filters.append(SportsFixture.status == status_filter)
    if tournament:
        filters.append(SportsFixture.tournament_name.ilike(f"%{tournament.strip()}%"))

    if filters:
        query = query.where(and_(*filters))

    res = await db.execute(query)
    fixtures = res.scalars().all()
    return [serialize_fixture(f) for f in fixtures]


@router.post("/fixtures", response_model=SportsFixtureOut, status_code=status.HTTP_201_CREATED)
async def create_sports_fixture(
    payload: SportsFixtureCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "lecturer")),
):
    """Schedule an upcoming sports match, friendly, or SLUG tournament fixture."""
    team_res = await db.execute(select(AthleticTeam).where(AthleticTeam.id == payload.team_id))
    team = team_res.scalars().first()
    if not team:
        raise HTTPException(status_code=404, detail="Athletic team not found.")

    fixture = SportsFixture(
        team_id=payload.team_id,
        tournament_name=payload.tournament_name,
        opponent_name=payload.opponent_name,
        scheduled_time=payload.scheduled_time,
        venue=payload.venue,
        fixture_type=payload.fixture_type,
        status="upcoming",
        created_at=datetime.utcnow(),
    )
    db.add(fixture)
    await db.commit()

    reload_res = await db.execute(
        select(SportsFixture)
        .options(selectinload(SportsFixture.team))
        .where(SportsFixture.id == fixture.id)
    )
    loaded = reload_res.scalars().first()
    return serialize_fixture(loaded)


@router.put("/fixtures/{fixture_id}/result", response_model=SportsFixtureOut)
async def record_fixture_result(
    fixture_id: int,
    payload: SportsFixtureResultUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "lecturer")),
):
    """Log match results, final scores, and highlights after a game."""
    res = await db.execute(
        select(SportsFixture)
        .options(selectinload(SportsFixture.team))
        .where(SportsFixture.id == fixture_id)
    )
    fixture = res.scalars().first()
    if not fixture:
        raise HTTPException(status_code=404, detail="Sports fixture not found.")

    fixture.status = payload.status
    fixture.our_score = payload.our_score
    fixture.opponent_score = payload.opponent_score
    fixture.match_result = payload.match_result
    if payload.highlights:
        fixture.highlights = payload.highlights

    await db.commit()
    await db.refresh(fixture)
    return serialize_fixture(fixture)


# ─── Facility Reservations ───────────────────────────────────────────────────

@router.get("/facility-bookings", response_model=List[SportsFacilityBookingOut])
async def list_facility_bookings(
    facility_name: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """List facility reservation schedules for campus sports grounds and indoor complexes."""
    query = (
        select(SportsFacilityBooking)
        .options(
            selectinload(SportsFacilityBooking.booked_by),
            selectinload(SportsFacilityBooking.team),
        )
        .order_by(SportsFacilityBooking.start_time.asc())
    )
    filters = []
    if facility_name and facility_name != "all":
        filters.append(SportsFacilityBooking.facility_name == facility_name)
    if status_filter and status_filter != "all":
        filters.append(SportsFacilityBooking.status == status_filter)

    if filters:
        query = query.where(and_(*filters))

    res = await db.execute(query)
    bookings = res.scalars().all()

    return [
        SportsFacilityBookingOut(
            id=b.id,
            facility_name=b.facility_name,
            booked_by_user_id=b.booked_by_user_id,
            booked_by_name=b.booked_by.full_name if b.booked_by else None,
            team_id=b.team_id,
            team_name=b.team.name if b.team else None,
            start_time=b.start_time,
            end_time=b.end_time,
            purpose=b.purpose,
            status=b.status,
            created_at=b.created_at,
        )
        for b in bookings
    ]


@router.post("/facility-bookings", response_model=SportsFacilityBookingOut, status_code=status.HTTP_201_CREATED)
async def book_sports_facility(
    payload: SportsFacilityBookingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reserve a sports ground, swimming pool, or gym with conflict detection."""
    if payload.end_time <= payload.start_time:
        raise HTTPException(status_code=400, detail="End time must be strictly after start time.")

    # Conflict detection: ensure no overlapping confirmed booking on the same facility
    conflict_q = await db.execute(
        select(SportsFacilityBooking).where(
            and_(
                SportsFacilityBooking.facility_name == payload.facility_name,
                SportsFacilityBooking.status == "confirmed",
                or_(
                    and_(
                        SportsFacilityBooking.start_time <= payload.start_time,
                        SportsFacilityBooking.end_time > payload.start_time,
                    ),
                    and_(
                        SportsFacilityBooking.start_time < payload.end_time,
                        SportsFacilityBooking.end_time >= payload.end_time,
                    ),
                    and_(
                        SportsFacilityBooking.start_time >= payload.start_time,
                        SportsFacilityBooking.end_time <= payload.end_time,
                    ),
                ),
            )
        )
    )
    conflict = conflict_q.scalars().first()
    if conflict:
        raise HTTPException(
            status_code=409,
            detail=f"Facility conflict: '{payload.facility_name}' is already reserved between {conflict.start_time.strftime('%H:%M')} and {conflict.end_time.strftime('%H:%M')}."
        )

    booking = SportsFacilityBooking(
        facility_name=payload.facility_name,
        booked_by_user_id=current_user.id,
        team_id=payload.team_id,
        start_time=payload.start_time,
        end_time=payload.end_time,
        purpose=payload.purpose,
        status="confirmed",
        created_at=datetime.utcnow(),
    )
    db.add(booking)
    await db.commit()

    reload_res = await db.execute(
        select(SportsFacilityBooking)
        .options(
            selectinload(SportsFacilityBooking.booked_by),
            selectinload(SportsFacilityBooking.team),
        )
        .where(SportsFacilityBooking.id == booking.id)
    )
    loaded = reload_res.scalars().first()

    return SportsFacilityBookingOut(
        id=loaded.id,
        facility_name=loaded.facility_name,
        booked_by_user_id=loaded.booked_by_user_id,
        booked_by_name=loaded.booked_by.full_name if loaded.booked_by else None,
        team_id=loaded.team_id,
        team_name=loaded.team.name if loaded.team else None,
        start_time=loaded.start_time,
        end_time=loaded.end_time,
        purpose=loaded.purpose,
        status=loaded.status,
        created_at=loaded.created_at,
    )


# ─── Athletic Department Analytics ───────────────────────────────────────────

@router.get("/stats", response_model=AthleticStatsOut)
async def get_athletic_stats(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Aggregate department overview: total squads, roster strength, fixtures, and win records."""
    teams_cnt = await db.execute(select(func.count(AthleticTeam.id)))
    athletes_cnt = await db.execute(select(func.count(AthleteProfile.id)))
    upcoming_cnt = await db.execute(
        select(func.count(SportsFixture.id)).where(SportsFixture.status == "upcoming")
    )
    won_cnt = await db.execute(
        select(func.count(SportsFixture.id)).where(SportsFixture.match_result == "won")
    )
    lost_cnt = await db.execute(
        select(func.count(SportsFixture.id)).where(SportsFixture.match_result == "lost")
    )
    bookings_cnt = await db.execute(
        select(func.count(SportsFacilityBooking.id)).where(SportsFacilityBooking.status == "confirmed")
    )

    return AthleticStatsOut(
        total_teams=teams_cnt.scalar() or 0,
        total_athletes=athletes_cnt.scalar() or 0,
        upcoming_fixtures_count=upcoming_cnt.scalar() or 0,
        matches_won=won_cnt.scalar() or 0,
        matches_lost=lost_cnt.scalar() or 0,
        facilities_booked_count=bookings_cnt.scalar() or 0,
    )
