"""backend/routers/facilities.py
Campus Facility and Resource Booking Router
Provides auditorium, lecture hall, lab, and meeting space management,
equipment asset tracking, conflict-detection reservation scheduling,
and booking approvals.
"""

from datetime import datetime, date, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.models import (
    User,
    CampusFacility,
    FacilityEquipment,
    FacilityReservation,
)
from backend.schemas import (
    CampusFacilityCreate,
    CampusFacilityUpdate,
    CampusFacilityOut,
    FacilityEquipmentCreate,
    FacilityEquipmentUpdate,
    FacilityEquipmentOut,
    FacilityReservationCreate,
    FacilityReservationUpdate,
    FacilityReservationOut,
    FacilityBookingSummaryOut,
)
from backend.utils.security import get_current_user, require_roles

router = APIRouter(prefix="/api/facilities", tags=["Campus Facility & Resource Booking"])


# ─── Operational Facilities Summary ──────────────────────────────────────────

@router.get("/summary", response_model=FacilityBookingSummaryOut)
async def get_facility_booking_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Institutional overview of facilities, equipment assets, and booking load."""
    f_res = await db.execute(
        select(
            func.count(CampusFacility.id),
            func.sum(CampusFacility.capacity),
        ).where(CampusFacility.is_active == True)
    )
    f_row = f_res.first()
    tot_facilities = f_row[0] or 0
    tot_cap = int(f_row[1] or 0)

    eq_res = await db.execute(select(func.count(FacilityEquipment.id)))
    tot_eq = eq_res.scalar() or 0

    today_start = datetime.combine(date.today(), datetime.min.time())
    today_end = datetime.combine(date.today(), datetime.max.time())

    today_res = await db.execute(
        select(func.count(FacilityReservation.id)).where(
            and_(
                FacilityReservation.status == "confirmed",
                FacilityReservation.start_time >= today_start,
                FacilityReservation.start_time <= today_end,
            )
        )
    )
    today_bookings = today_res.scalar() or 0

    pending_res = await db.execute(
        select(func.count(FacilityReservation.id)).where(FacilityReservation.status == "pending")
    )
    pending_appr = pending_res.scalar() or 0

    return FacilityBookingSummaryOut(
        total_facilities=tot_facilities,
        total_capacity=tot_cap,
        total_equipment=tot_eq,
        confirmed_reservations_today=today_bookings,
        pending_approvals=pending_appr,
    )


# ─── Campus Facilities ───────────────────────────────────────────────────────

def serialize_facility(f: CampusFacility) -> CampusFacilityOut:
    eq_out = [
        FacilityEquipmentOut(
            id=eq.id,
            facility_id=eq.facility_id,
            name=eq.name,
            asset_tag=eq.asset_tag,
            equipment_type=eq.equipment_type,
            status=eq.status,
            created_at=eq.created_at,
        )
        for eq in (f.equipment or [])
    ]
    active_cnt = len([r for r in (f.reservations or []) if r.status in ["confirmed", "pending"]])

    return CampusFacilityOut(
        id=f.id,
        name=f.name,
        facility_code=f.facility_code,
        facility_type=f.facility_type,
        building_name=f.building_name,
        floor=f.floor,
        capacity=f.capacity,
        hourly_rate=f.hourly_rate,
        amenities=f.amenities,
        is_active=f.is_active,
        created_at=f.created_at,
        equipment=eq_out,
        active_reservations_count=active_cnt,
    )


@router.get("", response_model=List[CampusFacilityOut])
async def list_campus_facilities(
    facility_type: Optional[str] = Query(None),
    min_capacity: Optional[int] = Query(None, ge=1),
    building_name: Optional[str] = Query(None),
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List lecture halls, auditoriums, labs, and seminar venues."""
    stmt = (
        select(CampusFacility)
        .options(
            selectinload(CampusFacility.equipment),
            selectinload(CampusFacility.reservations),
        )
        .order_by(CampusFacility.building_name, CampusFacility.name)
    )
    filters = []
    if active_only:
        filters.append(CampusFacility.is_active == True)
    if facility_type:
        filters.append(CampusFacility.facility_type == facility_type)
    if min_capacity:
        filters.append(CampusFacility.capacity >= min_capacity)
    if building_name:
        filters.append(CampusFacility.building_name.ilike(f"%{building_name.strip()}%"))

    if filters:
        stmt = stmt.where(and_(*filters))

    res = await db.execute(stmt)
    facilities = res.scalars().all()
    return [serialize_facility(f) for f in facilities]


