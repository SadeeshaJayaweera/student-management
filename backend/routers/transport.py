"""backend/routers/transport.py
Transport and Shuttle Management Router
Provides university bus and shuttle fleet management, routes, intermediate bus stops,
daily schedule timetables, live GPS telemetry updates, and student transit passes.
"""

import uuid
from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.models import (
    User,
    Student,
    TransportVehicle,
    ShuttleRoute,
    ShuttleStop,
    ShuttleSchedule,
    StudentTransportPass,
)
from backend.schemas import (
    TransportVehicleCreate,
    TransportVehicleUpdate,
    TransportVehicleTelemetryUpdate,
    TransportVehicleOut,
    ShuttleStopCreate,
    ShuttleStopOut,
    ShuttleRouteCreate,
    ShuttleRouteUpdate,
    ShuttleRouteOut,
    ShuttleScheduleCreate,
    ShuttleScheduleUpdate,
    ShuttleScheduleOut,
    StudentTransportPassCreate,
    StudentTransportPassOut,
    TransportFleetSummaryOut,
)
from backend.utils.security import get_current_user, require_roles

router = APIRouter(prefix="/api/transport", tags=["Transport & Shuttle Management"])


# ─── Operational Fleet Overview ──────────────────────────────────────────────

@router.get("/summary", response_model=TransportFleetSummaryOut)
async def get_transport_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Institutional overview of shuttle fleet, routes, timetable runs, and active student passes."""
    # Count vehicles
    v_res = await db.execute(
        select(
            func.count(TransportVehicle.id),
            func.sum(TransportVehicle.capacity),
        )
    )
    v_row = v_res.first()
    tot_vehicles = v_row[0] or 0
    fleet_cap = int(v_row[1] or 0)

    act_v_res = await db.execute(
        select(func.count(TransportVehicle.id)).where(TransportVehicle.status == "active")
    )
    active_v = act_v_res.scalar() or 0

    maint_v_res = await db.execute(
        select(func.count(TransportVehicle.id)).where(TransportVehicle.status == "maintenance")
    )
    maint_v = maint_v_res.scalar() or 0

    # Count routes & schedules
    r_res = await db.execute(select(func.count(ShuttleRoute.id)).where(ShuttleRoute.is_active == True))
    tot_routes = r_res.scalar() or 0

    s_res = await db.execute(select(func.count(ShuttleSchedule.id)).where(ShuttleSchedule.is_active == True))
    act_schedules = s_res.scalar() or 0

    # Count active passes
    p_res = await db.execute(
        select(func.count(StudentTransportPass.id)).where(
            and_(
                StudentTransportPass.status == "active",
                StudentTransportPass.valid_until >= date.today(),
            )
        )
    )
    act_passes = p_res.scalar() or 0

    return TransportFleetSummaryOut(
        total_vehicles=tot_vehicles,
        active_vehicles=active_v,
        maintenance_vehicles=maint_v,
        total_routes=tot_routes,
        active_schedules=act_schedules,
        active_passes=act_passes,
        fleet_capacity=fleet_cap,
    )


# ─── Transport Vehicles ──────────────────────────────────────────────────────

@router.get("/vehicles", response_model=List[TransportVehicleOut])
async def list_transport_vehicles(
    vehicle_type: Optional[str] = Query(None, pattern="^(bus|coaster|van|shuttle)$"),
    status_filter: Optional[str] = Query(None, pattern="^(active|maintenance|standby)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List transport vehicles with type and operational status filters."""
    stmt = select(TransportVehicle).order_by(TransportVehicle.vehicle_number)
    filters = []
    if vehicle_type:
        filters.append(TransportVehicle.vehicle_type == vehicle_type)
    if status_filter:
        filters.append(TransportVehicle.status == status_filter)

    if filters:
        stmt = stmt.where(and_(*filters))

    res = await db.execute(stmt)
    vehicles = res.scalars().all()
    return vehicles


