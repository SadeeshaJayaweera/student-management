"""backend/routers/timetable.py
Enterprise Timetable and Class Schedule Router
Provides weekly timetable aggregation, room & instructor conflict detection,
slot management, student schedule retrieval, and standard iCalendar (RFC 5545) export.
"""

from datetime import datetime, date, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.models import (
    User,
    Student,
    Lecturer,
    Course,
    Enrollment,
    TimetableSlot,
)
from backend.schemas import (
    TimetableSlotCreate,
    TimetableSlotUpdate,
    TimetableSlotOut,
    ConflictCheckPayload,
    ConflictCheckResponse,
    ScheduleConflict,
    StudentTimetableResponse,
    StudentTimetableDay,
)
from backend.utils.security import get_current_user, require_roles

router = APIRouter(prefix="/api/timetable", tags=["Timetable & Scheduling"])

DAY_NAMES = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

ICAL_DAYS = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]


def times_overlap(start_a: str, end_a: str, start_b: str, end_b: str) -> bool:
    """Check if two time intervals overlap (assuming HH:MM 24-hr format)."""
    return max(start_a, start_b) < min(end_a, end_b)


async def find_slot_conflicts(
    db: AsyncSession,
    day_of_week: int,
    start_time: str,
    end_time: str,
    room: str,
    lecturer_id: Optional[int] = None,
    exclude_slot_id: Optional[int] = None,
) -> List[ScheduleConflict]:
    """Check for room double-bookings and lecturer schedule collisions."""
    conflicts: List[ScheduleConflict] = []

    # Query all active slots on the same day of the week
    query = select(TimetableSlot).where(
        TimetableSlot.day_of_week == day_of_week,
        TimetableSlot.is_active == True,  # noqa: E712
    )
    if exclude_slot_id:
        query = query.where(TimetableSlot.id != exclude_slot_id)

    res = await db.execute(query)
    slots = res.scalars().all()

    for s in slots:
        if times_overlap(start_time, end_time, s.start_time, s.end_time):
            # Check room collision
            if s.room.strip().lower() == room.strip().lower():
                conflicts.append(
                    ScheduleConflict(
                        conflict_type="room_double_booked",
                        slot_id=s.id,
                        title=s.title,
                        day_of_week=s.day_of_week,
                        start_time=s.start_time,
                        end_time=s.end_time,
                        room=s.room,
                        description=f"Room '{s.room}' is already booked for '{s.title}' ({s.start_time} - {s.end_time}).",
                    )
                )

            # Check lecturer collision
            if lecturer_id and s.lecturer_id and s.lecturer_id == lecturer_id:
                conflicts.append(
                    ScheduleConflict(
                        conflict_type="lecturer_overlap",
                        slot_id=s.id,
                        title=s.title,
                        day_of_week=s.day_of_week,
                        start_time=s.start_time,
                        end_time=s.end_time,
                        room=s.room,
                        description=f"Instructor is already scheduled to teach '{s.title}' at {s.room} ({s.start_time} - {s.end_time}).",
                    )
                )

    return conflicts