@router.post("", response_model=CampusFacilityOut, status_code=status.HTTP_201_CREATED)
async def create_campus_facility(
    payload: CampusFacilityCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Register a new venue or facility on campus."""
    dup = await db.execute(
        select(CampusFacility).where(CampusFacility.facility_code == payload.facility_code.upper().strip())
    )
    if dup.scalars().first():
        raise HTTPException(status_code=400, detail="Facility with this code already exists.")

    facility = CampusFacility(
        name=payload.name.strip(),
        facility_code=payload.facility_code.upper().strip(),
        facility_type=payload.facility_type,
        building_name=payload.building_name.strip(),
        floor=payload.floor,
        capacity=payload.capacity,
        hourly_rate=payload.hourly_rate,
        amenities=payload.amenities or [],
        is_active=payload.is_active,
        created_at=datetime.utcnow(),
    )
    db.add(facility)
    await db.commit()

    reload_res = await db.execute(
        select(CampusFacility)
        .options(
            selectinload(CampusFacility.equipment),
            selectinload(CampusFacility.reservations),
        )
        .where(CampusFacility.id == facility.id)
    )
    loaded = reload_res.scalars().first()
    return serialize_facility(loaded)


@router.get("/{facility_id}", response_model=CampusFacilityOut)
async def get_campus_facility(
    facility_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve full detail of a venue including attached AV equipment and bookings."""
    res = await db.execute(
        select(CampusFacility)
        .options(
            selectinload(CampusFacility.equipment),
            selectinload(CampusFacility.reservations),
        )
        .where(CampusFacility.id == facility_id)
    )
    f = res.scalars().first()
    if not f:
        raise HTTPException(status_code=404, detail="Facility not found.")
    return serialize_facility(f)


@router.put("/{facility_id}", response_model=CampusFacilityOut)
async def update_campus_facility(
    facility_id: int,
    payload: CampusFacilityUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Update facility capacity, rate, or amenities."""
    res = await db.execute(
        select(CampusFacility)
        .options(
            selectinload(CampusFacility.equipment),
            selectinload(CampusFacility.reservations),
        )
        .where(CampusFacility.id == facility_id)
    )
    f = res.scalars().first()
    if not f:
        raise HTTPException(status_code=404, detail="Facility not found.")

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(f, k, v)

    await db.commit()
    await db.refresh(f)
    return serialize_facility(f)


# ─── Facility Equipment ──────────────────────────────────────────────────────

@router.get("/equipment/all", response_model=List[FacilityEquipmentOut])
async def list_facility_equipment(
    facility_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, pattern="^(available|in_use|maintenance)$"),
    equipment_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Query audio-visual equipment and portable tech assets."""
    stmt = select(FacilityEquipment).order_by(FacilityEquipment.name)
    filters = []
    if facility_id:
        filters.append(FacilityEquipment.facility_id == facility_id)
    if status_filter:
        filters.append(FacilityEquipment.status == status_filter)
    if equipment_type:
        filters.append(FacilityEquipment.equipment_type == equipment_type)

    if filters:
        stmt = stmt.where(and_(*filters))

    res = await db.execute(stmt)
    return res.scalars().all()


@router.post("/equipment", response_model=FacilityEquipmentOut, status_code=status.HTTP_201_CREATED)
async def create_facility_equipment(
    payload: FacilityEquipmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Register a new AV device or piece of equipment."""
    dup = await db.execute(
        select(FacilityEquipment).where(FacilityEquipment.asset_tag == payload.asset_tag.upper().strip())
    )
    if dup.scalars().first():
        raise HTTPException(status_code=400, detail="Equipment with this asset tag already registered.")

    eq = FacilityEquipment(
        facility_id=payload.facility_id,
        name=payload.name.strip(),
        asset_tag=payload.asset_tag.upper().strip(),
        equipment_type=payload.equipment_type,
        status=payload.status,
        created_at=datetime.utcnow(),
    )
    db.add(eq)
    await db.commit()
    await db.refresh(eq)
    return eq


@router.put("/equipment/{equipment_id}", response_model=FacilityEquipmentOut)
async def update_facility_equipment(
    equipment_id: int,
    payload: FacilityEquipmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Modify equipment status or room assignment."""
    res = await db.execute(select(FacilityEquipment).where(FacilityEquipment.id == equipment_id))
    eq = res.scalars().first()
    if not eq:
        raise HTTPException(status_code=404, detail="Equipment asset not found.")

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(eq, k, v)

    await db.commit()
    await db.refresh(eq)
    return eq


# ─── Facility Reservations ───────────────────────────────────────────────────

def serialize_reservation(r: FacilityReservation) -> FacilityReservationOut:
    f_name = r.facility.name if r.facility else None
    f_code = r.facility.facility_code if r.facility else None
    u_name = r.reserved_by.full_name if r.reserved_by else None
    u_role = r.reserved_by.role if r.reserved_by else None

    return FacilityReservationOut(
        id=r.id,
        facility_id=r.facility_id,
        facility_name=f_name,
        facility_code=f_code,
        reserved_by_user_id=r.reserved_by_user_id,
        reserved_by_name=u_name,
        reserved_by_role=u_role,
        start_time=r.start_time,
        end_time=r.end_time,
        purpose=r.purpose,
        attendee_count=r.attendee_count,
        status=r.status,
        approval_notes=r.approval_notes,
        equipment_requested=r.equipment_requested,
        created_at=r.created_at,
    )


@router.get("/reservations/all", response_model=List[FacilityReservationOut])
async def list_facility_reservations(
    facility_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, pattern="^(pending|confirmed|cancelled|rejected)$"),
    user_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Query scheduled venue bookings with facility and status filters."""
    stmt = (
        select(FacilityReservation)
        .options(
            selectinload(FacilityReservation.facility),
            selectinload(FacilityReservation.reserved_by),
        )
        .order_by(desc(FacilityReservation.start_time))
    )

    filters = []
    # Students can only view their own reservations unless viewing public schedule
    if current_user.role == "student" and not facility_id:
        filters.append(FacilityReservation.reserved_by_user_id == current_user.id)
    elif user_id:
        filters.append(FacilityReservation.reserved_by_user_id == user_id)

    if facility_id:
        filters.append(FacilityReservation.facility_id == facility_id)
    if status_filter:
        filters.append(FacilityReservation.status == status_filter)

    if filters:
        stmt = stmt.where(and_(*filters))

    res = await db.execute(stmt)
    reservations = res.scalars().all()
    return [serialize_reservation(r) for r in reservations]


@router.get("/reservations/my", response_model=List[FacilityReservationOut])
async def get_my_facility_reservations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve logged-in user's own reservations."""
    res = await db.execute(
        select(FacilityReservation)
        .options(
            selectinload(FacilityReservation.facility),
            selectinload(FacilityReservation.reserved_by),
        )
        .where(FacilityReservation.reserved_by_user_id == current_user.id)
        .order_by(desc(FacilityReservation.start_time))
    )
    reservations = res.scalars().all()
    return [serialize_reservation(r) for r in reservations]


@router.post("/reservations", response_model=FacilityReservationOut, status_code=status.HTTP_201_CREATED)
async def create_facility_reservation(
    payload: FacilityReservationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Book a campus facility with automatic schedule conflict detection."""
    if payload.end_time <= payload.start_time:
        raise HTTPException(status_code=400, detail="End time must be after start time.")

    f_res = await db.execute(select(CampusFacility).where(CampusFacility.id == payload.facility_id))
    facility = f_res.scalars().first()
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found.")
    if not facility.is_active:
        raise HTTPException(status_code=400, detail="Facility is currently deactivated.")

    # Capacity check
    if payload.attendee_count > facility.capacity:
        raise HTTPException(
            status_code=400,
            detail=f"Requested attendee count ({payload.attendee_count}) exceeds facility capacity ({facility.capacity}).",
        )

    # Conflict check: ensure no active reservation overlaps in this time window
    # Overlap condition: existing.start < new.end AND existing.end > new.start
    conflict_stmt = select(FacilityReservation).where(
        and_(
            FacilityReservation.facility_id == payload.facility_id,
            FacilityReservation.status.in_(["confirmed", "pending"]),
            FacilityReservation.start_time < payload.end_time,
            FacilityReservation.end_time > payload.start_time,
        )
    )
    conflict_res = await db.execute(conflict_stmt)
    conflict = conflict_res.scalars().first()
    if conflict:
        raise HTTPException(
            status_code=409,
            detail=f"Facility schedule conflict: already booked from {conflict.start_time.strftime('%H:%M')} to {conflict.end_time.strftime('%H:%M')} ({conflict.purpose}).",
        )

    # Determine status: Admin and lecturers auto-confirmed; student reservations are pending review
    init_status = "confirmed" if current_user.role in ["admin", "lecturer"] else "pending"

    reservation = FacilityReservation(
        facility_id=payload.facility_id,
        reserved_by_user_id=current_user.id,
        start_time=payload.start_time,
        end_time=payload.end_time,
        purpose=payload.purpose.strip(),
        attendee_count=payload.attendee_count,
        status=init_status,
        equipment_requested=payload.equipment_requested or [],
        created_at=datetime.utcnow(),
    )
    db.add(reservation)
    await db.commit()

    reload_res = await db.execute(
        select(FacilityReservation)
        .options(
            selectinload(FacilityReservation.facility),
            selectinload(FacilityReservation.reserved_by),
        )
        .where(FacilityReservation.id == reservation.id)
    )
    loaded = reload_res.scalars().first()
    return serialize_reservation(loaded)


@router.put("/reservations/{reservation_id}", response_model=FacilityReservationOut)
async def update_facility_reservation(
    reservation_id: int,
    payload: FacilityReservationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve, reject, or cancel a venue reservation."""
    res = await db.execute(
        select(FacilityReservation)
        .options(
            selectinload(FacilityReservation.facility),
            selectinload(FacilityReservation.reserved_by),
        )
        .where(FacilityReservation.id == reservation_id)
    )
    reservation = res.scalars().first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found.")

    # Authorization: Admins can approve/reject/cancel; users can only cancel their own
    if current_user.role not in ["admin", "lecturer"] and reservation.reserved_by_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized to modify this reservation.")

    if current_user.role not in ["admin", "lecturer"] and payload.status in ["confirmed", "rejected"]:
        raise HTTPException(status_code=403, detail="Only administrators can approve or reject venue bookings.")

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(reservation, k, v)

    await db.commit()
    await db.refresh(reservation)
    return serialize_reservation(reservation)
