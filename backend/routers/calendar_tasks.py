"""backend/routers/calendar_tasks.py
Enterprise Student Calendar and Task Management Router
Unified academic and personal calendar events, deadlines, reminders,
and personal study task tracking with metrics and status workflows.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.models import (
    User,
    Student,
    Course,
    Enrollment,
    Assignment,
    Quiz,
    VirtualClassroomSession,
    StudentTask,
    CalendarEvent,
)
from backend.schemas import (
    StudentTaskCreate,
    StudentTaskUpdate,
    StudentTaskStatusPatch,
    StudentTaskOut,
    StudentTaskMetrics,
    CalendarEventCreate,
    CalendarEventUpdate,
    CalendarEventOut,
)
from backend.utils.security import get_current_user, require_roles

router = APIRouter(tags=["Calendar & Task Management"])


def serialize_task(task: StudentTask) -> StudentTaskOut:
    now = datetime.utcnow()
    is_overdue = bool(task.due_date and task.due_date < now and task.status != "completed")
    course_code = task.course.course_code if task.course else None
    course_title = task.course.title if task.course else None

    return StudentTaskOut(
        id=task.id,
        student_id=task.student_id,
        course_id=task.course_id,
        course_code=course_code,
        course_title=course_title,
        title=task.title,
        description=task.description,
        due_date=task.due_date,
        priority=task.priority,
        status=task.status,
        category=task.category,
        estimated_minutes=task.estimated_minutes,
        completed_at=task.completed_at,
        reminder_at=task.reminder_at,
        is_overdue=is_overdue,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


def serialize_calendar_event(event: CalendarEvent) -> CalendarEventOut:
    course_code = event.course.course_code if event.course else None
    return CalendarEventOut(
        id=event.id,
        user_id=event.user_id,
        course_id=event.course_id,
        course_code=course_code,
        title=event.title,
        description=event.description,
        event_type=event.event_type,
        start_time=event.start_time,
        end_time=event.end_time,
        all_day=event.all_day,
        location=event.location,
        color=event.color,
        is_system_generated=event.is_system_generated,
        created_at=event.created_at,
    )


# ─── Student Task Endpoints ───────────────────────────────────────────────────

@router.get("/api/tasks", response_model=List[StudentTaskOut])
async def list_student_tasks(
    status_filter: Optional[str] = Query(None, alias="status"),
    course_id: Optional[int] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve all tasks for the authenticated student with optional filtering."""
    s_res = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = s_res.scalars().first()
    if not student:
        raise HTTPException(status_code=403, detail="Only students have personal task management.")

    query = (
        select(StudentTask)
        .options(selectinload(StudentTask.course))
        .where(StudentTask.student_id == student.id)
    )
    if status_filter:
        query = query.where(StudentTask.status == status_filter.lower())
    if course_id:
        query = query.where(StudentTask.course_id == course_id)
    if priority:
        query = query.where(StudentTask.priority == priority.lower())
    if category:
        query = query.where(StudentTask.category == category.lower())

    query = query.order_by(StudentTask.due_date.asc().nullslast(), StudentTask.created_at.desc())
    res = await db.execute(query)
    tasks = res.scalars().all()
    return [serialize_task(t) for t in tasks]