@router.post("/vehicles", response_model=TransportVehicleOut, status_code=status.HTTP_201_CREATED)
async def create_transport_vehicle(
    payload: TransportVehicleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Register a new vehicle in the university transport fleet."""
    dup = await db.execute(
        select(TransportVehicle).where(TransportVehicle.vehicle_number == payload.vehicle_number.upper().strip())
    )
    if dup.scalars().first():
        raise HTTPException(status_code=400, detail="Vehicle with this license number already registered.")

    vehicle = TransportVehicle(
        vehicle_number=payload.vehicle_number.upper().strip(),
        vehicle_type=payload.vehicle_type,
        capacity=payload.capacity,
        driver_name=payload.driver_name.strip(),
        driver_contact=payload.driver_contact.strip(),
        status=payload.status,
        current_lat=6.8211,   # NSBM Green University Campus lat
        current_lng=80.0416,  # NSBM Green University Campus lng
        last_telemetry_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
    )
    db.add(vehicle)
    await db.commit()
    await db.refresh(vehicle)
    return vehicle


@router.put("/vehicles/{vehicle_id}", response_model=TransportVehicleOut)
async def update_transport_vehicle(
    vehicle_id: int,
    payload: TransportVehicleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Update vehicle driver assignment, capacity, or maintenance state."""
    res = await db.execute(select(TransportVehicle).where(TransportVehicle.id == vehicle_id))
    vehicle = res.scalars().first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found.")

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(vehicle, k, v)

    await db.commit()
    await db.refresh(vehicle)
    return vehicle


@router.put("/vehicles/{vehicle_id}/telemetry", response_model=TransportVehicleOut)
async def update_vehicle_telemetry(
    vehicle_id: int,
    payload: TransportVehicleTelemetryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Simulate or stream real-time GPS coordinates for vehicle tracking."""
    res = await db.execute(select(TransportVehicle).where(TransportVehicle.id == vehicle_id))
    vehicle = res.scalars().first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found.")

    vehicle.current_lat = payload.current_lat
    vehicle.current_lng = payload.current_lng
    vehicle.last_telemetry_at = datetime.utcnow()

    await db.commit()
    await db.refresh(vehicle)
    return vehicle


# ─── Shuttle Routes & Stops ──────────────────────────────────────────────────

def serialize_route(route: ShuttleRoute) -> ShuttleRouteOut:
    stops_out = [
        ShuttleStopOut(
            id=s.id,
            route_id=s.route_id,
            stop_name=s.stop_name,
            stop_order=s.stop_order,
            latitude=s.latitude,
            longitude=s.longitude,
            estimated_time_offset_mins=s.estimated_time_offset_mins,
        )
        for s in (route.stops or [])
    ]

    schedules_out = [
        ShuttleScheduleOut(
            id=sch.id,
            route_id=sch.route_id,
            route_name=route.route_name,
            route_code=route.route_code,
            vehicle_id=sch.vehicle_id,
            vehicle_number=sch.vehicle.vehicle_number if sch.vehicle else None,
            departure_time=sch.departure_time,
            arrival_time=sch.arrival_time,
            days_of_week=sch.days_of_week,
            shift_type=sch.shift_type,
            is_active=sch.is_active,
            created_at=sch.created_at,
        )
        for sch in (route.schedules or [])
    ]

    return ShuttleRouteOut(
        id=route.id,
        route_name=route.route_name,
        route_code=route.route_code,
        origin=route.origin,
        destination=route.destination,
        distance_km=route.distance_km,
        estimated_duration_mins=route.estimated_duration_mins,
        fare_amount=route.fare_amount,
        is_active=route.is_active,
        created_at=route.created_at,
        stops=stops_out,
        schedules=schedules_out,
    )


@router.get("/routes", response_model=List[ShuttleRouteOut])
async def list_shuttle_routes(
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List shuttle transit routes with stops and timetables."""
    stmt = (
        select(ShuttleRoute)
        .options(
            selectinload(ShuttleRoute.stops),
            selectinload(ShuttleRoute.schedules).selectinload(ShuttleSchedule.vehicle),
        )
        .order_by(ShuttleRoute.route_name)
    )
    if active_only:
        stmt = stmt.where(ShuttleRoute.is_active == True)

    res = await db.execute(stmt)
    routes = res.scalars().all()
    return [serialize_route(r) for r in routes]


@router.post("/routes", response_model=ShuttleRouteOut, status_code=status.HTTP_201_CREATED)
async def create_shuttle_route(
    payload: ShuttleRouteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Define a campus shuttle route with optional waypoint stops."""
    dup = await db.execute(
        select(ShuttleRoute).where(ShuttleRoute.route_code == payload.route_code.upper().strip())
    )
    if dup.scalars().first():
        raise HTTPException(status_code=400, detail="Route with this code already exists.")

    route = ShuttleRoute(
        route_name=payload.route_name.strip(),
        route_code=payload.route_code.upper().strip(),
        origin=payload.origin.strip(),
        destination=payload.destination.strip(),
        distance_km=payload.distance_km,
        estimated_duration_mins=payload.estimated_duration_mins,
        fare_amount=payload.fare_amount,
        is_active=payload.is_active,
        created_at=datetime.utcnow(),
    )
    db.add(route)
    await db.flush()

    if payload.stops:
        for st in payload.stops:
            stop_obj = ShuttleStop(
                route_id=route.id,
                stop_name=st.stop_name.strip(),
                stop_order=st.stop_order,
                latitude=st.latitude,
                longitude=st.longitude,
                estimated_time_offset_mins=st.estimated_time_offset_mins,
            )
            db.add(stop_obj)

    await db.commit()

    reload_res = await db.execute(
        select(ShuttleRoute)
        .options(
            selectinload(ShuttleRoute.stops),
            selectinload(ShuttleRoute.schedules).selectinload(ShuttleSchedule.vehicle),
        )
        .where(ShuttleRoute.id == route.id)
    )
    loaded = reload_res.scalars().first()
    return serialize_route(loaded)


@router.get("/routes/{route_id}", response_model=ShuttleRouteOut)
async def get_shuttle_route(
    route_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve full details of a specific route."""
    res = await db.execute(
        select(ShuttleRoute)
        .options(
            selectinload(ShuttleRoute.stops),
            selectinload(ShuttleRoute.schedules).selectinload(ShuttleSchedule.vehicle),
        )
        .where(ShuttleRoute.id == route_id)
    )
    route = res.scalars().first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found.")
    return serialize_route(route)


@router.put("/routes/{route_id}", response_model=ShuttleRouteOut)
async def update_shuttle_route(
    route_id: int,
    payload: ShuttleRouteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Update route properties or fare."""
    res = await db.execute(
        select(ShuttleRoute)
        .options(
            selectinload(ShuttleRoute.stops),
            selectinload(ShuttleRoute.schedules).selectinload(ShuttleSchedule.vehicle),
        )
        .where(ShuttleRoute.id == route_id)
    )
    route = res.scalars().first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found.")

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(route, k, v)

    await db.commit()
    await db.refresh(route)
    return serialize_route(route)


@router.post("/routes/{route_id}/stops", response_model=ShuttleStopOut, status_code=status.HTTP_201_CREATED)
async def add_shuttle_stop(
    route_id: int,
    payload: ShuttleStopCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Append or insert an intermediate boarding stop to a route."""
    r_res = await db.execute(select(ShuttleRoute).where(ShuttleRoute.id == route_id))
    if not r_res.scalars().first():
        raise HTTPException(status_code=404, detail="Route not found.")

    stop = ShuttleStop(
        route_id=route_id,
        stop_name=payload.stop_name.strip(),
        stop_order=payload.stop_order,
        latitude=payload.latitude,
        longitude=payload.longitude,
        estimated_time_offset_mins=payload.estimated_time_offset_mins,
    )
    db.add(stop)
    await db.commit()
    await db.refresh(stop)

    return ShuttleStopOut(
        id=stop.id,
        route_id=stop.route_id,
        stop_name=stop.stop_name,
        stop_order=stop.stop_order,
        latitude=stop.latitude,
        longitude=stop.longitude,
        estimated_time_offset_mins=stop.estimated_time_offset_mins,
    )


# ─── Shuttle Timetable / Schedules ───────────────────────────────────────────

@router.get("/schedules", response_model=List[ShuttleScheduleOut])
async def list_shuttle_schedules(
    route_id: Optional[int] = Query(None),
    shift_type: Optional[str] = Query(None, pattern="^(morning_inbound|evening_outbound|midday_shuttle|special)$"),
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List bus trip timetables with route and departure filters."""
    stmt = (
        select(ShuttleSchedule)
        .options(
            selectinload(ShuttleSchedule.route),
            selectinload(ShuttleSchedule.vehicle),
        )
        .order_by(ShuttleSchedule.departure_time)
    )
    filters = []
    if route_id:
        filters.append(ShuttleSchedule.route_id == route_id)
    if shift_type:
        filters.append(ShuttleSchedule.shift_type == shift_type)
    if active_only:
        filters.append(ShuttleSchedule.is_active == True)

    if filters:
        stmt = stmt.where(and_(*filters))

    res = await db.execute(stmt)
    schedules = res.scalars().all()

    return [
        ShuttleScheduleOut(
            id=s.id,
            route_id=s.route_id,
            route_name=s.route.route_name if s.route else None,
            route_code=s.route.route_code if s.route else None,
            vehicle_id=s.vehicle_id,
            vehicle_number=s.vehicle.vehicle_number if s.vehicle else None,
            departure_time=s.departure_time,
            arrival_time=s.arrival_time,
            days_of_week=s.days_of_week,
            shift_type=s.shift_type,
            is_active=s.is_active,
            created_at=s.created_at,
        )
        for s in schedules
    ]


@router.post("/schedules", response_model=ShuttleScheduleOut, status_code=status.HTTP_201_CREATED)
async def create_shuttle_schedule(
    payload: ShuttleScheduleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Add a scheduled transit run to the timetable."""
    r_res = await db.execute(select(ShuttleRoute).where(ShuttleRoute.id == payload.route_id))
    route = r_res.scalars().first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found.")

    v_num = None
    if payload.vehicle_id:
        v_res = await db.execute(select(TransportVehicle).where(TransportVehicle.id == payload.vehicle_id))
        v_obj = v_res.scalars().first()
        if not v_obj:
            raise HTTPException(status_code=404, detail="Vehicle not found.")
        v_num = v_obj.vehicle_number

    schedule = ShuttleSchedule(
        route_id=payload.route_id,
        vehicle_id=payload.vehicle_id,
        departure_time=payload.departure_time,
        arrival_time=payload.arrival_time,
        days_of_week=payload.days_of_week or ["monday", "tuesday", "wednesday", "thursday", "friday"],
        shift_type=payload.shift_type,
        is_active=payload.is_active,
        created_at=datetime.utcnow(),
    )
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)

    return ShuttleScheduleOut(
        id=schedule.id,
        route_id=schedule.route_id,
        route_name=route.route_name,
        route_code=route.route_code,
        vehicle_id=schedule.vehicle_id,
        vehicle_number=v_num,
        departure_time=schedule.departure_time,
        arrival_time=schedule.arrival_time,
        days_of_week=schedule.days_of_week,
        shift_type=schedule.shift_type,
        is_active=schedule.is_active,
        created_at=schedule.created_at,
    )


# ─── Student Transport Passes ────────────────────────────────────────────────

def serialize_pass(p: StudentTransportPass) -> StudentTransportPassOut:
    s_name = p.student.user.full_name if (p.student and p.student.user) else None
    s_reg = p.student.student_id if p.student else None
    r_name = p.route.route_name if p.route else None
    r_code = p.route.route_code if p.route else None

    return StudentTransportPassOut(
        id=p.id,
        student_id=p.student_id,
        student_name=s_name,
        student_reg_number=s_reg,
        route_id=p.route_id,
        route_name=r_name,
        route_code=r_code,
        pass_type=p.pass_type,
        valid_from=p.valid_from,
        valid_until=p.valid_until,
        qr_code_token=p.qr_code_token,
        fare_paid=p.fare_paid,
        status=p.status,
        created_at=p.created_at,
    )


@router.get("/passes", response_model=List[StudentTransportPassOut])
async def list_transport_passes(
    route_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, pattern="^(active|expired|suspended)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List transport passes. Students only see their own passes."""
    stmt = (
        select(StudentTransportPass)
        .options(
            selectinload(StudentTransportPass.student).selectinload(Student.user),
            selectinload(StudentTransportPass.route),
        )
        .order_by(desc(StudentTransportPass.created_at))
    )

    filters = []
    if current_user.role == "student":
        stu_res = await db.execute(select(Student).where(Student.user_id == current_user.id))
        stu = stu_res.scalars().first()
        if not stu:
            return []
        filters.append(StudentTransportPass.student_id == stu.id)
    if route_id:
        filters.append(StudentTransportPass.route_id == route_id)
    if status_filter:
        filters.append(StudentTransportPass.status == status_filter)

    if filters:
        stmt = stmt.where(and_(*filters))

    res = await db.execute(stmt)
    passes = res.scalars().all()
    return [serialize_pass(p) for p in passes]


@router.get("/passes/my", response_model=Optional[StudentTransportPassOut])
async def get_my_active_transport_pass(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve currently logged in student's active bus transit pass."""
    stu_res = await db.execute(select(Student).where(Student.user_id == current_user.id))
    stu = stu_res.scalars().first()
    if not stu:
        return None

    res = await db.execute(
        select(StudentTransportPass)
        .options(
            selectinload(StudentTransportPass.student).selectinload(Student.user),
            selectinload(StudentTransportPass.route),
        )
        .where(
            and_(
                StudentTransportPass.student_id == stu.id,
                StudentTransportPass.status == "active",
                StudentTransportPass.valid_until >= date.today(),
            )
        )
    )
    p = res.scalars().first()
    return serialize_pass(p) if p else None


@router.post("/passes", response_model=StudentTransportPassOut, status_code=status.HTTP_201_CREATED)
async def create_student_transport_pass(
    payload: StudentTransportPassCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Issue a digital QR transport pass to a student."""
    stu_res = await db.execute(select(Student).where(Student.id == payload.student_id))
    if not stu_res.scalars().first():
        raise HTTPException(status_code=404, detail="Student not found.")

    r_res = await db.execute(select(ShuttleRoute).where(ShuttleRoute.id == payload.route_id))
    if not r_res.scalars().first():
        raise HTTPException(status_code=404, detail="Route not found.")

    token = f"PASS-{uuid.uuid4().hex[:12].upper()}"

    tpass = StudentTransportPass(
        student_id=payload.student_id,
        route_id=payload.route_id,
        pass_type=payload.pass_type,
        valid_from=payload.valid_from,
        valid_until=payload.valid_until,
        qr_code_token=token,
        fare_paid=payload.fare_paid,
        status="active",
        created_at=datetime.utcnow(),
    )
    db.add(tpass)
    await db.commit()

    reload_res = await db.execute(
        select(StudentTransportPass)
        .options(
            selectinload(StudentTransportPass.student).selectinload(Student.user),
            selectinload(StudentTransportPass.route),
        )
        .where(StudentTransportPass.id == tpass.id)
    )
    loaded = reload_res.scalars().first()
    return serialize_pass(loaded)
