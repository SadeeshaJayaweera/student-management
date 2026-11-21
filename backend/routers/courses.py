"""
NSBM EduSphere — Course & Module Management Router
Manages course catalog, credits, prerequisites, delivery methods, and structured learning modules.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from backend.database import get_db
from backend.models import Course, CoursePrerequisite, CourseModule, Institution, Program, Lecturer, User, UserRole
from backend.schemas import (
    CourseCreate, CourseUpdate, CourseOut,
    CoursePrerequisiteCreate, CoursePrerequisiteOut,
    CourseModuleCreate, CourseModuleUpdate, CourseModuleOut,
)
from backend.core.dependencies import get_current_user

router = APIRouter(tags=["Course & Module Management"])


def check_course_admin_or_faculty_access(current_user: User, course: Optional[Course] = None):
    """Allows Admins or assigned Lecturers to edit course content"""
    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if role_val == UserRole.ADMIN.value:
        return
    # If course provided, check if current user is the assigned lecturer
    if course and hasattr(current_user, "lecturer_profile") and current_user.lecturer_profile:
        if course.lecturer_id == current_user.lecturer_profile.id:
            return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Administrative or assigned faculty permissions required."
    )


# ─── Course Catalog Endpoints ─────────────────────────────────────────────────

@router.get("/api/courses", response_model=List[CourseOut])
async def list_courses(
    institution_id: Optional[int] = Query(None, description="Filter by institution"),
    program_id: Optional[int] = Query(None, description="Filter by academic program"),
    semester: Optional[int] = Query(None, description="Filter by semester number"),
    delivery_method: Optional[str] = Query(None, description="Filter by delivery method"),
    search: Optional[str] = Query(None, description="Search course code or title"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve catalog of courses with multi-dimensional filtering"""
    q = select(Course).where(Course.is_active == True)

    if institution_id is not None:
        q = q.where(Course.institution_id == institution_id)
    elif current_user.institution_id is not None:
        q = q.where(or_(Course.institution_id == current_user.institution_id, Course.institution_id.is_(None)))

    if program_id is not None:
        q = q.where(Course.program_id == program_id)
    if semester is not None:
        q = q.where(Course.semester == semester)
    if delivery_method is not None:
        q = q.where(Course.delivery_method == delivery_method)
    if search:
        search_filter = f"%{search.strip()}%"
        q = q.where(or_(Course.course_code.ilike(search_filter), Course.title.ilike(search_filter)))

    res = await db.execute(q.order_by(Course.course_code))
    return list(res.scalars().all())


