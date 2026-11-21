"""
NSBM EduSphere — Class Cohort and Group Management Router
Manages batch cohorts, tutorial/lab groups, project teams, section allocations, and membership.
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.models import (
    User, UserRole, Student, Lecturer, Course, Program, AcademicYear,
    Cohort, CohortMember, StudentGroup, StudentGroupMember
)
from backend.schemas import (
    CohortCreate, CohortUpdate, CohortOut,
    CohortMemberAdd, CohortMemberOut,
    StudentGroupCreate, StudentGroupOut,
    StudentGroupMemberAdd, StudentGroupMemberOut
)
from backend.utils.security import get_current_user, require_roles

router = APIRouter(prefix="/api/cohorts", tags=["Cohorts and Groups"])


@router.get("", response_model=List[CohortOut])
async def list_cohorts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    program_id: Optional[int] = None,
    academic_year_id: Optional[int] = None,
    year_of_study: Optional[int] = None,
    semester_number: Optional[int] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List cohorts with filtering and member counts."""
    query = select(Cohort)

    if current_user.institution_id is not None:
        query = query.where(Cohort.institution_id == current_user.institution_id)

    if program_id is not None:
        query = query.where(Cohort.program_id == program_id)
    if academic_year_id is not None:
        query = query.where(Cohort.academic_year_id == academic_year_id)
    if year_of_study is not None:
        query = query.where(Cohort.year_of_study == year_of_study)
    if semester_number is not None:
        query = query.where(Cohort.semester_number == semester_number)

    if search:
        search_filter = f"%{search}%"
        query = query.where(or_(Cohort.code.ilike(search_filter), Cohort.name.ilike(search_filter)))

    query = query.order_by(Cohort.created_at.desc()).offset(skip).limit(limit)
    res = await db.execute(query)
    cohorts = res.scalars().all()

    out = []
    for c in cohorts:
        cnt_q = await db.execute(
            select(func.count(CohortMember.id)).where(CohortMember.cohort_id == c.id)
        )
        c_out = CohortOut.model_validate(c)
        c_out.member_count = cnt_q.scalar() or 0
        out.append(c_out)

    return out


@router.post("", response_model=CohortOut, status_code=status.HTTP_201_CREATED)
async def create_cohort(
    payload: CohortCreate,
    current_user: User = Depends(require_roles("admin", "registrar", "dean")),
    db: AsyncSession = Depends(get_db)
):
    """Create a new class cohort. Restricted to Admins, Registrars, and Deans."""
    # Check duplicate code in same institution
    dup_q = select(Cohort).where(Cohort.code == payload.code)
    if current_user.institution_id:
        dup_q = dup_q.where(Cohort.institution_id == current_user.institution_id)
    dup_res = await db.execute(dup_q)
    if dup_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cohort with code '{payload.code}' already exists."
        )

    cohort = Cohort(
        institution_id=current_user.institution_id or 1,
        program_id=payload.program_id,
        academic_year_id=payload.academic_year_id,
        code=payload.code,
        name=payload.name,
        year_of_study=payload.year_of_study,
        semester_number=payload.semester_number,
        max_capacity=payload.max_capacity,
        is_active=True
    )
    db.add(cohort)
    await db.commit()
    await db.refresh(cohort)

    c_out = CohortOut.model_validate(cohort)
    c_out.member_count = 0
    return c_out


