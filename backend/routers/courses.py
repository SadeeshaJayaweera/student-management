"""
NSBM EduSphere — Course & Module Management Router
Manages course catalog, credits, prerequisites, delivery methods, and structured learning modules.
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func, update
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.models import (
    Course, CoursePrerequisite, CourseModule, CourseLesson, LessonContentVersion, CourseAnnouncement, Institution, Program, Lecturer,
    User, UserRole, Enrollment, Assignment, Student, StudentModuleProgress
)
from backend.schemas import (
    CourseCreate, CourseUpdate, CourseOut,
    CoursePrerequisiteCreate, CoursePrerequisiteOut,
    CourseModuleCreate, CourseModuleUpdate, CourseModuleOut,
    CourseLessonBase, CourseLessonCreate, CourseLessonUpdate, CourseLessonOut,
    LessonContentCreate, LessonContentOut, LessonContentVersionSummary,
    ModuleReorderRequest, LessonReorderRequest,
    CourseWorkspaceSettingsUpdate, CourseWorkspaceOut
)
from backend.core.dependencies import get_current_user
from backend.core.sanitization import sanitize_rich_content

router = APIRouter(tags=["Course & Module Management"])


def check_course_admin_or_faculty_access(current_user: User, course: Optional[Course] = None):
    """Allows Admins, Deans or assigned Lecturers to edit course content"""
    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if role_val in {UserRole.ADMIN.value, UserRole.DEAN.value}:
        return
    # If course provided, check if current user is the assigned lecturer
    if course and role_val == UserRole.LECTURER.value:
        lec = getattr(current_user, "lecturer", None) or getattr(current_user, "lecturer_profile", None)
        if lec and course.lecturer_id == lec.id:
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
    q = select(Course).options(selectinload(Course.lecturer).selectinload(Lecturer.user)).where(Course.is_active == True)

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
    """List all structured modules for a course ordered sequentially with lesson hierarchies and drip status"""
    c_res = await db.execute(select(Course).where(Course.id == course_id))
    course = c_res.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    is_admin = role_val in {UserRole.ADMIN.value, UserRole.DEAN.value}
    lec = getattr(current_user, "lecturer", None) or getattr(current_user, "lecturer_profile", None)
    is_instructor = bool(course.lecturer_id and lec and lec.id == course.lecturer_id)

    completed_mod_ids = set()
    if role_val == UserRole.STUDENT.value:
        stu = getattr(current_user, "student", None)
        if not stu:
            s_res = await db.execute(select(Student.id).where(Student.user_id == current_user.id))
            stu_id = s_res.scalar_one_or_none()
        else:
            stu_id = stu.id
        if stu_id:
            smp_res = await db.execute(
                select(StudentModuleProgress.module_id).where(
                    StudentModuleProgress.student_id == stu_id,
                    StudentModuleProgress.status == "completed"
                )
            )
            completed_mod_ids = set(smp_res.scalars().all())

    q = (
        select(CourseModule)
        .where(CourseModule.course_id == course_id)
        .options(selectinload(CourseModule.lessons), selectinload(CourseModule.prerequisite))
        .order_by(CourseModule.order_index)
    )
    res = await db.execute(q)
    modules = list(res.scalars().all())

    now = datetime.utcnow()
    output = []
    for mod in modules:
        # Filter unpublished or inactive modules for students
        if not (is_admin or is_instructor):
            if not mod.is_active or mod.status != "published":
                continue

        # Evaluate drip lock
        is_locked = False
        lock_reason = None
        if not (is_admin or is_instructor):
            if mod.unlock_at and mod.unlock_at > now:
                is_locked = True
                lock_reason = f"Unlocks on {mod.unlock_at.strftime('%Y-%m-%d %H:%M')}"
            elif mod.prerequisite_module_id and mod.prerequisite:
                if mod.prerequisite_module_id not in completed_mod_ids:
                    is_locked = True
                    lock_reason = f"Requires completion of prerequisite module: {mod.prerequisite.title}"

        # Lessons filtering
        lessons_data = []
        for les in sorted(mod.lessons, key=lambda l: l.order_index):
            if not (is_admin or is_instructor) and not les.is_published:
                continue
            lessons_data.append(les)

        mod_dict = {
            "id": mod.id,
            "course_id": mod.course_id,
            "order_index": mod.order_index,
            "title": mod.title,
            "description": mod.description,
            "learning_objectives": mod.learning_objectives,
            "estimated_hours": mod.estimated_hours,
            "status": mod.status,
            "unlock_at": mod.unlock_at,
            "prerequisite_module_id": mod.prerequisite_module_id,
            "is_active": mod.is_active,
            "is_locked": is_locked,
            "lock_reason": lock_reason,
            "lessons": lessons_data,
            "created_at": mod.created_at,
            "updated_at": mod.updated_at,
        }
        output.append(CourseModuleOut(**mod_dict))

    return output


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
        status=payload.status,
        unlock_at=payload.unlock_at,
        prerequisite_module_id=payload.prerequisite_module_id,
        is_active=payload.is_active,
    )
    db.add(mod)
    await db.commit()
    
    q = (
        select(CourseModule)
        .where(CourseModule.id == mod.id)
        .options(selectinload(CourseModule.lessons), selectinload(CourseModule.prerequisite))
    )
    res = await db.execute(q)
    loaded_mod = res.scalar_one()
    loaded_mod.is_locked = False
    loaded_mod.lock_reason = None
    return loaded_mod


@router.put("/api/courses/{course_id}/modules/reorder")
async def reorder_course_modules(
    course_id: int,
    payload: ModuleReorderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reorder modules within a course sequentially"""
    course = await db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    check_course_admin_or_faculty_access(current_user, course)

    res = await db.execute(select(CourseModule).where(CourseModule.course_id == course_id))
    modules = {m.id: m for m in res.scalars().all()}

    for new_idx, mod_id in enumerate(payload.module_ids, start=1):
        if mod_id in modules:
            modules[mod_id].order_index = new_idx

    await db.commit()
    return {"message": "Modules reordered successfully", "reordered_count": len(payload.module_ids)}


