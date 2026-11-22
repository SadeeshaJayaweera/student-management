"""backend/routers/hostels.py
Hostel and Accommodation Management Router
Provides university hall of residence management, block/room inventories,
student room allocation workflows, check-in/check-out lifecycle,
and facility maintenance ticketing.
"""

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
    HostelBuilding,
    HostelRoom,
    HostelAllocation,
    HostelMaintenanceRequest,
)
from backend.schemas import (
    HostelBuildingCreate,
    HostelBuildingUpdate,
    HostelBuildingOut,
    HostelRoomCreate,
    HostelRoomUpdate,
    HostelRoomOut,
    HostelAllocationCreate,
    HostelAllocationUpdate,
    HostelAllocationOut,
    HostelMaintenanceRequestCreate,
    HostelMaintenanceRequestUpdate,
    HostelMaintenanceRequestOut,
    HostelOccupancySummaryOut,
)
from backend.utils.security import get_current_user, require_roles

router = APIRouter(prefix="/api/hostels", tags=["Hostel & Accommodation Management"])


# ─── Operational Dashboard / Summary ────────────────────────────────────────

@router.get("/summary", response_model=HostelOccupancySummaryOut)
async def get_hostel_occupancy_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Institutional overview of campus residence occupancy and pending repairs."""
    # Count buildings
    b_res = await db.execute(select(func.count(HostelBuilding.id)).where(HostelBuilding.is_active == True))
    total_bldgs = b_res.scalar() or 0

    # Count rooms and capacities
    r_res = await db.execute(
        select(
            func.count(HostelRoom.id),
            func.sum(HostelRoom.capacity),
            func.sum(HostelRoom.occupied_count),
        )
    )
    r_row = r_res.first()
    tot_rooms = r_row[0] or 0
    tot_capacity = int(r_row[1] or 0)
    occ_beds = int(r_row[2] or 0)
    avail_beds = max(0, tot_capacity - occ_beds)
    occ_rate = round((occ_beds / tot_capacity * 100), 1) if tot_capacity > 0 else 0.0

    # Count active maintenance tickets
    m_res = await db.execute(
        select(func.count(HostelMaintenanceRequest.id)).where(
            HostelMaintenanceRequest.status.in_(["reported", "in_progress"])
        )
    )
    active_maint = m_res.scalar() or 0

    return HostelOccupancySummaryOut(
        total_buildings=total_bldgs,
        total_rooms=tot_rooms,
        total_capacity=tot_capacity,
        occupied_beds=occ_beds,
        available_beds=avail_beds,
        occupancy_rate=occ_rate,
        active_maintenance_issues=active_maint,
    )


# ─── Hostel Buildings ────────────────────────────────────────────────────────

@router.get("/buildings", response_model=List[HostelBuildingOut])
async def list_hostel_buildings(
    gender_type: Optional[str] = Query(None, pattern="^(male|female|mixed)$"),
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List residence halls and accommodation blocks."""
    stmt = (
        select(HostelBuilding)
        .options(selectinload(HostelBuilding.rooms))
        .order_by(HostelBuilding.name)
    )
    filters = []
    if active_only:
        filters.append(HostelBuilding.is_active == True)
    if gender_type:
        filters.append(HostelBuilding.gender_type == gender_type)

    if filters:
        stmt = stmt.where(and_(*filters))

    res = await db.execute(stmt)
    buildings = res.scalars().all()

    out = []
    for b in buildings:
        rooms_list = b.rooms or []
        tot_rooms = len(rooms_list)
        tot_cap = sum(r.capacity for r in rooms_list)
        occ = sum(r.occupied_count for r in rooms_list)
        avail = max(0, tot_cap - occ)

        rooms_out = [
            HostelRoomOut(
                id=r.id,
                building_id=r.building_id,
                building_name=b.name,
                room_number=r.room_number,
                floor=r.floor,
                room_type=r.room_type,
                capacity=r.capacity,
                occupied_count=r.occupied_count,
                monthly_fee=r.monthly_fee,
                status=r.status,
                created_at=r.created_at,
            )
            for r in rooms_list
        ]

        out.append(
            HostelBuildingOut(
                id=b.id,
                name=b.name,
                code=b.code,
                gender_type=b.gender_type,
                total_floors=b.total_floors,
                warden_name=b.warden_name,
                warden_contact=b.warden_contact,
                campus_location=b.campus_location,
                amenities=b.amenities,
                is_active=b.is_active,
                total_rooms=tot_rooms,
                total_capacity=tot_cap,
                occupied_beds=occ,
                available_beds=avail,
                created_at=b.created_at,
                rooms=rooms_out,
            )
        )
    return out