@router.get("/my")
async def get_my_cohorts_and_groups(
    current_user: User = Depends(require_roles("student")),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve all cohorts and groups the logged-in student belongs to."""
    student_res = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = student_res.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    # Cohorts
    cohort_memberships = await db.execute(
        select(CohortMember).where(
            and_(CohortMember.student_id == student.id, CohortMember.status == "active")
        ).options(selectinload(CohortMember.cohort))
    )
    cm_list = cohort_memberships.scalars().all()

    # Groups
    group_memberships = await db.execute(
        select(StudentGroupMember).where(StudentGroupMember.student_id == student.id)
        .options(selectinload(StudentGroupMember.group))
    )
    gm_list = group_memberships.scalars().all()

    return {
        "student_id": student.student_id,
        "cohorts": [
            {
                "cohort_id": cm.cohort.id,
                "code": cm.cohort.code,
                "name": cm.cohort.name,
                "role": cm.role,
                "joined_at": cm.joined_at.isoformat()
            }
            for cm in cm_list
        ],
        "groups": [
            {
                "group_id": gm.group.id,
                "name": gm.group.name,
                "group_type": gm.group.group_type,
                "role": gm.group_role,
                "schedule_info": gm.group.schedule_info,
                "joined_at": gm.joined_at.isoformat()
            }
            for gm in gm_list
        ]
    }


@router.get("/{cohort_id}", response_model=CohortOut)
async def get_cohort(
    cohort_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get single cohort details with member count."""
    res = await db.execute(select(Cohort).where(Cohort.id == cohort_id))
    cohort = res.scalar_one_or_none()
    if not cohort:
        raise HTTPException(status_code=404, detail="Cohort not found")

    cnt_q = await db.execute(
        select(func.count(CohortMember.id)).where(CohortMember.cohort_id == cohort.id)
    )
    c_out = CohortOut.model_validate(cohort)
    c_out.member_count = cnt_q.scalar() or 0
    return c_out


@router.put("/{cohort_id}", response_model=CohortOut)
async def update_cohort(
    cohort_id: int,
    payload: CohortUpdate,
    current_user: User = Depends(require_roles("admin", "registrar", "dean")),
    db: AsyncSession = Depends(get_db)
):
    """Update cohort details. Restricted to Admins, Registrars, and Deans."""
    res = await db.execute(select(Cohort).where(Cohort.id == cohort_id))
    cohort = res.scalar_one_or_none()
    if not cohort:
        raise HTTPException(status_code=404, detail="Cohort not found")

    if payload.name is not None:
        cohort.name = payload.name
    if payload.max_capacity is not None:
        cohort.max_capacity = payload.max_capacity
    if payload.year_of_study is not None:
        cohort.year_of_study = payload.year_of_study
    if payload.semester_number is not None:
        cohort.semester_number = payload.semester_number
    if payload.is_active is not None:
        cohort.is_active = payload.is_active

    await db.commit()
    await db.refresh(cohort)

    cnt_q = await db.execute(
        select(func.count(CohortMember.id)).where(CohortMember.cohort_id == cohort.id)
    )
    c_out = CohortOut.model_validate(cohort)
    c_out.member_count = cnt_q.scalar() or 0
    return c_out


@router.get("/{cohort_id}/members", response_model=List[CohortMemberOut])
async def list_cohort_members(
    cohort_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all members assigned to a cohort."""
    query = select(CohortMember).where(CohortMember.cohort_id == cohort_id).order_by(CohortMember.joined_at.asc())
    res = await db.execute(query)
    return res.scalars().all()


@router.post("/{cohort_id}/members", response_model=CohortMemberOut, status_code=status.HTTP_201_CREATED)
async def add_cohort_member(
    cohort_id: int,
    payload: CohortMemberAdd,
    current_user: User = Depends(require_roles("admin", "registrar", "dean", "lecturer")),
    db: AsyncSession = Depends(get_db)
):
    """Add a student to a cohort, enforcing capacity limits and uniqueness."""
    res = await db.execute(select(Cohort).where(Cohort.id == cohort_id))
    cohort = res.scalar_one_or_none()
    if not cohort:
        raise HTTPException(status_code=404, detail="Cohort not found")

    # Check student
    stu_res = await db.execute(select(Student).where(Student.id == payload.student_id))
    student = stu_res.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Check duplicate
    dup_q = await db.execute(
        select(CohortMember).where(
            and_(CohortMember.cohort_id == cohort_id, CohortMember.student_id == payload.student_id)
        )
    )
    if dup_q.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Student is already assigned to this cohort.")

    # Check capacity
    cur_count_q = await db.execute(
        select(func.count(CohortMember.id)).where(CohortMember.cohort_id == cohort_id)
    )
    if (cur_count_q.scalar() or 0) >= cohort.max_capacity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cohort capacity limit ({cohort.max_capacity}) reached."
        )

    member = CohortMember(
        cohort_id=cohort_id,
        student_id=payload.student_id,
        role=payload.role,
        status="active"
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member


@router.delete("/{cohort_id}/members/{student_id}", status_code=status.HTTP_200_OK)
async def remove_cohort_member(
    cohort_id: int,
    student_id: int,
    current_user: User = Depends(require_roles("admin", "registrar", "dean")),
    db: AsyncSession = Depends(get_db)
):
    """Remove a student from a cohort."""
    res = await db.execute(
        select(CohortMember).where(
            and_(CohortMember.cohort_id == cohort_id, CohortMember.student_id == student_id)
        )
    )
    member = res.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Student is not a member of this cohort.")

    await db.delete(member)
    await db.commit()
    return {"message": "Student successfully removed from cohort."}


# ─── Student Groups (Tutorial / Lab / Project Teams) ───────────────────────────

@router.get("/groups/all", response_model=List[StudentGroupOut])
async def list_student_groups(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    cohort_id: Optional[int] = None,
    course_id: Optional[int] = None,
    group_type: Optional[str] = None,
    mentor_lecturer_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List student groups (tutorial, lab, project teams) with member counts."""
    query = select(StudentGroup)

    if current_user.institution_id is not None:
        query = query.where(StudentGroup.institution_id == current_user.institution_id)

    if cohort_id is not None:
        query = query.where(StudentGroup.cohort_id == cohort_id)
    if course_id is not None:
        query = query.where(StudentGroup.course_id == course_id)
    if group_type is not None:
        query = query.where(StudentGroup.group_type == group_type)
    if mentor_lecturer_id is not None:
        query = query.where(StudentGroup.mentor_lecturer_id == mentor_lecturer_id)

    query = query.order_by(StudentGroup.created_at.desc()).offset(skip).limit(limit)
    res = await db.execute(query)
    groups = res.scalars().all()

    out = []
    for g in groups:
        cnt_q = await db.execute(
            select(func.count(StudentGroupMember.id)).where(StudentGroupMember.group_id == g.id)
        )
        g_out = StudentGroupOut.model_validate(g)
        g_out.member_count = cnt_q.scalar() or 0
        out.append(g_out)

    return out


@router.post("/groups", response_model=StudentGroupOut, status_code=status.HTTP_201_CREATED)
async def create_student_group(
    payload: StudentGroupCreate,
    current_user: User = Depends(require_roles("admin", "dean", "lecturer")),
    db: AsyncSession = Depends(get_db)
):
    """Create a tutorial, lab, or project team group. Restricted to academic staff."""
    group = StudentGroup(
        institution_id=current_user.institution_id or 1,
        cohort_id=payload.cohort_id,
        course_id=payload.course_id,
        group_type=payload.group_type,
        name=payload.name,
        max_capacity=payload.max_capacity,
        mentor_lecturer_id=payload.mentor_lecturer_id,
        schedule_info=payload.schedule_info,
        is_active=True
    )
    db.add(group)
    await db.commit()
    await db.refresh(group)

    g_out = StudentGroupOut.model_validate(group)
    g_out.member_count = 0
    return g_out


@router.get("/groups/{group_id}/members", response_model=List[StudentGroupMemberOut])
async def list_group_members(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all students enrolled in a group."""
    query = select(StudentGroupMember).where(StudentGroupMember.group_id == group_id).order_by(StudentGroupMember.joined_at.asc())
    res = await db.execute(query)
    return res.scalars().all()


@router.post("/groups/{group_id}/members", response_model=StudentGroupMemberOut, status_code=status.HTTP_201_CREATED)
async def add_group_member(
    group_id: int,
    payload: StudentGroupMemberAdd,
    current_user: User = Depends(require_roles("admin", "dean", "lecturer")),
    db: AsyncSession = Depends(get_db)
):
    """Add a student to a tutorial, lab, or project group."""
    res = await db.execute(select(StudentGroup).where(StudentGroup.id == group_id))
    group = res.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Student group not found")

    # Check student
    stu_res = await db.execute(select(Student).where(Student.id == payload.student_id))
    student = stu_res.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Check duplicate
    dup_q = await db.execute(
        select(StudentGroupMember).where(
            and_(StudentGroupMember.group_id == group_id, StudentGroupMember.student_id == payload.student_id)
        )
    )
    if dup_q.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Student is already a member of this group.")

    # Check capacity
    cur_count_q = await db.execute(
        select(func.count(StudentGroupMember.id)).where(StudentGroupMember.group_id == group_id)
    )
    if (cur_count_q.scalar() or 0) >= group.max_capacity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Group capacity limit ({group.max_capacity}) reached."
        )

    member = StudentGroupMember(
        group_id=group_id,
        student_id=payload.student_id,
        group_role=payload.group_role
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member


@router.delete("/groups/{group_id}/members/{student_id}", status_code=status.HTTP_200_OK)
async def remove_group_member(
    group_id: int,
    student_id: int,
    current_user: User = Depends(require_roles("admin", "dean", "lecturer")),
    db: AsyncSession = Depends(get_db)
):
    """Remove a student from a group."""
    res = await db.execute(
        select(StudentGroupMember).where(
            and_(StudentGroupMember.group_id == group_id, StudentGroupMember.student_id == student_id)
        )
    )
    member = res.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Student is not in this group.")

    await db.delete(member)
    await db.commit()
    return {"message": "Student successfully removed from group."}
