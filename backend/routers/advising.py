"""
NSBM EduSphere — Academic Advising and Student Support Router
Manages advisor assignments, advising meeting sessions, confidential advising notes,
and student support intervention cases.
"""
from typing import List, Optional
from datetime import datetime, date
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.models import (
    User, UserRole, Student, Lecturer,
    AcademicAdvisorAssignment, AdvisingSession,
    StudentSupportCase, SupportCaseNote
)
from backend.schemas import (
    AdvisorAssignmentCreate, AdvisorAssignmentOut,
    AdvisingSessionCreate, AdvisingSessionUpdate, AdvisingSessionOut,
    StudentSupportCaseCreate, StudentSupportCaseUpdate, StudentSupportCaseOut,
    SupportCaseNoteCreate, SupportCaseNoteOut
)
from backend.utils.security import get_current_user, require_roles

router = APIRouter(prefix="/api/advising", tags=["Academic Advising and Support"])


def _mask_confidential_session_notes(session: AdvisingSession, current_user: User) -> AdvisingSessionOut:
    out = AdvisingSessionOut.model_validate(session)
    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    is_staff = role_val in {UserRole.ADMIN.value, UserRole.DEAN.value, UserRole.REGISTRAR.value, UserRole.LECTURER.value}
    if not is_staff:
        out.confidential_notes = None
    return out


# ─── Advisor Assignments ───────────────────────────────────────────────────────

@router.post("/assignments", response_model=AdvisorAssignmentOut, status_code=status.HTTP_201_CREATED)
async def assign_advisor(
    payload: AdvisorAssignmentCreate,
    current_user: User = Depends(require_roles("admin", "registrar", "dean")),
    db: AsyncSession = Depends(get_db)
):
    """Assign a faculty lecturer as academic advisor to a student."""
    # Verify student
    s_res = await db.execute(select(Student).where(Student.id == payload.student_id))
    student = s_res.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Verify lecturer
    l_res = await db.execute(select(Lecturer).where(Lecturer.id == payload.lecturer_id))
    lecturer = l_res.scalar_one_or_none()
    if not lecturer:
        raise HTTPException(status_code=404, detail="Lecturer not found")

    institution_id = current_user.institution_id or student.institution_id or 1

    assignment = AcademicAdvisorAssignment(
        institution_id=institution_id,
        student_id=payload.student_id,
        lecturer_id=payload.lecturer_id,
        advising_type=payload.advising_type,
        assigned_date=date.today(),
        is_active=True
    )
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    return assignment