@router.post("/api/tasks", response_model=StudentTaskOut, status_code=status.HTTP_201_CREATED)
async def create_student_task(
    payload: StudentTaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new study or personal task."""
    s_res = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = s_res.scalars().first()
    if not student:
        raise HTTPException(status_code=403, detail="Only students have personal task management.")

    if payload.course_id:
        c_res = await db.execute(select(Course).where(Course.id == payload.course_id))
        if not c_res.scalars().first():
            raise HTTPException(status_code=404, detail="Course not found.")

    task = StudentTask(
        student_id=student.id,
        course_id=payload.course_id,
        title=payload.title,
        description=payload.description,
        due_date=payload.due_date,
        priority=payload.priority.lower(),
        status="todo",
        category=payload.category.lower(),
        estimated_minutes=payload.estimated_minutes,
        reminder_at=payload.reminder_at,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    # Reload relationships
    t_res = await db.execute(
        select(StudentTask).options(selectinload(StudentTask.course)).where(StudentTask.id == task.id)
    )
    return serialize_task(t_res.scalars().first())


@router.put("/api/tasks/{task_id}", response_model=StudentTaskOut)
async def update_student_task(
    task_id: int,
    payload: StudentTaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update task details."""
    s_res = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = s_res.scalars().first()
    if not student:
        raise HTTPException(status_code=403, detail="Unauthorized.")

    t_res = await db.execute(
        select(StudentTask)
        .options(selectinload(StudentTask.course))
        .where(StudentTask.id == task_id, StudentTask.student_id == student.id)
    )
    task = t_res.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    if payload.title is not None:
        task.title = payload.title
    if payload.description is not None:
        task.description = payload.description
    if payload.due_date is not None:
        task.due_date = payload.due_date
    if payload.priority is not None:
        task.priority = payload.priority.lower()
    if payload.status is not None:
        old_status = task.status
        task.status = payload.status.lower()
        if task.status == "completed" and old_status != "completed":
            task.completed_at = datetime.utcnow()
        elif task.status != "completed":
            task.completed_at = None
    if payload.category is not None:
        task.category = payload.category.lower()
    if payload.estimated_minutes is not None:
        task.estimated_minutes = payload.estimated_minutes
    if payload.reminder_at is not None:
        task.reminder_at = payload.reminder_at

    await db.commit()
    await db.refresh(task)
    return serialize_task(task)


@router.patch("/api/tasks/{task_id}/status", response_model=StudentTaskOut)
async def patch_task_status(
    task_id: int,
    payload: StudentTaskStatusPatch,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Quickly update the progress status of a task."""
    s_res = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = s_res.scalars().first()
    if not student:
        raise HTTPException(status_code=403, detail="Unauthorized.")

    t_res = await db.execute(
        select(StudentTask)
        .options(selectinload(StudentTask.course))
        .where(StudentTask.id == task_id, StudentTask.student_id == student.id)
    )
    task = t_res.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    new_stat = payload.status.lower()
    task.status = new_stat
    if new_stat == "completed":
        task.completed_at = datetime.utcnow()
    else:
        task.completed_at = None

    await db.commit()
    await db.refresh(task)
    return serialize_task(task)


@router.delete("/api/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a task."""
    s_res = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = s_res.scalars().first()
    if not student:
        raise HTTPException(status_code=403, detail="Unauthorized.")

    t_res = await db.execute(
        select(StudentTask).where(StudentTask.id == task_id, StudentTask.student_id == student.id)
    )
    task = t_res.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    await db.delete(task)
    await db.commit()
    return None


@router.get("/api/tasks/metrics", response_model=StudentTaskMetrics)
async def get_task_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Calculate overall productivity and completion metrics for the student's tasks."""
    s_res = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = s_res.scalars().first()
    if not student:
        raise HTTPException(status_code=403, detail="Unauthorized.")

    res = await db.execute(select(StudentTask).where(StudentTask.student_id == student.id))
    tasks = res.scalars().all()

    now = datetime.utcnow()
    today_start = datetime(now.year, now.month, now.day)
    today_end = today_start + timedelta(days=1)

    total = len(tasks)
    completed = sum(1 for t in tasks if t.status == "completed")
    pending = total - completed
    overdue = sum(1 for t in tasks if t.due_date and t.due_date < now and t.status != "completed")
    rate = round((completed / total) * 100, 1) if total > 0 else 100.0
    due_today = sum(
        1 for t in tasks if t.due_date and today_start <= t.due_date < today_end and t.status != "completed"
    )
    urgent_cnt = sum(1 for t in tasks if t.priority == "urgent" and t.status != "completed")

    return StudentTaskMetrics(
        total_tasks=total,
        completed_tasks=completed,
        pending_tasks=pending,
        overdue_tasks=overdue,
        completion_rate=rate,
        due_today_count=due_today,
        urgent_priority_count=urgent_cnt,
    )


# ─── Unified Calendar Endpoints ───────────────────────────────────────────────

@router.get("/api/calendar/events", response_model=List[CalendarEventOut])
async def get_calendar_events(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Unified calendar aggregation feed combining personal events, assignment deadlines, and lectures."""
    start_bound = start_date or (datetime.utcnow() - timedelta(days=30))
    end_bound = end_date or (datetime.utcnow() + timedelta(days=90))

    # 1. Custom and assigned Calendar Events
    ev_query = (
        select(CalendarEvent)
        .options(selectinload(CalendarEvent.course))
        .where(
            or_(
                CalendarEvent.user_id == current_user.id,
                CalendarEvent.user_id.is_(None),  # campus-wide
            ),
            CalendarEvent.start_time >= start_bound,
            CalendarEvent.start_time <= end_bound,
        )
    )
    ev_res = await db.execute(ev_query)
    events = [serialize_calendar_event(e) for e in ev_res.scalars().all()]

    # 2. If student, pull enrolled course assignment deadlines as system events
    if current_user.role == "student":
        s_res = await db.execute(select(Student).where(Student.user_id == current_user.id))
        student = s_res.scalars().first()
        if student:
            enr_res = await db.execute(
                select(Enrollment.course_id).where(
                    Enrollment.student_id == student.id,
                    Enrollment.status.in_(["enrolled", "active", "completed"]),
                )
            )
            course_ids = [r[0] for r in enr_res.all()]
            if course_ids:
                # Assignments
                asg_res = await db.execute(
                    select(Assignment)
                    .options(selectinload(Assignment.course))
                    .where(
                        Assignment.course_id.in_(course_ids),
                        Assignment.due_date >= start_bound,
                        Assignment.due_date <= end_bound,
                    )
                )
                for a in asg_res.scalars().all():
                    events.append(
                        CalendarEventOut(
                            id=100000 + a.id,
                            user_id=None,
                            course_id=a.course_id,
                            course_code=a.course.course_code if a.course else None,
                            title=f"Due: {a.title}",
                            description=f"Assignment deadline for {a.course.course_code if a.course else ''}",
                            event_type="assignment_due",
                            start_time=a.due_date,
                            end_time=a.due_date + timedelta(minutes=30),
                            all_day=False,
                            location="Online Submission",
                            color="#F59E0B",
                            is_system_generated=True,
                            created_at=a.due_date,
                        )
                    )

                # Virtual Classroom Live Sessions
                vc_res = await db.execute(
                    select(VirtualClassroomSession)
                    .options(selectinload(VirtualClassroomSession.course))
                    .where(
                        VirtualClassroomSession.course_id.in_(course_ids),
                        VirtualClassroomSession.start_time >= start_bound,
                        VirtualClassroomSession.start_time <= end_bound,
                    )
                )
                for vc in vc_res.scalars().all():
                    dur = timedelta(minutes=vc.duration_minutes or 60)
                    events.append(
                        CalendarEventOut(
                            id=200000 + vc.id,
                            user_id=None,
                            course_id=vc.course_id,
                            course_code=vc.course.course_code if vc.course else None,
                            title=f"Class: {vc.title}",
                            description=f"Virtual live lecture for {vc.course.course_code if vc.course else ''}",
                            event_type="lecture",
                            start_time=vc.start_time,
                            end_time=vc.start_time + dur,
                            all_day=False,
                            location=vc.room_name or "Virtual Room",
                            color="#10B981",
                            is_system_generated=True,
                            created_at=vc.start_time,
                        )
                    )

    # Sort all events chronologically
    events.sort(key=lambda x: x.start_time)
    return events


@router.post("/api/calendar/events", response_model=CalendarEventOut, status_code=status.HTTP_201_CREATED)
async def create_calendar_event(
    payload: CalendarEventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a personal or course-linked calendar event."""
    if payload.start_time >= payload.end_time:
        raise HTTPException(status_code=400, detail="start_time must be strictly before end_time.")

    event = CalendarEvent(
        user_id=current_user.id,
        course_id=payload.course_id,
        title=payload.title,
        description=payload.description,
        event_type=payload.event_type.lower(),
        start_time=payload.start_time,
        end_time=payload.end_time,
        all_day=payload.all_day,
        location=payload.location,
        color=payload.color,
        is_system_generated=False,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)

    ev_res = await db.execute(
        select(CalendarEvent).options(selectinload(CalendarEvent.course)).where(CalendarEvent.id == event.id)
    )
    return serialize_calendar_event(ev_res.scalars().first())


@router.put("/api/calendar/events/{event_id}", response_model=CalendarEventOut)
async def update_calendar_event(
    event_id: int,
    payload: CalendarEventUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a custom calendar event owned by the user."""
    ev_res = await db.execute(
        select(CalendarEvent)
        .options(selectinload(CalendarEvent.course))
        .where(CalendarEvent.id == event_id)
    )
    event = ev_res.scalars().first()
    if not event:
        raise HTTPException(status_code=404, detail="Calendar event not found.")

    if event.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="You do not have permission to modify this event.")

    if payload.title is not None:
        event.title = payload.title
    if payload.description is not None:
        event.description = payload.description
    if payload.event_type is not None:
        event.event_type = payload.event_type.lower()
    if payload.start_time is not None:
        event.start_time = payload.start_time
    if payload.end_time is not None:
        event.end_time = payload.end_time
    if payload.all_day is not None:
        event.all_day = payload.all_day
    if payload.location is not None:
        event.location = payload.location
    if payload.color is not None:
        event.color = payload.color

    if event.start_time >= event.end_time:
        raise HTTPException(status_code=400, detail="start_time must be strictly before end_time.")

    await db.commit()
    await db.refresh(event)
    return serialize_calendar_event(event)


@router.delete("/api/calendar/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_calendar_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a custom calendar event owned by the user."""
    ev_res = await db.execute(select(CalendarEvent).where(CalendarEvent.id == event_id))
    event = ev_res.scalars().first()
    if not event:
        raise HTTPException(status_code=404, detail="Calendar event not found.")

    if event.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="You do not have permission to delete this event.")

    await db.delete(event)
    await db.commit()
    return None