@router.get("/api/modules/{module_id}", response_model=CourseModuleOut)
async def get_module(
    module_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve details of a single course learning module with lessons"""
    res = await db.execute(
        select(CourseModule)
        .where(CourseModule.id == module_id)
        .options(selectinload(CourseModule.lessons), selectinload(CourseModule.prerequisite))
    )
    mod = res.scalar_one_or_none()
    if not mod:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course module not found")
    mod.is_locked = False
    mod.lock_reason = None
    return mod


@router.put("/api/modules/{module_id}", response_model=CourseModuleOut)
async def update_module(
    module_id: int,
    payload: CourseModuleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update details of a learning module"""
    res = await db.execute(
        select(CourseModule)
        .where(CourseModule.id == module_id)
        .options(selectinload(CourseModule.lessons))
    )
    mod = res.scalar_one_or_none()
    if not mod:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course module not found")

    course = await db.get(Course, mod.course_id)
    check_course_admin_or_faculty_access(current_user, course)

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(mod, field, val)

    await db.commit()
    
    q = (
        select(CourseModule)
        .where(CourseModule.id == module_id)
        .options(selectinload(CourseModule.lessons), selectinload(CourseModule.prerequisite))
    )
    res = await db.execute(q)
    loaded_mod = res.scalar_one()
    loaded_mod.is_locked = False
    loaded_mod.lock_reason = None
    return loaded_mod


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


# ─── Course Lesson Endpoints ──────────────────────────────────────────────────

@router.post("/api/modules/{module_id}/lessons", response_model=CourseLessonOut, status_code=201)
async def create_course_lesson(
    module_id: int,
    payload: CourseLessonCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a structured lesson or learning item to a course module"""
    res = await db.execute(select(CourseModule).where(CourseModule.id == module_id))
    mod = res.scalar_one_or_none()
    if not mod:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course module not found")

    course = await db.get(Course, mod.course_id)
    check_course_admin_or_faculty_access(current_user, course)

    lesson = CourseLesson(
        module_id=module_id,
        title=payload.title.strip(),
        lesson_type=payload.lesson_type,
        content=payload.content,
        resource_url=payload.resource_url,
        estimated_minutes=payload.estimated_minutes,
        order_index=payload.order_index,
        is_required=payload.is_required,
        is_published=payload.is_published,
        unlock_at=payload.unlock_at,
    )
    db.add(lesson)
    await db.commit()
    await db.refresh(lesson)
    return lesson


@router.get("/api/modules/{module_id}/lessons", response_model=List[CourseLessonOut])
async def list_module_lessons(
    module_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all lessons in a module ordered sequentially"""
    res = await db.execute(select(CourseModule).where(CourseModule.id == module_id))
    mod = res.scalar_one_or_none()
    if not mod:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course module not found")

    course = await db.get(Course, mod.course_id)
    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    is_admin = role_val == UserRole.ADMIN.value
    is_instructor = bool(
        course and course.lecturer_id and hasattr(current_user, "lecturer_profile") and
        current_user.lecturer_profile and current_user.lecturer_profile.id == course.lecturer_id
    )

    q = select(CourseLesson).where(CourseLesson.module_id == module_id).order_by(CourseLesson.order_index)
    if not (is_admin or is_instructor):
        q = q.where(CourseLesson.is_published == True)

    l_res = await db.execute(q)
    return list(l_res.scalars().all())


@router.put("/api/modules/{module_id}/lessons/reorder")
async def reorder_module_lessons(
    module_id: int,
    payload: LessonReorderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reorder lessons within a module sequentially"""
    res = await db.execute(select(CourseModule).where(CourseModule.id == module_id))
    mod = res.scalar_one_or_none()
    if not mod:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course module not found")

    course = await db.get(Course, mod.course_id)
    check_course_admin_or_faculty_access(current_user, course)

    l_res = await db.execute(select(CourseLesson).where(CourseLesson.module_id == module_id))
    lessons = {l.id: l for l in l_res.scalars().all()}

    for new_idx, lesson_id in enumerate(payload.lesson_ids, start=1):
        if lesson_id in lessons:
            lessons[lesson_id].order_index = new_idx

    await db.commit()
    return {"message": "Lessons reordered successfully", "reordered_count": len(payload.lesson_ids)}


@router.get("/api/lessons/{lesson_id}", response_model=CourseLessonOut)
async def get_lesson(
    lesson_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve details of a single lesson"""
    res = await db.execute(select(CourseLesson).where(CourseLesson.id == lesson_id))
    lesson = res.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")

    mod = await db.get(CourseModule, lesson.module_id)
    course = await db.get(Course, mod.course_id) if mod else None

    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    is_admin = role_val == UserRole.ADMIN.value
    is_instructor = bool(
        course and course.lecturer_id and hasattr(current_user, "lecturer_profile") and
        current_user.lecturer_profile and current_user.lecturer_profile.id == course.lecturer_id
    )

    if not (is_admin or is_instructor) and not lesson.is_published:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")

    return lesson


@router.put("/api/lessons/{lesson_id}", response_model=CourseLessonOut)
async def update_lesson(
    lesson_id: int,
    payload: CourseLessonUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update details of a lesson"""
    res = await db.execute(select(CourseLesson).where(CourseLesson.id == lesson_id))
    lesson = res.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")

    mod = await db.get(CourseModule, lesson.module_id)
    course = await db.get(Course, mod.course_id) if mod else None
    check_course_admin_or_faculty_access(current_user, course)

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(lesson, field, val)

    await db.commit()
    await db.refresh(lesson)
    return lesson


@router.delete("/api/lessons/{lesson_id}", status_code=204)
async def delete_lesson(
    lesson_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a lesson from a course module"""
    res = await db.execute(select(CourseLesson).where(CourseLesson.id == lesson_id))
    lesson = res.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")

    mod = await db.get(CourseModule, lesson.module_id)
    course = await db.get(Course, mod.course_id) if mod else None
    check_course_admin_or_faculty_access(current_user, course)

    await db.delete(lesson)
    await db.commit()
    return None


# ─── Rich Learning Content Authoring & Versioning ─────────────────────────────

@router.post("/api/lessons/{lesson_id}/content", response_model=LessonContentOut, status_code=201)
async def author_lesson_content(
    lesson_id: int,
    payload: LessonContentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Author or update rich learning content for a lesson with automatic versioning
    and anti-XSS sanitization.
    """
    res = await db.execute(select(CourseLesson).where(CourseLesson.id == lesson_id))
    lesson = res.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")

    mod = await db.get(CourseModule, lesson.module_id)
    course = await db.get(Course, mod.course_id) if mod else None
    check_course_admin_or_faculty_access(current_user, course)

    # Sanitize content against XSS while preserving rich format
    rendered = sanitize_rich_content(payload.raw_content, content_format=payload.content_format)

    # Determine next version number
    q_ver = select(func.max(LessonContentVersion.version_number)).where(
        LessonContentVersion.lesson_id == lesson_id
    )
    max_ver = (await db.execute(q_ver)).scalar() or 0
    next_ver = max_ver + 1

    # Mark existing versions as not current
    await db.execute(
        update(LessonContentVersion)
        .where(LessonContentVersion.lesson_id == lesson_id)
        .values(is_current=False)
    )

    new_content = LessonContentVersion(
        lesson_id=lesson_id,
        version_number=next_ver,
        content_format=payload.content_format,
        raw_content=payload.raw_content,
        rendered_content=rendered,
        widget_configs=payload.widget_configs,
        author_id=current_user.id,
        change_summary=payload.change_summary or f"Version {next_ver} updated",
        is_current=True,
    )
    db.add(new_content)

    # Sync lesson content field with rendered content
    lesson.content = rendered
    await db.commit()
    await db.refresh(new_content)
    return new_content


@router.get("/api/lessons/{lesson_id}/content", response_model=LessonContentOut)
async def get_lesson_content(
    lesson_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve current active rich learning content for a lesson"""
    res = await db.execute(select(CourseLesson).where(CourseLesson.id == lesson_id))
    lesson = res.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")

    mod = await db.get(CourseModule, lesson.module_id)
    course = await db.get(Course, mod.course_id) if mod else None

    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    is_admin = role_val in {UserRole.ADMIN.value, UserRole.DEAN.value}
    is_instructor = bool(course and course.lecturer and course.lecturer.user_id == current_user.id)

    if not (is_admin or is_instructor) and not lesson.is_published:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found or unavailable")

    c_res = await db.execute(
        select(LessonContentVersion)
        .where(LessonContentVersion.lesson_id == lesson_id, LessonContentVersion.is_current == True)
    )
    content = c_res.scalar_one_or_none()
    if not content:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No content authored for this lesson")

    return content


@router.get("/api/lessons/{lesson_id}/content/versions", response_model=List[LessonContentVersionSummary])
async def list_content_versions(
    lesson_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List historical revision audit trail for lesson content (faculty and admin only)"""
    res = await db.execute(select(CourseLesson).where(CourseLesson.id == lesson_id))
    lesson = res.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")

    mod = await db.get(CourseModule, lesson.module_id)
    course = await db.get(Course, mod.course_id) if mod else None
    check_course_admin_or_faculty_access(current_user, course)

    v_res = await db.execute(
        select(LessonContentVersion)
        .where(LessonContentVersion.lesson_id == lesson_id)
        .order_by(LessonContentVersion.version_number.desc())
    )
    return list(v_res.scalars().all())


@router.get("/api/lessons/{lesson_id}/content/versions/{version_number}", response_model=LessonContentOut)
async def get_content_version(
    lesson_id: int,
    version_number: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve specific historical version of lesson content (faculty and admin only)"""
    res = await db.execute(select(CourseLesson).where(CourseLesson.id == lesson_id))
    lesson = res.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")

    mod = await db.get(CourseModule, lesson.module_id)
    course = await db.get(Course, mod.course_id) if mod else None
    check_course_admin_or_faculty_access(current_user, course)

    v_res = await db.execute(
        select(LessonContentVersion)
        .where(
            LessonContentVersion.lesson_id == lesson_id,
            LessonContentVersion.version_number == version_number
        )
    )
    target = v_res.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")

    return target


@router.post("/api/lessons/{lesson_id}/content/rollback/{version_number}", response_model=LessonContentOut)
async def rollback_content_version(
    lesson_id: int,
    version_number: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Rollback lesson content to a prior version, appending a new version with
    the restored content and maintaining full version lineage.
    """
    res = await db.execute(select(CourseLesson).where(CourseLesson.id == lesson_id))
    lesson = res.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")

    mod = await db.get(CourseModule, lesson.module_id)
    course = await db.get(Course, mod.course_id) if mod else None
    check_course_admin_or_faculty_access(current_user, course)

    v_res = await db.execute(
        select(LessonContentVersion)
        .where(
            LessonContentVersion.lesson_id == lesson_id,
            LessonContentVersion.version_number == version_number
        )
    )
    target = v_res.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target revision not found")

    # Determine next version
    q_ver = select(func.max(LessonContentVersion.version_number)).where(
        LessonContentVersion.lesson_id == lesson_id
    )
    max_ver = (await db.execute(q_ver)).scalar() or 0
    next_ver = max_ver + 1

    # Mark existing as not current
    await db.execute(
        update(LessonContentVersion)
        .where(LessonContentVersion.lesson_id == lesson_id)
        .values(is_current=False)
    )

    restored = LessonContentVersion(
        lesson_id=lesson_id,
        version_number=next_ver,
        content_format=target.content_format,
        raw_content=target.raw_content,
        rendered_content=target.rendered_content,
        widget_configs=target.widget_configs,
        author_id=current_user.id,
        change_summary=f"Rollback to version {version_number}",
        is_current=True,
    )
    db.add(restored)
    lesson.content = target.rendered_content
    await db.commit()
    await db.refresh(restored)
    return restored


# ─── Course Workspace Architecture ───────────────────────────────────────────

@router.get("/api/courses/{course_id}/workspace", response_model=CourseWorkspaceOut)
async def get_course_workspace(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Unified course learning workspace hub.
    Enforces authorization: Accessible only to enrolled students or course instructors/administrators.
    """
    q = select(Course).where(Course.id == course_id).options(
        selectinload(Course.lecturer).selectinload(Lecturer.user),
        selectinload(Course.modules).selectinload(CourseModule.lessons),
        selectinload(Course.assignments),
        selectinload(Course.announcements).selectinload(CourseAnnouncement.author),
        selectinload(Course.live_sessions),
        selectinload(Course.enrollments).selectinload(Enrollment.student)
    )
    res = await db.execute(q)
    course = res.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    is_admin = role_val in {UserRole.ADMIN.value, UserRole.DEAN.value}
    is_instructor = bool(course.lecturer and course.lecturer.user_id == current_user.id)

    # Check student enrollment
    is_enrolled_student = False
    enrollment_status = None
    if role_val == UserRole.STUDENT.value:
        for enr in course.enrollments:
            if enr.student and enr.student.user_id == current_user.id:
                enrollment_status = enr.status
                if enr.status in {"active", "completed"}:
                    is_enrolled_student = True
                break

    if not (is_admin or is_instructor or is_enrolled_student):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You must be actively enrolled in or instructor of this course to access the workspace."
        )

    # Calculate active stats
    active_students = len([e for e in course.enrollments if e.status == "active"])
    sorted_modules = sorted(course.modules, key=lambda m: m.order_index)
    sorted_assignments = sorted(course.assignments, key=lambda a: a.due_date if a.due_date else datetime.max)

    modules_data = [
        {
            "id": m.id,
            "order_index": m.order_index,
            "title": m.title,
            "description": m.description,
            "learning_objectives": m.learning_objectives,
            "estimated_hours": m.estimated_hours,
            "status": m.status,
            "unlock_at": m.unlock_at.isoformat() if m.unlock_at else None,
            "is_active": m.is_active,
            "lessons": [
                {
                    "id": l.id,
                    "title": l.title,
                    "lesson_type": l.lesson_type,
                    "estimated_minutes": l.estimated_minutes,
                    "order_index": l.order_index,
                    "is_required": l.is_required,
                    "is_published": l.is_published,
                }
                for l in sorted(m.lessons, key=lambda x: x.order_index)
                if l.is_published or is_admin or is_instructor
            ]
        }
        for m in sorted_modules if m.is_active or is_admin or is_instructor
    ]

    assignments_data = [
        {
            "id": a.id,
            "title": a.title,
            "description": a.description,
            "due_date": a.due_date.isoformat() if a.due_date else None,
            "max_marks": a.max_marks,
            "type": a.assignment_type
        }
        for a in sorted_assignments
    ]

    lecturer_info = None
    if course.lecturer:
        lecturer_info = {
            "id": course.lecturer.id,
            "full_name": course.lecturer.user.full_name if course.lecturer.user else "Faculty Instructor",
            "email": course.lecturer.user.email if course.lecturer.user else None,
            "office_location": course.lecturer.office_location,
            "office_hours": course.lecturer.office_hours
        }

    now = datetime.utcnow()
    recent_announcements = [
        {
            "id": ann.id,
            "title": ann.title,
            "content": ann.content[:200],
            "priority": ann.priority,
            "is_pinned": ann.is_pinned,
            "published_at": ann.published_at.isoformat() if ann.published_at else None,
            "author_name": ann.author.full_name if ann.author else "Instructor",
        }
        for ann in course.announcements[:5]
        if is_admin or is_instructor or (ann.published_at and ann.published_at <= now)
    ]

    upcoming_sessions = [
        {
            "id": s.id,
            "title": s.title,
            "provider": s.provider,
            "start_time": s.start_time.isoformat() if s.start_time else None,
            "end_time": s.end_time.isoformat() if s.end_time else None,
            "status": s.status,
            "join_url": s.join_url,
        }
        for s in course.live_sessions
        if s.status in {"scheduled", "live"}
    ]

    return CourseWorkspaceOut(
        course_id=course.id,
        course_code=course.course_code,
        title=course.title,
        description=course.description,
        credits=course.credits,
        delivery_method=course.delivery_method,
        learning_outcomes=course.learning_outcomes,
        schedule=course.schedule,
        banner_url=course.banner_url,
        syllabus_data=course.syllabus_data,
        workspace_settings=course.workspace_settings,
        lecturer=lecturer_info,
        stats={
            "enrolled_count": active_students,
            "modules_count": len(modules_data),
            "assignments_count": len(assignments_data)
        },
        user_context={
            "role": role_val,
            "is_instructor": is_instructor,
            "is_admin": is_admin,
            "enrollment_status": enrollment_status
        },
        modules=modules_data,
        recent_announcements=recent_announcements,
        active_assignments=assignments_data,
        upcoming_live_sessions=upcoming_sessions
    )


@router.put("/api/courses/{course_id}/workspace/settings")
async def update_course_workspace_settings(
    course_id: int,
    payload: CourseWorkspaceSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update course syllabus, banner, and workspace configurations (Instructor/Admin only)"""
    res = await db.execute(
        select(Course).where(Course.id == course_id).options(selectinload(Course.lecturer))
    )
    course = res.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    is_admin = role_val in {UserRole.ADMIN.value, UserRole.DEAN.value}
    is_instructor = bool(course.lecturer and course.lecturer.user_id == current_user.id)

    if not (is_admin or is_instructor):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Instructor or administrative privileges required to update workspace settings."
        )

    if payload.syllabus_data is not None:
        course.syllabus_data = payload.syllabus_data
    if payload.workspace_settings is not None:
        course.workspace_settings = payload.workspace_settings
    if payload.banner_url is not None:
        course.banner_url = payload.banner_url

    await db.commit()
    await db.refresh(course)
    return {
        "course_id": course.id,
        "syllabus_data": course.syllabus_data,
        "workspace_settings": course.workspace_settings,
        "banner_url": course.banner_url
    }