def serialize_slot(slot: TimetableSlot) -> TimetableSlotOut:
    course_code = slot.course.course_code if slot.course else None
    course_title = slot.course.title if slot.course else None
    lecturer_name = slot.lecturer.full_name if slot.lecturer else None
    return TimetableSlotOut(
        id=slot.id,
        course_id=slot.course_id,
        lecturer_id=slot.lecturer_id,
        day_of_week=slot.day_of_week,
        start_time=slot.start_time,
        end_time=slot.end_time,
        title=slot.title,
        slot_type=slot.slot_type,
        room=slot.room,
        building=slot.building,
        recurrence_pattern=slot.recurrence_pattern,
        is_active=slot.is_active,
        color=slot.color,
        notes=slot.notes,
        course_code=course_code,
        course_title=course_title,
        lecturer_name=lecturer_name,
        created_at=slot.created_at,
        updated_at=slot.updated_at,
    )


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/conflicts/check", response_model=ConflictCheckResponse)
async def check_conflicts(
    payload: ConflictCheckPayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Validate potential room and lecturer collisions before saving a slot."""
    conflicts = await find_slot_conflicts(
        db=db,
        day_of_week=payload.day_of_week,
        start_time=payload.start_time,
        end_time=payload.end_time,
        room=payload.room,
        lecturer_id=payload.lecturer_id,
        exclude_slot_id=payload.exclude_slot_id,
    )
    return ConflictCheckResponse(
        has_conflict=len(conflicts) > 0,
        conflicts=conflicts,
    )


@router.get("/student", response_model=StudentTimetableResponse)
async def get_student_timetable(
    student_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch the authenticated student's personalized weekly timetable across enrolled courses."""
    target_student: Optional[Student] = None

    if current_user.role == "student":
        res = await db.execute(select(Student).where(Student.user_id == current_user.id))
        target_student = res.scalars().first()
        if not target_student:
            raise HTTPException(status_code=404, detail="Student profile not found.")
    else:
        if student_id:
            res = await db.execute(select(Student).where(Student.student_id == student_id))
            target_student = res.scalars().first()
            if not target_student:
                raise HTTPException(status_code=404, detail=f"Student {student_id} not found.")
        else:
            # If user is lecturer or admin without student_id, fetch all active slots
            # or slots for lecturer's assigned courses
            pass

    # Retrieve enrolled courses
    enrolled_course_ids: List[int] = []
    if target_student:
        enr_res = await db.execute(
            select(Enrollment.course_id).where(
                Enrollment.student_id == target_student.id,
                Enrollment.status.in_(["enrolled", "active", "completed"]),
            )
        )
        enrolled_course_ids = [row[0] for row in enr_res.all()]

    # Query timetable slots
    slots_query = (
        select(TimetableSlot)
        .options(selectinload(TimetableSlot.course), selectinload(TimetableSlot.lecturer))
        .where(TimetableSlot.is_active == True)  # noqa: E712
    )

    if target_student:
        if enrolled_course_ids:
            slots_query = slots_query.where(
                or_(
                    TimetableSlot.course_id.in_(enrolled_course_ids),
                    TimetableSlot.course_id.is_(None),  # campus-wide sessions
                )
            )
        else:
            slots_query = slots_query.where(TimetableSlot.course_id.is_(None))
    elif current_user.role == "lecturer":
        slots_query = slots_query.where(TimetableSlot.lecturer_id == current_user.id)

    slots_query = slots_query.order_by(TimetableSlot.day_of_week, TimetableSlot.start_time)
    slots_res = await db.execute(slots_query)
    slots = slots_res.scalars().all()

    # Detect student schedule overlaps
    conflicts: List[ScheduleConflict] = []
    for i in range(len(slots)):
        for j in range(i + 1, len(slots)):
            s1 = slots[i]
            s2 = slots[j]
            if s1.day_of_week == s2.day_of_week and times_overlap(
                s1.start_time, s1.end_time, s2.start_time, s2.end_time
            ):
                conflicts.append(
                    ScheduleConflict(
                        conflict_type="student_overlap",
                        slot_id=s2.id,
                        title=s2.title,
                        day_of_week=s2.day_of_week,
                        start_time=s2.start_time,
                        end_time=s2.end_time,
                        room=s2.room,
                        description=f"Course collision: '{s1.title}' ({s1.start_time}-{s1.end_time}) overlaps with '{s2.title}' ({s2.start_time}-{s2.end_time}).",
                    )
                )

    # Group by day
    days_data: List[StudentTimetableDay] = []
    for day_idx in range(7):
        day_slots = [serialize_slot(s) for s in slots if s.day_of_week == day_idx]
        days_data.append(
            StudentTimetableDay(
                day_of_week=day_idx,
                day_name=DAY_NAMES[day_idx],
                slots=day_slots,
            )
        )

    s_id = target_student.student_id if target_student else "CURRENT_USER"
    s_name = current_user.full_name

    return StudentTimetableResponse(
        student_id=s_id,
        student_name=s_name,
        schedule=days_data,
        total_slots=len(slots),
        conflicts_detected=conflicts,
    )


@router.get("/courses/{course_id}", response_model=List[TimetableSlotOut])
async def get_course_timetable(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve all schedule slots defined for a specific course."""
    res = await db.execute(
        select(TimetableSlot)
        .options(selectinload(TimetableSlot.course), selectinload(TimetableSlot.lecturer))
        .where(TimetableSlot.course_id == course_id, TimetableSlot.is_active == True)  # noqa: E712
        .order_by(TimetableSlot.day_of_week, TimetableSlot.start_time)
    )
    slots = res.scalars().all()
    return [serialize_slot(s) for s in slots]


@router.post("/slots", response_model=TimetableSlotOut, status_code=status.HTTP_201_CREATED)
async def create_timetable_slot(
    payload: TimetableSlotCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("lecturer", "admin")),
):
    """Create a new timetable slot with conflict verification."""
    # Check course if specified
    if payload.course_id:
        c_res = await db.execute(select(Course).where(Course.id == payload.course_id))
        course = c_res.scalars().first()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found.")

    # Validate time order
    if payload.start_time >= payload.end_time:
        raise HTTPException(
            status_code=400,
            detail="start_time must be strictly before end_time.",
        )

    # Conflict check
    conflicts = await find_slot_conflicts(
        db=db,
        day_of_week=payload.day_of_week,
        start_time=payload.start_time,
        end_time=payload.end_time,
        room=payload.room,
        lecturer_id=payload.lecturer_id or (current_user.id if current_user.role == "lecturer" else None),
    )

    if conflicts and not payload.allow_conflicts:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "Schedule conflict detected.",
                "conflicts": [c.model_dump() for c in conflicts],
            },
        )

    assigned_lecturer_id = payload.lecturer_id
    if not assigned_lecturer_id and current_user.role == "lecturer":
        assigned_lecturer_id = current_user.id

    new_slot = TimetableSlot(
        course_id=payload.course_id,
        lecturer_id=assigned_lecturer_id,
        day_of_week=payload.day_of_week,
        start_time=payload.start_time,
        end_time=payload.end_time,
        title=payload.title,
        slot_type=payload.slot_type,
        room=payload.room,
        building=payload.building,
        recurrence_pattern=payload.recurrence_pattern,
        is_active=payload.is_active,
        color=payload.color,
        notes=payload.notes,
    )
    db.add(new_slot)
    await db.commit()
    await db.refresh(new_slot)

    # Reload with course and lecturer
    res = await db.execute(
        select(TimetableSlot)
        .options(selectinload(TimetableSlot.course), selectinload(TimetableSlot.lecturer))
        .where(TimetableSlot.id == new_slot.id)
    )
    loaded_slot = res.scalars().first()
    return serialize_slot(loaded_slot)


@router.put("/slots/{slot_id}", response_model=TimetableSlotOut)
async def update_timetable_slot(
    slot_id: int,
    payload: TimetableSlotUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("lecturer", "admin")),
):
    """Update an existing schedule slot with conflict checking."""
    res = await db.execute(
        select(TimetableSlot)
        .options(selectinload(TimetableSlot.course), selectinload(TimetableSlot.lecturer))
        .where(TimetableSlot.id == slot_id)
    )
    slot = res.scalars().first()
    if not slot:
        raise HTTPException(status_code=404, detail="Timetable slot not found.")

    target_day = payload.day_of_week if payload.day_of_week is not None else slot.day_of_week
    target_start = payload.start_time if payload.start_time is not None else slot.start_time
    target_end = payload.end_time if payload.end_time is not None else slot.end_time
    target_room = payload.room if payload.room is not None else slot.room
    target_lecturer = payload.lecturer_id if payload.lecturer_id is not None else slot.lecturer_id

    if target_start >= target_end:
        raise HTTPException(
            status_code=400,
            detail="start_time must be strictly before end_time.",
        )

    conflicts = await find_slot_conflicts(
        db=db,
        day_of_week=target_day,
        start_time=target_start,
        end_time=target_end,
        room=target_room,
        lecturer_id=target_lecturer,
        exclude_slot_id=slot.id,
    )

    if conflicts and not payload.allow_conflicts:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "Schedule conflict detected on update.",
                "conflicts": [c.model_dump() for c in conflicts],
            },
        )

    if payload.course_id is not None:
        slot.course_id = payload.course_id
    if payload.lecturer_id is not None:
        slot.lecturer_id = payload.lecturer_id
    if payload.day_of_week is not None:
        slot.day_of_week = payload.day_of_week
    if payload.start_time is not None:
        slot.start_time = payload.start_time
    if payload.end_time is not None:
        slot.end_time = payload.end_time
    if payload.title is not None:
        slot.title = payload.title
    if payload.slot_type is not None:
        slot.slot_type = payload.slot_type
    if payload.room is not None:
        slot.room = payload.room
    if payload.building is not None:
        slot.building = payload.building
    if payload.recurrence_pattern is not None:
        slot.recurrence_pattern = payload.recurrence_pattern
    if payload.is_active is not None:
        slot.is_active = payload.is_active
    if payload.color is not None:
        slot.color = payload.color
    if payload.notes is not None:
        slot.notes = payload.notes

    await db.commit()
    await db.refresh(slot)

    # Reload relationships
    r_res = await db.execute(
        select(TimetableSlot)
        .options(selectinload(TimetableSlot.course), selectinload(TimetableSlot.lecturer))
        .where(TimetableSlot.id == slot.id)
    )
    loaded_slot = r_res.scalars().first()
    return serialize_slot(loaded_slot)


@router.delete("/slots/{slot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_timetable_slot(
    slot_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("lecturer", "admin")),
):
    """Deactivate or remove a schedule slot."""
    res = await db.execute(select(TimetableSlot).where(TimetableSlot.id == slot_id))
    slot = res.scalars().first()
    if not slot:
        raise HTTPException(status_code=404, detail="Timetable slot not found.")

    await db.delete(slot)
    await db.commit()
    return None


@router.get("/ical/export")
async def export_student_calendar_ical(
    student_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate standard RFC 5545 iCalendar feed for student schedule subscription."""
    # Fetch timetable using standard logic
    timetable_res = await get_student_timetable(
        student_id=student_id, db=db, current_user=current_user
    )

    now_stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    today = date.today()

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//NSBM EduSphere//Academic Timetable//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:EduSphere Timetable - {timetable_res.student_name}",
        "X-WR-TIMEZONE:UTC",
    ]

    for day in timetable_res.schedule:
        for slot in day.slots:
            byday = ICAL_DAYS[slot.day_of_week]
            # Calculate next occurrence of this day
            days_ahead = (slot.day_of_week - today.weekday()) % 7
            event_date = today + timedelta(days=days_ahead)

            start_hh, start_mm = slot.start_time.split(":")
            end_hh, end_mm = slot.end_time.split(":")

            dt_start = f"{event_date.strftime('%Y%m%d')}T{start_hh}{start_mm}00"
            dt_end = f"{event_date.strftime('%Y%m%d')}T{end_hh}{end_mm}00"

            summary = f"{slot.course_code + ': ' if slot.course_code else ''}{slot.title}"
            location = f"{slot.room}{' - ' + slot.building if slot.building else ''}"
            desc = f"{slot.slot_type.upper()} | Instructor: {slot.lecturer_name or 'TBA'} | {slot.notes or ''}".strip()

            lines.extend([
                "BEGIN:VEVENT",
                f"UID:edusphere-slot-{slot.id}@edusphere.nsbm.ac.lk",
                f"DTSTAMP:{now_stamp}",
                f"DTSTART:{dt_start}",
                f"DTEND:{dt_end}",
                f"RRULE:FREQ=WEEKLY;BYDAY={byday}",
                f"SUMMARY:{summary}",
                f"LOCATION:{location}",
                f"DESCRIPTION:{desc}",
                f"STATUS:CONFIRMED",
                "END:VEVENT",
            ])

    lines.append("END:VCALENDAR")
    ical_content = "\r\n".join(lines) + "\r\n"

    return Response(
        content=ical_content,
        media_type="text/calendar",
        headers={
            "Content-Disposition": f'attachment; filename="student_timetable_{timetable_res.student_id}.ics"',
            "Cache-Control": "no-cache",
        },
    )
