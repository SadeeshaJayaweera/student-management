"""
NSBM EduSphere — Course Announcements & Communication Router
Manages priority broadcasting, pinned announcements, cohort targeting, scheduled drip release,
read acknowledgements, and multi-channel student notifications.
"""
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.models import (
    Course, CourseAnnouncement, AnnouncementAcknowledgement, CohortMember,
    Enrollment, User, UserRole, Student
)
from backend.schemas import (
    CourseAnnouncementCreate, CourseAnnouncementUpdate, CourseAnnouncementOut,
    AnnouncementAcknowledgeOut
)
from backend.core.dependencies import get_current_user
from backend.core.sanitization import sanitize_rich_content

router = APIRouter(tags=["Course Announcements & Communication"])


def check_course_admin_or_faculty_access(current_user: User, course: Optional[Course] = None):
    """Allows Admins or assigned Lecturers to broadcast announcements"""
    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if role_val in {UserRole.ADMIN.value, UserRole.DEAN.value}:
        return
    if course and role_val == UserRole.LECTURER.value:
        lec = getattr(current_user, "lecturer", None) or getattr(current_user, "lecturer_profile", None)
        if lec and course.lecturer_id == lec.id:
            return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Administrative or assigned faculty permissions required."
    )


async def check_course_read_access(current_user: User, course_id: int, db: AsyncSession) -> Tuple[Course, Optional[Student]]:
    """Verifies that user is either course instructor, admin, or actively enrolled student"""
    res = await db.execute(
        select(Course)
        .where(Course.id == course_id)
        .options(
            selectinload(Course.lecturer),
            selectinload(Course.enrollments).selectinload(Enrollment.student)
        )
    )
    course = res.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    is_admin = role_val in {UserRole.ADMIN.value, UserRole.DEAN.value}
    is_instructor = bool(
        course.lecturer_id and hasattr(current_user, "lecturer_profile") and
        current_user.lecturer_profile and current_user.lecturer_profile.id == course.lecturer_id
    )

    if is_admin or is_instructor:
        return course, None

    # Check student enrollment
    if role_val == UserRole.STUDENT.value:
        for enr in course.enrollments:
            if enr.student and enr.student.user_id == current_user.id and enr.status in {"active", "completed"}:
                return course, enr.student

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied: You must be actively enrolled in or instructor of this course."
    )


# ─── Announcement Endpoints ───────────────────────────────────────────────────