@router.post("/buildings", response_model=HostelBuildingOut, status_code=status.HTTP_201_CREATED)
async def create_hostel_building(
    payload: HostelBuildingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Register a new residence building or dormitory block."""
    existing = await db.execute(
        select(HostelBuilding).where(
            or_(HostelBuilding.code == payload.code.upper(), HostelBuilding.name == payload.name)
        )
    )
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="Hostel building with this code or name already exists.")

    building = HostelBuilding(
        name=payload.name,
        code=payload.code.upper(),
        gender_type=payload.gender_type,
        total_floors=payload.total_floors,
        warden_name=payload.warden_name,
        warden_contact=payload.warden_contact,
        campus_location=payload.campus_location,
        amenities=payload.amenities or [],
        is_active=payload.is_active,
        created_at=datetime.utcnow(),
    )
    db.add(building)
    await db.commit()
    await db.refresh(building)

    return HostelBuildingOut(
        id=building.id,
        name=building.name,
        code=building.code,
        gender_type=building.gender_type,
        total_floors=building.total_floors,
        warden_name=building.warden_name,
        warden_contact=building.warden_contact,
        campus_location=building.campus_location,
        amenities=building.amenities,
        is_active=building.is_active,
        total_rooms=0,
        total_capacity=0,
        occupied_beds=0,
        available_beds=0,
        created_at=building.created_at,
        rooms=[],
    )


@router.get("/buildings/{building_id}", response_model=HostelBuildingOut)
async def get_hostel_building(
    building_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve residence hall details including its room roster."""
    res = await db.execute(
        select(HostelBuilding)
        .options(selectinload(HostelBuilding.rooms))
        .where(HostelBuilding.id == building_id)
    )
    b = res.scalars().first()
    if not b:
        raise HTTPException(status_code=404, detail="Hostel building not found.")

    rooms_list = b.rooms or []
    tot_rooms = len(rooms_list)
    tot_cap = sum(r.capacity for r in rooms_list)
    occ = sum(r.occupied_count for r in rooms_list)
    avail = max(0, tot_cap - occ)

    rooms_out = [
        HostelRoomOut(
            id=r.id,
            building_id=r.building_id,
            building_name=b.name,
            room_number=r.room_number,
            floor=r.floor,
            room_type=r.room_type,
            capacity=r.capacity,
            occupied_count=r.occupied_count,
            monthly_fee=r.monthly_fee,
            status=r.status,
            created_at=r.created_at,
        )
        for r in rooms_list
    ]

    return HostelBuildingOut(
        id=b.id,
        name=b.name,
        code=b.code,
        gender_type=b.gender_type,
        total_floors=b.total_floors,
        warden_name=b.warden_name,
        warden_contact=b.warden_contact,
        campus_location=b.campus_location,
        amenities=b.amenities,
        is_active=b.is_active,
        total_rooms=tot_rooms,
        total_capacity=tot_cap,
        occupied_beds=occ,
        available_beds=avail,
        created_at=b.created_at,
        rooms=rooms_out,
    )


@router.put("/buildings/{building_id}", response_model=HostelBuildingOut)
async def update_hostel_building(
    building_id: int,
    payload: HostelBuildingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Update building amenities, warden contact, or operational status."""
    res = await db.execute(
        select(HostelBuilding)
        .options(selectinload(HostelBuilding.rooms))
        .where(HostelBuilding.id == building_id)
    )
    b = res.scalars().first()
    if not b:
        raise HTTPException(status_code=404, detail="Hostel building not found.")

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(b, k, v)

    await db.commit()
    await db.refresh(b)
    return await get_hostel_building(building_id, db, current_user)


# ─── Hostel Rooms ────────────────────────────────────────────────────────────

@router.get("/rooms", response_model=List[HostelRoomOut])
async def list_hostel_rooms(
    building_id: Optional[int] = Query(None),
    room_type: Optional[str] = Query(None, pattern="^(single|double|triple|quad)$"),
    status_filter: Optional[str] = Query(None, pattern="^(available|full|maintenance)$"),
    available_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List residence rooms with vacancy and type filters."""
    stmt = (
        select(HostelRoom)
        .options(selectinload(HostelRoom.building))
        .order_by(HostelRoom.building_id, HostelRoom.room_number)
    )
    filters = []
    if building_id:
        filters.append(HostelRoom.building_id == building_id)
    if room_type:
        filters.append(HostelRoom.room_type == room_type)
    if status_filter:
        filters.append(HostelRoom.status == status_filter)
    if available_only:
        filters.append(HostelRoom.status == "available")
        filters.append(HostelRoom.occupied_count < HostelRoom.capacity)

    if filters:
        stmt = stmt.where(and_(*filters))

    res = await db.execute(stmt)
    rooms = res.scalars().all()

    return [
        HostelRoomOut(
            id=r.id,
            building_id=r.building_id,
            building_name=r.building.name if r.building else None,
            room_number=r.room_number,
            floor=r.floor,
            room_type=r.room_type,
            capacity=r.capacity,
            occupied_count=r.occupied_count,
            monthly_fee=r.monthly_fee,
            status=r.status,
            created_at=r.created_at,
        )
        for r in rooms
    ]


@router.post("/rooms", response_model=HostelRoomOut, status_code=status.HTTP_201_CREATED)
async def create_hostel_room(
    payload: HostelRoomCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Add a room unit to a residence building."""
    b_res = await db.execute(select(HostelBuilding).where(HostelBuilding.id == payload.building_id))
    bldg = b_res.scalars().first()
    if not bldg:
        raise HTTPException(status_code=404, detail="Hostel building not found.")

    dup_check = await db.execute(
        select(HostelRoom).where(
            and_(
                HostelRoom.building_id == payload.building_id,
                HostelRoom.room_number == payload.room_number,
            )
        )
    )
    if dup_check.scalars().first():
        raise HTTPException(status_code=400, detail="Room number already exists in this building.")

    room = HostelRoom(
        building_id=payload.building_id,
        room_number=payload.room_number,
        floor=payload.floor,
        room_type=payload.room_type,
        capacity=payload.capacity,
        occupied_count=0,
        monthly_fee=payload.monthly_fee,
        status=payload.status,
        created_at=datetime.utcnow(),
    )
    db.add(room)
    await db.commit()
    await db.refresh(room)

    return HostelRoomOut(
        id=room.id,
        building_id=room.building_id,
        building_name=bldg.name,
        room_number=room.room_number,
        floor=room.floor,
        room_type=room.room_type,
        capacity=room.capacity,
        occupied_count=room.occupied_count,
        monthly_fee=room.monthly_fee,
        status=room.status,
        created_at=room.created_at,
    )


@router.put("/rooms/{room_id}", response_model=HostelRoomOut)
async def update_hostel_room(
    room_id: int,
    payload: HostelRoomUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Modify room fee, capacity, or maintenance status."""
    res = await db.execute(
        select(HostelRoom).options(selectinload(HostelRoom.building)).where(HostelRoom.id == room_id)
    )
    room = res.scalars().first()
    if not room:
        raise HTTPException(status_code=404, detail="Hostel room not found.")

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(room, k, v)

    # Recalculate status if capacity changed
    if room.occupied_count >= room.capacity:
        room.status = "full"
    elif room.status != "maintenance":
        room.status = "available"

    await db.commit()
    await db.refresh(room)

    return HostelRoomOut(
        id=room.id,
        building_id=room.building_id,
        building_name=room.building.name if room.building else None,
        room_number=room.room_number,
        floor=room.floor,
        room_type=room.room_type,
        capacity=room.capacity,
        occupied_count=room.occupied_count,
        monthly_fee=room.monthly_fee,
        status=room.status,
        created_at=room.created_at,
    )


# ─── Room Allocations ────────────────────────────────────────────────────────

def serialize_allocation(alloc: HostelAllocation) -> HostelAllocationOut:
    s_name = alloc.student.user.full_name if (alloc.student and alloc.student.user) else None
    s_reg = alloc.student.student_id if alloc.student else None
    r_num = alloc.room.room_number if alloc.room else None
    b_name = alloc.room.building.name if (alloc.room and alloc.room.building) else None

    return HostelAllocationOut(
        id=alloc.id,
        student_id=alloc.student_id,
        student_name=s_name,
        student_reg_number=s_reg,
        room_id=alloc.room_id,
        room_number=r_num,
        building_name=b_name,
        academic_year=alloc.academic_year,
        semester=alloc.semester,
        check_in_date=alloc.check_in_date,
        check_out_date=alloc.check_out_date,
        status=alloc.status,
        deposit_paid=alloc.deposit_paid,
        emergency_contact=alloc.emergency_contact,
        notes=alloc.notes,
        created_at=alloc.created_at,
    )


@router.get("/allocations", response_model=List[HostelAllocationOut])
async def list_hostel_allocations(
    student_id: Optional[int] = Query(None),
    room_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, pattern="^(pending|active|checked_out|cancelled)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Query student room assignments and booking records."""
    stmt = (
        select(HostelAllocation)
        .options(
            selectinload(HostelAllocation.student).selectinload(Student.user),
            selectinload(HostelAllocation.room).selectinload(HostelRoom.building),
        )
        .order_by(desc(HostelAllocation.created_at))
    )

    filters = []
    # Students can only view their own allocations unless admin/lecturer
    if current_user.role == "student":
        stu_res = await db.execute(select(Student).where(Student.user_id == current_user.id))
        stu = stu_res.scalars().first()
        if not stu:
            return []
        filters.append(HostelAllocation.student_id == stu.id)
    elif student_id:
        filters.append(HostelAllocation.student_id == student_id)

    if room_id:
        filters.append(HostelAllocation.room_id == room_id)
    if status_filter:
        filters.append(HostelAllocation.status == status_filter)

    if filters:
        stmt = stmt.where(and_(*filters))

    res = await db.execute(stmt)
    allocations = res.scalars().all()
    return [serialize_allocation(a) for a in allocations]


@router.get("/allocations/my", response_model=Optional[HostelAllocationOut])
async def get_my_active_allocation(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve current student's active room accommodation."""
    stu_res = await db.execute(select(Student).where(Student.user_id == current_user.id))
    stu = stu_res.scalars().first()
    if not stu:
        return None

    res = await db.execute(
        select(HostelAllocation)
        .options(
            selectinload(HostelAllocation.student).selectinload(Student.user),
            selectinload(HostelAllocation.room).selectinload(HostelRoom.building),
        )
        .where(
            and_(
                HostelAllocation.student_id == stu.id,
                HostelAllocation.status == "active",
            )
        )
    )
    alloc = res.scalars().first()
    return serialize_allocation(alloc) if alloc else None


@router.post("/allocations", response_model=HostelAllocationOut, status_code=status.HTTP_201_CREATED)
async def create_hostel_allocation(
    payload: HostelAllocationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Assign an undergraduate/postgraduate student to a hostel room bed."""
    # Verify student
    stu_res = await db.execute(select(Student).where(Student.id == payload.student_id))
    student = stu_res.scalars().first()
    if not student:
        raise HTTPException(status_code=404, detail="Student record not found.")

    # Check if student already has an active allocation
    active_check = await db.execute(
        select(HostelAllocation).where(
            and_(
                HostelAllocation.student_id == payload.student_id,
                HostelAllocation.status == "active",
            )
        )
    )
    if active_check.scalars().first():
        raise HTTPException(status_code=400, detail="Student already has an active hostel allocation.")

    # Check room vacancy
    room_res = await db.execute(
        select(HostelRoom)
        .options(selectinload(HostelRoom.building))
        .where(HostelRoom.id == payload.room_id)
    )
    room = room_res.scalars().first()
    if not room:
        raise HTTPException(status_code=404, detail="Hostel room not found.")

    if room.status == "maintenance":
        raise HTTPException(status_code=400, detail="Cannot allocate: room is currently under maintenance.")

    if room.occupied_count >= room.capacity:
        raise HTTPException(status_code=400, detail="Cannot allocate: room is at maximum capacity.")

    # Create allocation
    alloc = HostelAllocation(
        student_id=payload.student_id,
        room_id=payload.room_id,
        academic_year=payload.academic_year,
        semester=payload.semester,
        check_in_date=payload.check_in_date,
        check_out_date=payload.check_out_date,
        status="active",
        deposit_paid=payload.deposit_paid,
        emergency_contact=payload.emergency_contact,
        notes=payload.notes,
        created_at=datetime.utcnow(),
    )
    db.add(alloc)

    # Increment room occupancy
    room.occupied_count += 1
    if room.occupied_count >= room.capacity:
        room.status = "full"

    await db.commit()

    reload_res = await db.execute(
        select(HostelAllocation)
        .options(
            selectinload(HostelAllocation.student).selectinload(Student.user),
            selectinload(HostelAllocation.room).selectinload(HostelRoom.building),
        )
        .where(HostelAllocation.id == alloc.id)
    )
    loaded = reload_res.scalars().first()
    return serialize_allocation(loaded)


@router.put("/allocations/{allocation_id}", response_model=HostelAllocationOut)
async def update_hostel_allocation(
    allocation_id: int,
    payload: HostelAllocationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Process student check-out, status change, or notes update."""
    res = await db.execute(
        select(HostelAllocation)
        .options(
            selectinload(HostelAllocation.student).selectinload(Student.user),
            selectinload(HostelAllocation.room).selectinload(HostelRoom.building),
        )
        .where(HostelAllocation.id == allocation_id)
    )
    alloc = res.scalars().first()
    if not alloc:
        raise HTTPException(status_code=404, detail="Hostel allocation record not found.")

    prev_status = alloc.status

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(alloc, k, v)

    # If transitioning from active to checked_out/cancelled, release the bed
    if prev_status == "active" and alloc.status in ["checked_out", "cancelled"]:
        if alloc.room:
            alloc.room.occupied_count = max(0, alloc.room.occupied_count - 1)
            if alloc.room.status != "maintenance":
                alloc.room.status = "available"
        if not alloc.check_out_date:
            alloc.check_out_date = date.today()

    await db.commit()
    await db.refresh(alloc)
    return serialize_allocation(alloc)


# ─── Maintenance Requests ────────────────────────────────────────────────────

def serialize_maintenance(req: HostelMaintenanceRequest) -> HostelMaintenanceRequestOut:
    r_num = req.room.room_number if req.room else None
    b_name = req.room.building.name if (req.room and req.room.building) else None
    s_name = req.student.user.full_name if (req.student and req.student.user) else None

    return HostelMaintenanceRequestOut(
        id=req.id,
        room_id=req.room_id,
        room_number=r_num,
        building_name=b_name,
        student_id=req.student_id,
        student_name=s_name,
        issue_type=req.issue_type,
        description=req.description,
        priority=req.priority,
        status=req.status,
        resolution_notes=req.resolution_notes,
        reported_at=req.reported_at,
        resolved_at=req.resolved_at,
    )


@router.get("/maintenance", response_model=List[HostelMaintenanceRequestOut])
async def list_maintenance_requests(
    room_id: Optional[int] = Query(None),
    issue_type: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List facility repair requests with status and severity filters."""
    stmt = (
        select(HostelMaintenanceRequest)
        .options(
            selectinload(HostelMaintenanceRequest.room).selectinload(HostelRoom.building),
            selectinload(HostelMaintenanceRequest.student).selectinload(Student.user),
        )
        .order_by(desc(HostelMaintenanceRequest.reported_at))
    )

    filters = []
    if current_user.role == "student":
        stu_res = await db.execute(select(Student).where(Student.user_id == current_user.id))
        stu = stu_res.scalars().first()
        if stu:
            filters.append(HostelMaintenanceRequest.student_id == stu.id)
    if room_id:
        filters.append(HostelMaintenanceRequest.room_id == room_id)
    if issue_type:
        filters.append(HostelMaintenanceRequest.issue_type == issue_type)
    if status_filter:
        filters.append(HostelMaintenanceRequest.status == status_filter)
    if priority:
        filters.append(HostelMaintenanceRequest.priority == priority)

    if filters:
        stmt = stmt.where(and_(*filters))

    res = await db.execute(stmt)
    records = res.scalars().all()
    return [serialize_maintenance(r) for r in records]


@router.post("/maintenance", response_model=HostelMaintenanceRequestOut, status_code=status.HTTP_201_CREATED)
async def create_maintenance_request(
    payload: HostelMaintenanceRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit a room repair ticket (plumbing, electrical, furniture, cleanliness)."""
    room_res = await db.execute(select(HostelRoom).where(HostelRoom.id == payload.room_id))
    room = room_res.scalars().first()
    if not room:
        raise HTTPException(status_code=404, detail="Hostel room not found.")

    # Find student ID
    stu_id = None
    if current_user.role == "student":
        stu_res = await db.execute(select(Student).where(Student.user_id == current_user.id))
        stu = stu_res.scalars().first()
        if not stu:
            raise HTTPException(status_code=400, detail="Student profile not found for this user.")
        stu_id = stu.id
    else:
        # If admin/warden submits on behalf of room, find first allocated student or self
        alloc_res = await db.execute(
            select(HostelAllocation).where(
                and_(HostelAllocation.room_id == payload.room_id, HostelAllocation.status == "active")
            )
        )
        first_alloc = alloc_res.scalars().first()
        if first_alloc:
            stu_id = first_alloc.student_id
        else:
            # fallback to any existing student
            any_stu = await db.execute(select(Student).limit(1))
            st = any_stu.scalars().first()
            if not st:
                raise HTTPException(status_code=400, detail="No student record exists to associate with ticket.")
            stu_id = st.id

    req = HostelMaintenanceRequest(
        room_id=payload.room_id,
        student_id=stu_id,
        issue_type=payload.issue_type,
        description=payload.description,
        priority=payload.priority,
        status="reported",
        reported_at=datetime.utcnow(),
    )
    db.add(req)
    await db.commit()

    reload_res = await db.execute(
        select(HostelMaintenanceRequest)
        .options(
            selectinload(HostelMaintenanceRequest.room).selectinload(HostelRoom.building),
            selectinload(HostelMaintenanceRequest.student).selectinload(Student.user),
        )
        .where(HostelMaintenanceRequest.id == req.id)
    )
    loaded = reload_res.scalars().first()
    return serialize_maintenance(loaded)


@router.put("/maintenance/{request_id}", response_model=HostelMaintenanceRequestOut)
async def update_maintenance_request(
    request_id: int,
    payload: HostelMaintenanceRequestUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Warden or facilities staff resolves or updates ticket progress."""
    res = await db.execute(
        select(HostelMaintenanceRequest)
        .options(
            selectinload(HostelMaintenanceRequest.room).selectinload(HostelRoom.building),
            selectinload(HostelMaintenanceRequest.student).selectinload(Student.user),
        )
        .where(HostelMaintenanceRequest.id == request_id)
    )
    req = res.scalars().first()
    if not req:
        raise HTTPException(status_code=404, detail="Maintenance ticket not found.")

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(req, k, v)

    if req.status == "resolved" and not req.resolved_at:
        req.resolved_at = datetime.utcnow()

    await db.commit()
    await db.refresh(req)
    return serialize_maintenance(req)
