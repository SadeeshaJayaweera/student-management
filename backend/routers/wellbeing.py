"""backend/routers/wellbeing.py
Enterprise Student Wellbeing and Support Workflows Router
Provides confidential mental health triage, academic counseling appointment scheduling,
crisis escalation protocols, and wellness resource directories.
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
    WellbeingSupportRequest,
    WellbeingAppointment,
    WellbeingResource,
)
from backend.schemas import (
    WellbeingSupportRequestCreate,
    WellbeingSupportRequestStatusUpdate,
    WellbeingSupportRequestOut,
    WellbeingAppointmentCreate,
    WellbeingAppointmentOut,
    WellbeingResourceCreate,
    WellbeingResourceOut,
)
from backend.utils.security import get_current_user, require_roles

router = APIRouter(prefix="/api/wellbeing", tags=["Student Wellbeing & Support"])


def serialize_appointment(a: WellbeingAppointment) -> WellbeingAppointmentOut:
    c_name = a.counselor.full_name if a.counselor else None
    s_name = a.student.user.full_name if (a.student and a.student.user) else None
    return WellbeingAppointmentOut(
        id=a.id,
        request_id=a.request_id,
        counselor_id=a.counselor_id,
        counselor_name=c_name,
        student_id=a.student_id,
        student_name=s_name,
        appointment_type=a.appointment_type,
        scheduled_at=a.scheduled_at,
        duration_minutes=a.duration_minutes,
        location_or_link=a.location_or_link,
        status=a.status,
        meeting_notes=a.meeting_notes,
        created_at=a.created_at,
    )


def serialize_request(r: WellbeingSupportRequest) -> WellbeingSupportRequestOut:
    s_name = r.student.user.full_name if (r.student and r.student.user) else None
    s_num = r.student.student_id if r.student else None
    c_name = r.assigned_counselor.full_name if r.assigned_counselor else None
    appts = [serialize_appointment(a) for a in (r.appointments or [])]

    return WellbeingSupportRequestOut(
        id=r.id,
        institution_id=r.institution_id,
        student_id=r.student_id,
        student_name=s_name,
        student_number=s_num,
        request_type=r.request_type,
        subject=r.subject,
        description=r.description,
        urgency=r.urgency,
        status=r.status,
        assigned_counselor_id=r.assigned_counselor_id,
        assigned_counselor_name=c_name,
        is_confidential=r.is_confidential,
        resolution_notes=r.resolution_notes,
        created_at=r.created_at,
        updated_at=r.updated_at,
        appointments=appts,
    )


# ─── Student Support Requests ────────────────────────────────────────────────

@router.post("/requests", response_model=WellbeingSupportRequestOut, status_code=status.HTTP_201_CREATED)
async def create_support_request(
    payload: WellbeingSupportRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Student submits a confidential mental health, academic stress, or counseling support request."""
    stu_res = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = stu_res.scalars().first()
    if not student:
        raise HTTPException(status_code=403, detail="Only registered students can submit wellbeing requests.")

    req = WellbeingSupportRequest(
        student_id=student.id,
        request_type=payload.request_type,
        subject=payload.subject,
        description=payload.description,
        urgency=payload.urgency,
        status="submitted",
        is_confidential=payload.is_confidential,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(req)
    await db.commit()
    await db.refresh(req)

    # Reload with student relation
    res = await db.execute(
        select(WellbeingSupportRequest)
        .options(
            selectinload(WellbeingSupportRequest.student).selectinload(Student.user),
            selectinload(WellbeingSupportRequest.assigned_counselor),
            selectinload(WellbeingSupportRequest.appointments),
        )
        .where(WellbeingSupportRequest.id == req.id)
    )
    loaded = res.scalars().first()
    return serialize_request(loaded)


@router.get("/requests/my", response_model=List[WellbeingSupportRequestOut])
async def list_my_support_requests(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve all support requests and scheduled appointments submitted by the current student."""
    stu_res = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = stu_res.scalars().first()
    if not student:
        return []

    res = await db.execute(
        select(WellbeingSupportRequest)
        .options(
            selectinload(WellbeingSupportRequest.student).selectinload(Student.user),
            selectinload(WellbeingSupportRequest.assigned_counselor),
            selectinload(WellbeingSupportRequest.appointments).selectinload(WellbeingAppointment.counselor),
            selectinload(WellbeingSupportRequest.appointments).selectinload(WellbeingAppointment.student).selectinload(Student.user),
        )
        .where(WellbeingSupportRequest.student_id == student.id)
        .order_by(desc(WellbeingSupportRequest.created_at))
    )
    requests = res.scalars().all()
    return [serialize_request(r) for r in requests]


# ─── Counselor / Admin Triage & Scheduling ───────────────────────────────────

@router.get("/counselor/requests", response_model=List[WellbeingSupportRequestOut])
async def list_counselor_requests(
    status_filter: Optional[str] = Query(None, description="Filter by status (submitted, assigned, in_progress, resolved)"),
    urgency_filter: Optional[str] = Query(None, description="Filter by urgency (crisis, high, normal, low)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "lecturer")),
):
    """Advisors, mental health counselors, and administrators triage submitted support cases."""
    filters = []
    if status_filter:
        filters.append(WellbeingSupportRequest.status == status_filter)
    if urgency_filter:
        filters.append(WellbeingSupportRequest.urgency == urgency_filter)

    query = (
        select(WellbeingSupportRequest)
        .options(
            selectinload(WellbeingSupportRequest.student).selectinload(Student.user),
            selectinload(WellbeingSupportRequest.assigned_counselor),
            selectinload(WellbeingSupportRequest.appointments).selectinload(WellbeingAppointment.counselor),
            selectinload(WellbeingSupportRequest.appointments).selectinload(WellbeingAppointment.student).selectinload(Student.user),
        )
        .order_by(
            desc(WellbeingSupportRequest.urgency == "crisis"),
            desc(WellbeingSupportRequest.urgency == "high"),
            desc(WellbeingSupportRequest.created_at),
        )
    )
    if filters:
        query = query.where(and_(*filters))

    res = await db.execute(query)
    requests = res.scalars().all()
    return [serialize_request(r) for r in requests]


@router.put("/requests/{request_id}/status", response_model=WellbeingSupportRequestOut)
async def update_request_status(
    request_id: int,
    payload: WellbeingSupportRequestStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "lecturer")),
):
    """Counselor or administrator updates triage status, assigns counselor, and documents resolution notes."""
    res = await db.execute(
        select(WellbeingSupportRequest)
        .options(
            selectinload(WellbeingSupportRequest.student).selectinload(Student.user),
            selectinload(WellbeingSupportRequest.assigned_counselor),
            selectinload(WellbeingSupportRequest.appointments),
        )
        .where(WellbeingSupportRequest.id == request_id)
    )
    req = res.scalars().first()
    if not req:
        raise HTTPException(status_code=404, detail="Support request not found.")

    req.status = payload.status
    if payload.assigned_counselor_id is not None:
        req.assigned_counselor_id = payload.assigned_counselor_id
    elif req.assigned_counselor_id is None:
        req.assigned_counselor_id = current_user.id

    if payload.resolution_notes:
        req.resolution_notes = payload.resolution_notes

    req.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(req)

    # Reload
    re_res = await db.execute(
        select(WellbeingSupportRequest)
        .options(
            selectinload(WellbeingSupportRequest.student).selectinload(Student.user),
            selectinload(WellbeingSupportRequest.assigned_counselor),
            selectinload(WellbeingSupportRequest.appointments),
        )
        .where(WellbeingSupportRequest.id == request_id)
    )
    return serialize_request(re_res.scalars().first())


@router.post("/requests/{request_id}/appointments", response_model=WellbeingAppointmentOut, status_code=status.HTTP_201_CREATED)
async def schedule_counseling_appointment(
    request_id: int,
    payload: WellbeingAppointmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "lecturer")),
):
    """Schedule an in-person or virtual counseling appointment for a support ticket."""
    req_res = await db.execute(
        select(WellbeingSupportRequest).where(WellbeingSupportRequest.id == request_id)
    )
    req = req_res.scalars().first()
    if not req:
        raise HTTPException(status_code=404, detail="Support request not found.")

    appt = WellbeingAppointment(
        request_id=request_id,
        counselor_id=current_user.id,
        student_id=req.student_id,
        appointment_type=payload.appointment_type,
        scheduled_at=payload.scheduled_at,
        duration_minutes=payload.duration_minutes,
        location_or_link=payload.location_or_link,
        status="scheduled",
        meeting_notes=payload.meeting_notes,
        created_at=datetime.utcnow(),
    )
    db.add(appt)
    req.status = "scheduled"
    req.assigned_counselor_id = current_user.id
    req.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(appt)

    # Reload with relations
    res = await db.execute(
        select(WellbeingAppointment)
        .options(
            selectinload(WellbeingAppointment.counselor),
            selectinload(WellbeingAppointment.student).selectinload(Student.user),
        )
        .where(WellbeingAppointment.id == appt.id)
    )
    return serialize_appointment(res.scalars().first())


# ─── Wellbeing Resource Directory ────────────────────────────────────────────

@router.get("/resources", response_model=List[WellbeingResourceOut])
async def list_wellbeing_resources(
    category: Optional[str] = Query(None),
    is_crisis: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Public/student directory of verified wellness guides, hotlines, and mindfulness tools."""
    filters = []
    if category and category != "all":
        filters.append(WellbeingResource.category == category)
    if is_crisis is not None:
        filters.append(WellbeingResource.is_crisis_resource == is_crisis)

    query = select(WellbeingResource).order_by(
        desc(WellbeingResource.is_crisis_resource),
        desc(WellbeingResource.is_featured),
        WellbeingResource.title.asc(),
    )
    if filters:
        query = query.where(and_(*filters))

    res = await db.execute(query)
    return res.scalars().all()


@router.post("/resources", response_model=WellbeingResourceOut, status_code=status.HTTP_201_CREATED)
async def create_wellbeing_resource(
    payload: WellbeingResourceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "lecturer")),
):
    """Staff publishes a verified campus wellness resource, emergency hotline, or self-help guide."""
    res = WellbeingResource(
        title=payload.title,
        category=payload.category,
        description=payload.description,
        content_url=payload.content_url,
        emergency_phone=payload.emergency_phone,
        is_crisis_resource=payload.is_crisis_resource,
        is_featured=payload.is_featured,
        created_at=datetime.utcnow(),
    )
    db.add(res)
    await db.commit()
    await db.refresh(res)
    return res
