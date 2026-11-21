"""
NSBM EduSphere — Video Learning Delivery Router
Manages streaming video metadata, captions, chapters, timestamps, and
granular student playback progress telemetry (bookmarks, notes, watch percentage).
"""
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.models import (
    Course, CourseModule, CourseLesson, CourseVideo, VideoPlaybackProgress,
    Enrollment, User, UserRole, Student, Lecturer
)
from backend.schemas import (
    CourseVideoCreate, CourseVideoUpdate, CourseVideoOut,
    VideoPlaybackProgressUpdate, VideoPlaybackProgressOut
)
from backend.core.dependencies import get_current_user

router = APIRouter(tags=["Video Learning Delivery"])


def check_course_admin_or_faculty_access(current_user: User, course: Optional[Course] = None):
    """Allows Admins or assigned Lecturers to manage course video content"""
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


# ─── Video Delivery Endpoints ─────────────────────────────────────────────────

@router.post("/api/courses/{course_id}/videos", response_model=CourseVideoOut, status_code=201)
async def create_course_video(
    course_id: int,
    payload: CourseVideoCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Publishes a video learning item with chapters and caption tracks"""
    course = await db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    check_course_admin_or_faculty_access(current_user, course)

    if payload.module_id:
        mod = await db.get(CourseModule, payload.module_id)
        if not mod or mod.course_id != course_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid module ID for this course")

    if payload.lesson_id:
        les = await db.get(CourseLesson, payload.lesson_id)
        if not les:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid lesson ID")

    video = CourseVideo(
        course_id=course_id,
        module_id=payload.module_id,
        lesson_id=payload.lesson_id,
        title=payload.title.strip(),
        description=payload.description,
        provider=payload.provider,
        video_url=payload.video_url.strip(),
        duration_seconds=payload.duration_seconds,
        thumbnail_url=payload.thumbnail_url,
        captions_track=payload.captions_track,
        chapters=payload.chapters,
        is_published=payload.is_published,
    )
    db.add(video)
    await db.commit()
    await db.refresh(video)
    return video


@router.get("/api/courses/{course_id}/videos", response_model=List[CourseVideoOut])
async def list_course_videos(
    course_id: int,
    module_id: Optional[int] = Query(None, description="Filter by module"),
    lesson_id: Optional[int] = Query(None, description="Filter by lesson"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists videos for a course and includes student's personal playback progress"""
    course, student = await check_course_read_access(current_user, course_id, db)

    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    is_admin = role_val in {UserRole.ADMIN.value, UserRole.DEAN.value}
    is_instructor = bool(
        course.lecturer_id and hasattr(current_user, "lecturer_profile") and
        current_user.lecturer_profile and current_user.lecturer_profile.id == course.lecturer_id
    )

    q = select(CourseVideo).where(CourseVideo.course_id == course_id)
    if not (is_admin or is_instructor):
        q = q.where(CourseVideo.is_published == True)

    if module_id is not None:
        q = q.where(CourseVideo.module_id == module_id)
    if lesson_id is not None:
        q = q.where(CourseVideo.lesson_id == lesson_id)

    q = q.order_by(CourseVideo.created_at.desc())
    res = await db.execute(q)
    videos = list(res.scalars().all())

    # If student, retrieve personal progress
    progress_map = {}
    if student:
        video_ids = [v.id for v in videos]
        if video_ids:
            p_res = await db.execute(
                select(VideoPlaybackProgress)
                .where(
                    VideoPlaybackProgress.video_id.in_(video_ids),
                    VideoPlaybackProgress.student_id == student.id
                )
            )
            for prog in p_res.scalars().all():
                progress_map[prog.video_id] = prog

    output = []
    for vid in videos:
        v_dict = {
            "id": vid.id,
            "course_id": vid.course_id,
            "module_id": vid.module_id,
            "lesson_id": vid.lesson_id,
            "title": vid.title,
            "description": vid.description,
            "provider": vid.provider,
            "video_url": vid.video_url,
            "duration_seconds": vid.duration_seconds,
            "thumbnail_url": vid.thumbnail_url,
            "captions_track": vid.captions_track,
            "chapters": vid.chapters,
            "is_published": vid.is_published,
            "playback_progress": progress_map.get(vid.id),
            "created_at": vid.created_at,
            "updated_at": vid.updated_at,
        }
        output.append(CourseVideoOut(**v_dict))

    return output


@router.get("/api/videos/{video_id}", response_model=CourseVideoOut)
async def get_video_details(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves single video details with chapters, captions, and student progress"""
    res = await db.execute(select(CourseVideo).where(CourseVideo.id == video_id))
    video = res.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")

    course, student = await check_course_read_access(current_user, video.course_id, db)

    prog = None
    if student:
        p_res = await db.execute(
            select(VideoPlaybackProgress)
            .where(
                VideoPlaybackProgress.video_id == video_id,
                VideoPlaybackProgress.student_id == student.id
            )
        )
        prog = p_res.scalar_one_or_none()

    v_dict = {
        "id": video.id,
        "course_id": video.course_id,
        "module_id": video.module_id,
        "lesson_id": video.lesson_id,
        "title": video.title,
        "description": video.description,
        "provider": video.provider,
        "video_url": video.video_url,
        "duration_seconds": video.duration_seconds,
        "thumbnail_url": video.thumbnail_url,
        "captions_track": video.captions_track,
        "chapters": video.chapters,
        "is_published": video.is_published,
        "playback_progress": prog,
        "created_at": video.created_at,
        "updated_at": video.updated_at,
    }
    return CourseVideoOut(**v_dict)


@router.put("/api/videos/{video_id}", response_model=CourseVideoOut)
async def update_video(
    video_id: int,
    payload: CourseVideoUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Updates video learning item metadata"""
    res = await db.execute(select(CourseVideo).where(CourseVideo.id == video_id))
    video = res.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")

    course = await db.get(Course, video.course_id)
    check_course_admin_or_faculty_access(current_user, course)

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(video, field, val)

    await db.commit()
    await db.refresh(video)
    return video


@router.delete("/api/videos/{video_id}", status_code=204)
async def delete_video(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Removes a video learning item"""
    res = await db.execute(select(CourseVideo).where(CourseVideo.id == video_id))
    video = res.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")

    course = await db.get(Course, video.course_id)
    check_course_admin_or_faculty_access(current_user, course)

    await db.delete(video)
    await db.commit()
    return None


# ─── Video Telemetry & Playback Tracking ──────────────────────────────────────

@router.post("/api/videos/{video_id}/progress", response_model=VideoPlaybackProgressOut)
async def update_playback_progress(
    video_id: int,
    payload: VideoPlaybackProgressUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Records student video watch telemetry, updates max watched position,
    computes completion percentage, and saves bookmarks/notes with timestamps.
    """
    res = await db.execute(select(CourseVideo).where(CourseVideo.id == video_id))
    video = res.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")

    course, student = await check_course_read_access(current_user, video.course_id, db)
    if not student:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only enrolled students have playback records")

    p_res = await db.execute(
        select(VideoPlaybackProgress)
        .where(
            VideoPlaybackProgress.video_id == video_id,
            VideoPlaybackProgress.student_id == student.id
        )
    )
    prog = p_res.scalar_one_or_none()

    now = datetime.utcnow()
    if not prog:
        prog = VideoPlaybackProgress(
            video_id=video_id,
            student_id=student.id,
            last_position_seconds=payload.position_seconds,
            max_watched_seconds=payload.position_seconds,
            watch_percentage=0.0,
            is_completed=False,
            bookmarks=[],
            notes=[],
        )
        db.add(prog)

    prog.last_position_seconds = payload.position_seconds
    prog.max_watched_seconds = max(prog.max_watched_seconds or 0, payload.position_seconds)

    # Calculate watch percentage
    current_pct = prog.watch_percentage or 0.0
    if payload.watch_percentage is not None:
        prog.watch_percentage = max(current_pct, payload.watch_percentage)
    elif video.duration_seconds > 0:
        calc_pct = round((prog.max_watched_seconds / video.duration_seconds) * 100.0, 1)
        prog.watch_percentage = max(current_pct, min(100.0, calc_pct))

    # Evaluate completion
    if payload.is_completed or prog.watch_percentage >= 90.0:
        if not prog.is_completed:
            prog.is_completed = True
            prog.completed_at = now

    # Add bookmark
    if payload.add_bookmark:
        bm_list = list(prog.bookmarks or [])
        bm_list.append(payload.add_bookmark)
        prog.bookmarks = bm_list

    # Add note
    if payload.add_note:
        notes_list = list(prog.notes or [])
        notes_list.append(payload.add_note)
        prog.notes = notes_list

    await db.commit()
    await db.refresh(prog)
    return prog


@router.get("/api/videos/{video_id}/progress", response_model=VideoPlaybackProgressOut)
async def get_playback_progress(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves student's personal playback telemetry and notes for a video"""
    res = await db.execute(select(CourseVideo).where(CourseVideo.id == video_id))
    video = res.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")

    course, student = await check_course_read_access(current_user, video.course_id, db)
    if not student:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only enrolled students have playback records")

    p_res = await db.execute(
        select(VideoPlaybackProgress)
        .where(
            VideoPlaybackProgress.video_id == video_id,
            VideoPlaybackProgress.student_id == student.id
        )
    )
    prog = p_res.scalar_one_or_none()
    if not prog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No playback telemetry recorded yet")

    return prog