@router.post("/api/courses/{course_id}/announcements", response_model=CourseAnnouncementOut, status_code=201)
async def create_course_announcement(
    course_id: int,
    payload: CourseAnnouncementCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Broadcasts a course announcement with priority tagging and pinning"""
    course = await db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    check_course_admin_or_faculty_access(current_user, course)

    cleaned_content = sanitize_rich_content(payload.content)
    now = datetime.utcnow()

    announcement = CourseAnnouncement(
        course_id=course_id,
        author_id=current_user.id,
        cohort_id=payload.cohort_id,
        title=payload.title.strip(),
        content=cleaned_content,
        priority=payload.priority,
        is_pinned=payload.is_pinned,
        requires_acknowledgement=payload.requires_acknowledgement,
        published_at=payload.published_at or now,
    )
    db.add(announcement)
    await db.commit()
    await db.refresh(announcement)

    return CourseAnnouncementOut(
        id=announcement.id,
        course_id=announcement.course_id,
        author_id=announcement.author_id,
        author_name=current_user.full_name,
        cohort_id=announcement.cohort_id,
        title=announcement.title,
        content=announcement.content,
        priority=announcement.priority,
        is_pinned=announcement.is_pinned,
        requires_acknowledgement=announcement.requires_acknowledgement,
        is_acknowledged=False,
        acknowledgements_count=0,
        published_at=announcement.published_at,
        created_at=announcement.created_at,
        updated_at=announcement.updated_at,
    )


@router.get("/api/courses/{course_id}/announcements", response_model=List[CourseAnnouncementOut])
async def list_course_announcements(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists course announcements ordered by pinned status and publication date"""
    course, student = await check_course_read_access(current_user, course_id, db)

    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    is_admin = role_val in {UserRole.ADMIN.value, UserRole.DEAN.value}
    is_instructor = bool(
        course.lecturer_id and hasattr(current_user, "lecturer_profile") and
        current_user.lecturer_profile and current_user.lecturer_profile.id == course.lecturer_id
    )

    q = (
        select(CourseAnnouncement)
        .where(CourseAnnouncement.course_id == course_id)
        .options(selectinload(CourseAnnouncement.author), selectinload(CourseAnnouncement.acknowledgements))
        .order_by(desc(CourseAnnouncement.is_pinned), desc(CourseAnnouncement.published_at))
    )

    now = datetime.utcnow()
    res = await db.execute(q)
    all_announcements = list(res.scalars().all())

    # If student, filter by publication date and cohort
    student_cohort_ids = set()
    acknowledged_announcement_ids = set()
    if student:
        # Load cohorts student belongs to
        c_res = await db.execute(select(CohortMember.cohort_id).where(CohortMember.student_id == student.id))
        student_cohort_ids = set(c_res.scalars().all())

        # Load student acknowledgements
        a_res = await db.execute(
            select(AnnouncementAcknowledgement.announcement_id)
            .where(AnnouncementAcknowledgement.student_id == student.id)
        )
        acknowledged_announcement_ids = set(a_res.scalars().all())

    output = []
    for ann in all_announcements:
        if not (is_admin or is_instructor):
            if ann.published_at and ann.published_at > now:
                continue
            if ann.cohort_id and ann.cohort_id not in student_cohort_ids:
                continue

        is_ack = ann.id in acknowledged_announcement_ids
        author_name = ann.author.full_name if ann.author else "Instructor"

        output.append(
            CourseAnnouncementOut(
                id=ann.id,
                course_id=ann.course_id,
                author_id=ann.author_id,
                author_name=author_name,
                cohort_id=ann.cohort_id,
                title=ann.title,
                content=ann.content,
                priority=ann.priority,
                is_pinned=ann.is_pinned,
                requires_acknowledgement=ann.requires_acknowledgement,
                is_acknowledged=is_ack,
                acknowledgements_count=len(ann.acknowledgements),
                published_at=ann.published_at,
                created_at=ann.created_at,
                updated_at=ann.updated_at,
            )
        )

    return output


@router.get("/api/announcements/{announcement_id}", response_model=CourseAnnouncementOut)
async def get_announcement_details(
    announcement_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves single course announcement details"""
    res = await db.execute(
        select(CourseAnnouncement)
        .where(CourseAnnouncement.id == announcement_id)
        .options(selectinload(CourseAnnouncement.author), selectinload(CourseAnnouncement.acknowledgements))
    )
    ann = res.scalar_one_or_none()
    if not ann:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found")

    course, student = await check_course_read_access(current_user, ann.course_id, db)

    is_ack = False
    if student:
        ack_res = await db.execute(
            select(AnnouncementAcknowledgement).where(
                AnnouncementAcknowledgement.announcement_id == announcement_id,
                AnnouncementAcknowledgement.student_id == student.id
            )
        )
        is_ack = ack_res.scalar_one_or_none() is not None

    return CourseAnnouncementOut(
        id=ann.id,
        course_id=ann.course_id,
        author_id=ann.author_id,
        author_name=ann.author.full_name if ann.author else "Instructor",
        cohort_id=ann.cohort_id,
        title=ann.title,
        content=ann.content,
        priority=ann.priority,
        is_pinned=ann.is_pinned,
        requires_acknowledgement=ann.requires_acknowledgement,
        is_acknowledged=is_ack,
        acknowledgements_count=len(ann.acknowledgements),
        published_at=ann.published_at,
        created_at=ann.created_at,
        updated_at=ann.updated_at,
    )


@router.put("/api/announcements/{announcement_id}", response_model=CourseAnnouncementOut)
async def update_course_announcement(
    announcement_id: int,
    payload: CourseAnnouncementUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Updates announcement content, priority, or pinned status"""
    res = await db.execute(
        select(CourseAnnouncement)
        .where(CourseAnnouncement.id == announcement_id)
        .options(selectinload(CourseAnnouncement.author), selectinload(CourseAnnouncement.acknowledgements))
    )
    ann = res.scalar_one_or_none()
    if not ann:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found")

    course = await db.get(Course, ann.course_id)
    check_course_admin_or_faculty_access(current_user, course)

    update_data = payload.model_dump(exclude_unset=True)
    if "content" in update_data and update_data["content"]:
        update_data["content"] = sanitize_rich_content(update_data["content"])

    for field, val in update_data.items():
        setattr(ann, field, val)

    await db.commit()
    await db.refresh(ann)

    return CourseAnnouncementOut(
        id=ann.id,
        course_id=ann.course_id,
        author_id=ann.author_id,
        author_name=ann.author.full_name if ann.author else "Instructor",
        cohort_id=ann.cohort_id,
        title=ann.title,
        content=ann.content,
        priority=ann.priority,
        is_pinned=ann.is_pinned,
        requires_acknowledgement=ann.requires_acknowledgement,
        is_acknowledged=False,
        acknowledgements_count=len(ann.acknowledgements),
        published_at=ann.published_at,
        created_at=ann.created_at,
        updated_at=ann.updated_at,
    )


@router.delete("/api/announcements/{announcement_id}", status_code=204)
async def delete_course_announcement(
    announcement_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Removes a course announcement"""
    res = await db.execute(select(CourseAnnouncement).where(CourseAnnouncement.id == announcement_id))
    ann = res.scalar_one_or_none()
    if not ann:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found")

    course = await db.get(Course, ann.course_id)
    check_course_admin_or_faculty_access(current_user, course)

    await db.delete(ann)
    await db.commit()
    return None


@router.post("/api/announcements/{announcement_id}/acknowledge", response_model=AnnouncementAcknowledgeOut)
async def acknowledge_announcement(
    announcement_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Student acknowledges reading an announcement"""
    res = await db.execute(select(CourseAnnouncement).where(CourseAnnouncement.id == announcement_id))
    ann = res.scalar_one_or_none()
    if not ann:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found")

    course, student = await check_course_read_access(current_user, ann.course_id, db)
    if not student:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only students can acknowledge announcements")

    ack_res = await db.execute(
        select(AnnouncementAcknowledgement).where(
            AnnouncementAcknowledgement.announcement_id == announcement_id,
            AnnouncementAcknowledgement.student_id == student.id
        )
    )
    ack = ack_res.scalar_one_or_none()
    now = datetime.utcnow()

    if not ack:
        ack = AnnouncementAcknowledgement(
            announcement_id=announcement_id,
            student_id=student.id,
            acknowledged_at=now,
        )
        db.add(ack)
        await db.commit()
        await db.refresh(ack)

    return ack