@router.get("/assignments", response_model=List[AdvisorAssignmentOut])
async def list_advisor_assignments(
    student_id: Optional[int] = None,
    lecturer_id: Optional[int] = None,
    advising_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List advisor assignments with role-based filtering."""
    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    is_staff = role_val in {UserRole.ADMIN.value, UserRole.DEAN.value, UserRole.REGISTRAR.value, UserRole.LECTURER.value}

    query = select(AcademicAdvisorAssignment)

    if current_user.institution_id is not None:
        query = query.where(AcademicAdvisorAssignment.institution_id == current_user.institution_id)

    if not is_staff:
        # Restrict student to their own assignments
        s_res = await db.execute(select(Student.id).where(Student.user_id == current_user.id))
        cur_student_id = s_res.scalar_one_or_none()
        if not cur_student_id:
            return []
        query = query.where(AcademicAdvisorAssignment.student_id == cur_student_id)
    elif student_id is not None:
        query = query.where(AcademicAdvisorAssignment.student_id == student_id)

    if lecturer_id is not None:
        query = query.where(AcademicAdvisorAssignment.lecturer_id == lecturer_id)
    if advising_type is not None:
        query = query.where(AcademicAdvisorAssignment.advising_type == advising_type)

    res = await db.execute(query)
    return res.scalars().all()


# ─── Advising Sessions ─────────────────────────────────────────────────────────

@router.post("/sessions", response_model=AdvisingSessionOut, status_code=status.HTTP_201_CREATED)
async def schedule_advising_session(
    payload: AdvisingSessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Schedule an advising appointment."""
    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    is_staff = role_val in {UserRole.ADMIN.value, UserRole.DEAN.value, UserRole.REGISTRAR.value, UserRole.LECTURER.value}

    # Verify student
    s_res = await db.execute(select(Student).where(Student.id == payload.student_id))
    student = s_res.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # If student is scheduling, ensure they are scheduling for themselves
    if not is_staff:
        if student.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Cannot schedule advising sessions for other students.")

    # Confidential notes cannot be set by students
    confidential_notes = payload.confidential_notes if is_staff else None

    institution_id = current_user.institution_id or student.institution_id or 1

    session = AdvisingSession(
        institution_id=institution_id,
        student_id=payload.student_id,
        lecturer_id=payload.lecturer_id,
        scheduled_at=payload.scheduled_at,
        duration_minutes=payload.duration_minutes,
        session_type=payload.session_type,
        status="scheduled",
        topic=payload.topic,
        student_notes=payload.student_notes,
        confidential_notes=confidential_notes,
        action_items=payload.action_items
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return _mask_confidential_session_notes(session, current_user)


@router.get("/sessions", response_model=List[AdvisingSessionOut])
async def list_advising_sessions(
    student_id: Optional[int] = None,
    lecturer_id: Optional[int] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List advising sessions with confidentiality masking for students."""
    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    is_staff = role_val in {UserRole.ADMIN.value, UserRole.DEAN.value, UserRole.REGISTRAR.value, UserRole.LECTURER.value}

    query = select(AdvisingSession)

    if current_user.institution_id is not None:
        query = query.where(AdvisingSession.institution_id == current_user.institution_id)

    if not is_staff:
        s_res = await db.execute(select(Student.id).where(Student.user_id == current_user.id))
        cur_student_id = s_res.scalar_one_or_none()
        if not cur_student_id:
            return []
        query = query.where(AdvisingSession.student_id == cur_student_id)
    elif student_id is not None:
        query = query.where(AdvisingSession.student_id == student_id)

    if lecturer_id is not None:
        query = query.where(AdvisingSession.lecturer_id == lecturer_id)
    if status_filter is not None:
        query = query.where(AdvisingSession.status == status_filter)

    query = query.order_by(AdvisingSession.scheduled_at.desc())
    res = await db.execute(query)
    sessions = res.scalars().all()
    return [_mask_confidential_session_notes(s, current_user) for s in sessions]


@router.get("/sessions/{session_id}", response_model=AdvisingSessionOut)
async def get_advising_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get single advising session with confidentiality masking."""
    res = await db.execute(
        select(AdvisingSession).where(AdvisingSession.id == session_id).options(selectinload(AdvisingSession.student))
    )
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Advising session not found")

    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    is_staff = role_val in {UserRole.ADMIN.value, UserRole.DEAN.value, UserRole.REGISTRAR.value, UserRole.LECTURER.value}
    is_owner = session.student.user_id == current_user.id

    if not (is_staff or is_owner):
        raise HTTPException(status_code=403, detail="Access denied to this advising session.")

    return _mask_confidential_session_notes(session, current_user)


@router.put("/sessions/{session_id}", response_model=AdvisingSessionOut)
async def update_advising_session(
    session_id: int,
    payload: AdvisingSessionUpdate,
    current_user: User = Depends(require_roles("admin", "dean", "lecturer")),
    db: AsyncSession = Depends(get_db)
):
    """Update session status, notes, or action items. Restricted to academic staff."""
    res = await db.execute(select(AdvisingSession).where(AdvisingSession.id == session_id))
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Advising session not found")

    if payload.status is not None:
        session.status = payload.status
        if payload.status == "completed":
            session.completed_at = datetime.utcnow()
    if payload.student_notes is not None:
        session.student_notes = payload.student_notes
    if payload.confidential_notes is not None:
        session.confidential_notes = payload.confidential_notes
    if payload.action_items is not None:
        session.action_items = payload.action_items

    await db.commit()
    await db.refresh(session)
    return _mask_confidential_session_notes(session, current_user)


# ─── Student Support Cases & Interventions ─────────────────────────────────────

@router.post("/cases", response_model=StudentSupportCaseOut, status_code=status.HTTP_201_CREATED)
async def create_support_case(
    payload: StudentSupportCaseCreate,
    current_user: User = Depends(require_roles("admin", "dean", "registrar", "lecturer")),
    db: AsyncSession = Depends(get_db)
):
    """Create a student support intervention case (e.g. academic probation alert)."""
    s_res = await db.execute(select(Student).where(Student.id == payload.student_id))
    student = s_res.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    case_no = f"CASE-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    institution_id = current_user.institution_id or student.institution_id or 1

    support_case = StudentSupportCase(
        institution_id=institution_id,
        student_id=payload.student_id,
        assigned_staff_id=payload.assigned_staff_id or current_user.id,
        case_number=case_no,
        category=payload.category,
        priority=payload.priority,
        status="open",
        title=payload.title,
        description=payload.description,
        created_by_id=current_user.id
    )
    db.add(support_case)
    await db.commit()
    await db.refresh(support_case)
    return support_case


@router.get("/cases", response_model=List[StudentSupportCaseOut])
async def list_support_cases(
    student_id: Optional[int] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List student support cases with role-based filtering."""
    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    is_staff = role_val in {UserRole.ADMIN.value, UserRole.DEAN.value, UserRole.REGISTRAR.value, UserRole.LECTURER.value}

    query = select(StudentSupportCase)

    if current_user.institution_id is not None:
        query = query.where(StudentSupportCase.institution_id == current_user.institution_id)

    if not is_staff:
        s_res = await db.execute(select(Student.id).where(Student.user_id == current_user.id))
        cur_student_id = s_res.scalar_one_or_none()
        if not cur_student_id:
            return []
        query = query.where(StudentSupportCase.student_id == cur_student_id)
    elif student_id is not None:
        query = query.where(StudentSupportCase.student_id == student_id)

    if category is not None:
        query = query.where(StudentSupportCase.category == category)
    if priority is not None:
        query = query.where(StudentSupportCase.priority == priority)
    if status_filter is not None:
        query = query.where(StudentSupportCase.status == status_filter)

    query = query.order_by(StudentSupportCase.created_at.desc())
    res = await db.execute(query)
    return res.scalars().all()


@router.patch("/cases/{case_id}", response_model=StudentSupportCaseOut)
async def update_support_case(
    case_id: int,
    payload: StudentSupportCaseUpdate,
    current_user: User = Depends(require_roles("admin", "dean", "registrar", "lecturer")),
    db: AsyncSession = Depends(get_db)
):
    """Update support case status, resolution summary, or priority."""
    res = await db.execute(select(StudentSupportCase).where(StudentSupportCase.id == case_id))
    support_case = res.scalar_one_or_none()
    if not support_case:
        raise HTTPException(status_code=404, detail="Support case not found")

    if payload.status is not None:
        support_case.status = payload.status
        if payload.status in {"resolved", "closed"}:
            support_case.resolved_at = datetime.utcnow()
    if payload.priority is not None:
        support_case.priority = payload.priority
    if payload.assigned_staff_id is not None:
        support_case.assigned_staff_id = payload.assigned_staff_id
    if payload.resolution_summary is not None:
        support_case.resolution_summary = payload.resolution_summary

    await db.commit()
    await db.refresh(support_case)
    return support_case


@router.post("/cases/{case_id}/notes", response_model=SupportCaseNoteOut, status_code=status.HTTP_201_CREATED)
async def add_case_note(
    case_id: int,
    payload: SupportCaseNoteCreate,
    current_user: User = Depends(require_roles("admin", "dean", "registrar", "lecturer")),
    db: AsyncSession = Depends(get_db)
):
    """Add a progress or intervention note to a support case."""
    res = await db.execute(select(StudentSupportCase).where(StudentSupportCase.id == case_id))
    if not res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Support case not found")

    note = SupportCaseNote(
        case_id=case_id,
        author_id=current_user.id,
        is_confidential=payload.is_confidential,
        content=payload.content
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note


@router.get("/cases/{case_id}/notes", response_model=List[SupportCaseNoteOut])
async def list_case_notes(
    case_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List case notes, filtering out confidential notes for student viewers."""
    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    is_staff = role_val in {UserRole.ADMIN.value, UserRole.DEAN.value, UserRole.REGISTRAR.value, UserRole.LECTURER.value}

    query = select(SupportCaseNote).where(SupportCaseNote.case_id == case_id)
    if not is_staff:
        query = query.where(SupportCaseNote.is_confidential == False)

    query = query.order_by(SupportCaseNote.created_at.asc())
    res = await db.execute(query)
    return res.scalars().all()