@router.post("/api/courses", response_model=CourseOut, status_code=201)
async def create_course(
    payload: CourseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Register a new course in the curriculum catalog (Admin only)"""
    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if role_val != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required to register new courses."
        )

    code_upper = payload.course_code.strip().upper()
    existing = await db.execute(select(Course).where(Course.course_code == code_upper))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Course with code '{code_upper}' already exists."
        )

    # Validate program if supplied
    if payload.program_id is not None:
        prog_res = await db.execute(select(Program).where(Program.id == payload.program_id))
        if not prog_res.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid program_id specified.")

    course = Course(
        institution_id=current_user.institution_id,
        course_code=code_upper,
        title=payload.title.strip(),
        description=payload.description,
        credits=payload.credits,
        faculty=payload.faculty or "General",
        department=payload.department or "General",
        semester=payload.semester,
        year=payload.year,
        max_students=payload.max_students,
        lecturer_id=payload.lecturer_id,
        program_id=payload.program_id,
        faculty_id=payload.faculty_id,
        department_id=payload.department_id,
        delivery_method=payload.delivery_method,
        learning_outcomes=payload.learning_outcomes,
        schedule=payload.schedule,
    )
    db.add(course)
    await db.commit()
    await db.refresh(course)
    return course


@router.get("/api/courses/{course_id}", response_model=CourseOut)
async def get_course_detail(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve detailed course information"""
    res = await db.execute(select(Course).where(Course.id == course_id))
    course = res.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return course


@router.put("/api/courses/{course_id}", response_model=CourseOut)
async def update_course(
    course_id: int,
    payload: CourseUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update course syllabus, metadata, delivery method, or outcomes"""
    res = await db.execute(select(Course).where(Course.id == course_id))
    course = res.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    check_course_admin_or_faculty_access(current_user, course)

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(course, field, val)

    await db.commit()
    await db.refresh(course)
    return course


@router.delete("/api/courses/{course_id}", status_code=204)
async def delete_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a course from the catalog"""
    res = await db.execute(select(Course).where(Course.id == course_id))
    course = res.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    check_course_admin_or_faculty_access(current_user, course)

    await db.delete(course)
    await db.commit()
    return None


# ─── Course Prerequisite Endpoints ────────────────────────────────────────────

@router.get("/api/courses/{course_id}/prerequisites", response_model=List[CoursePrerequisiteOut])
async def list_course_prerequisites(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all prerequisites required for a course"""
    c_res = await db.execute(select(Course).where(Course.id == course_id))
    if not c_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    res = await db.execute(
        select(CoursePrerequisite).where(CoursePrerequisite.course_id == course_id)
    )
    prereqs = res.scalars().all()

    # Enrich with prerequisite course code and title
    out = []
    for p in prereqs:
        p_course = await db.get(Course, p.prerequisite_course_id)
        out.append(
            CoursePrerequisiteOut(
                id=p.id,
                course_id=p.course_id,
                prerequisite_course_id=p.prerequisite_course_id,
                is_mandatory=p.is_mandatory,
                minimum_grade=p.minimum_grade,
                created_at=p.created_at,
                prerequisite_course_code=p_course.course_code if p_course else None,
                prerequisite_title=p_course.title if p_course else None,
            )
        )
    return out


@router.post("/api/courses/{course_id}/prerequisites", response_model=CoursePrerequisiteOut, status_code=201)
async def add_course_prerequisite(
    course_id: int,
    payload: CoursePrerequisiteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a prerequisite requirement to a course (Admin only)"""
    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if role_val != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required to configure course prerequisites."
        )

    if course_id == payload.prerequisite_course_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A course cannot be a prerequisite of itself."
        )

    # Verify both courses exist
    target_course = await db.get(Course, course_id)
    prereq_course = await db.get(Course, payload.prerequisite_course_id)
    if not target_course or not prereq_course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Specified course not found.")

    # Check for existing duplicate prerequisite
    existing = await db.execute(
        select(CoursePrerequisite).where(
            CoursePrerequisite.course_id == course_id,
            CoursePrerequisite.prerequisite_course_id == payload.prerequisite_course_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This course prerequisite is already configured."
        )

    prereq = CoursePrerequisite(
        course_id=course_id,
        prerequisite_course_id=payload.prerequisite_course_id,
        is_mandatory=payload.is_mandatory,
        minimum_grade=payload.minimum_grade.upper(),
    )
    db.add(prereq)
    await db.commit()
    await db.refresh(prereq)

    return CoursePrerequisiteOut(
        id=prereq.id,
        course_id=prereq.course_id,
        prerequisite_course_id=prereq.prerequisite_course_id,
        is_mandatory=prereq.is_mandatory,
        minimum_grade=prereq.minimum_grade,
        created_at=prereq.created_at,
        prerequisite_course_code=prereq_course.course_code,
        prerequisite_title=prereq_course.title,
    )


@router.delete("/api/courses/{course_id}/prerequisites/{prereq_id}", status_code=204)
async def delete_course_prerequisite(
    course_id: int,
    prereq_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a prerequisite requirement"""
    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if role_val != UserRole.ADMIN.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")

    res = await db.execute(
        select(CoursePrerequisite).where(
            CoursePrerequisite.id == prereq_id, CoursePrerequisite.course_id == course_id
        )
    )
    prereq = res.scalar_one_or_none()
    if not prereq:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prerequisite rule not found.")

    await db.delete(prereq)
    await db.commit()
    return None


# ─── Course Module Endpoints ──────────────────────────────────────────────────

@router.get("/api/courses/{course_id}/modules", response_model=List[CourseModuleOut])
async def list_course_modules(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all structured modules for a course ordered sequentially"""
    c_res = await db.execute(select(Course).where(Course.id == course_id))
    if not c_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    res = await db.execute(
        select(CourseModule)
        .where(CourseModule.course_id == course_id)
        .order_by(CourseModule.order_index)
    )
    return list(res.scalars().all())


@router.post("/api/courses/{course_id}/modules", response_model=CourseModuleOut, status_code=201)
async def create_course_module(
    course_id: int,
    payload: CourseModuleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a structured learning module to a course"""
    course = await db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    check_course_admin_or_faculty_access(current_user, course)

    mod = CourseModule(
        course_id=course_id,
        order_index=payload.order_index,
        title=payload.title.strip(),
        description=payload.description,
        learning_objectives=payload.learning_objectives,
        estimated_hours=payload.estimated_hours,
        is_active=payload.is_active,
    )
    db.add(mod)
    await db.commit()
    await db.refresh(mod)
    return mod


@router.get("/api/modules/{module_id}", response_model=CourseModuleOut)
async def get_module(
    module_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve details of a single course learning module"""
    res = await db.execute(select(CourseModule).where(CourseModule.id == module_id))
    mod = res.scalar_one_or_none()
    if not mod:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course module not found")
    return mod


@router.put("/api/modules/{module_id}", response_model=CourseModuleOut)
async def update_module(
    module_id: int,
    payload: CourseModuleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update details of a learning module"""
    res = await db.execute(select(CourseModule).where(CourseModule.id == module_id))
    mod = res.scalar_one_or_none()
    if not mod:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course module not found")

    course = await db.get(Course, mod.course_id)
    check_course_admin_or_faculty_access(current_user, course)

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(mod, field, val)

    await db.commit()
    await db.refresh(mod)
    return mod


@router.delete("/api/modules/{module_id}", status_code=204)
async def delete_module(
    module_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a course module"""
    res = await db.execute(select(CourseModule).where(CourseModule.id == module_id))
    mod = res.scalar_one_or_none()
    if not mod:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course module not found")

    course = await db.get(Course, mod.course_id)
    check_course_admin_or_faculty_access(current_user, course)

    await db.delete(mod)
    await db.commit()
    return None
