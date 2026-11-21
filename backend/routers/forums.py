"""
NSBM EduSphere — Course Discussion Forums Router
Provides collaborative academic discourse, Q&A threads, nested replies,
instructor endorsements, verified solution marking, and interactive reactions
with strict BOLA authorization and anti-XSS sanitization.
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func, desc, update
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.models import (
    User, UserRole, Course, Lecturer, Enrollment,
    CourseForumCategory, ForumThread, ForumPost, ForumPostReaction
)
from backend.schemas import (
    CourseForumCategoryCreate, CourseForumCategoryUpdate, CourseForumCategoryOut,
    ForumThreadCreate, ForumThreadUpdate, ForumThreadSummaryOut, ForumThreadDetailOut,
    ForumPostCreate, ForumPostUpdate, ForumPostOut
)
from backend.utils.security import get_current_user
from backend.core.sanitization import sanitize_rich_content

router = APIRouter(tags=["Course Discussion Forums"])


async def verify_course_forum_access(
    course_id: int,
    current_user: User,
    db: AsyncSession
) -> tuple[Course, bool]:
    """
    Validates course existence and confirms that current_user has legitimate
    academic authorization (actively enrolled student, course instructor, or administrator).
    Returns (Course, is_instructor_or_admin).
    """
    q = select(Course).where(Course.id == course_id).options(
        selectinload(Course.lecturer),
        selectinload(Course.enrollments).selectinload(Enrollment.student)
    )
    res = await db.execute(q)
    course = res.scalar_one_or_none()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    is_admin = role_val in {UserRole.ADMIN.value, UserRole.DEAN.value}
    is_instructor = bool(course.lecturer and course.lecturer.user_id == current_user.id)
    is_instructor_or_admin = is_admin or is_instructor

    if is_instructor_or_admin:
        return course, True

    # Validate active student enrollment
    is_enrolled_student = False
    if role_val == UserRole.STUDENT.value:
        for enr in course.enrollments:
            if enr.student and enr.student.user_id == current_user.id:
                if enr.status in {"active", "completed"}:
                    is_enrolled_student = True
                break

    if not is_enrolled_student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You must be enrolled in or teaching this course to access discussion forums."
        )

    return course, False


async def fetch_post_out(post_id: int, current_user_id: int, db: AsyncSession) -> ForumPostOut:
    """Helper to fetch a post with its author and reactions eagerly loaded to prevent MissingGreenlet"""
    q = (
        select(ForumPost)
        .where(ForumPost.id == post_id)
        .options(
            selectinload(ForumPost.author),
            selectinload(ForumPost.reactions),
        )
    )
    res = await db.execute(q)
    post = res.scalar_one()
    has_reacted = any(r.user_id == current_user_id for r in post.reactions)
    author_name = post.author.full_name if post.author else "Unknown"

    return ForumPostOut(
        id=post.id,
        thread_id=post.thread_id,
        author_id=post.author_id,
        author_name=author_name,
        parent_post_id=post.parent_post_id,
        content=post.content,
        is_endorsed_by_instructor=post.is_endorsed_by_instructor,
        is_solution=post.is_solution,
        upvotes=post.upvotes or 0,
        user_has_reacted=has_reacted,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )


# ─── Category Endpoints ───────────────────────────────────────────────────────

@router.post("/api/courses/{course_id}/forums/categories", response_model=CourseForumCategoryOut, status_code=201)
async def create_forum_category(
    course_id: int,
    payload: CourseForumCategoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new discussion forum category (Instructors & Administrators only)"""
    course, is_instructor_or_admin = await verify_course_forum_access(course_id, current_user, db)
    if not is_instructor_or_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only course instructors and administrators can create forum categories."
        )

    cat = CourseForumCategory(
        course_id=course_id,
        title=payload.title.strip(),
        description=payload.description.strip() if payload.description else None,
        is_locked=payload.is_locked,
        display_order=payload.display_order,
    )
    db.add(cat)
    await db.commit()

    q = select(CourseForumCategory).where(CourseForumCategory.id == cat.id)
    res = await db.execute(q)
    fresh_cat = res.scalar_one()

    return CourseForumCategoryOut(
        id=fresh_cat.id,
        course_id=fresh_cat.course_id,
        title=fresh_cat.title,
        description=fresh_cat.description,
        is_locked=fresh_cat.is_locked,
        display_order=fresh_cat.display_order,
        thread_count=0,
        created_at=fresh_cat.created_at,
        updated_at=fresh_cat.updated_at,
    )


@router.get("/api/courses/{course_id}/forums/categories", response_model=List[CourseForumCategoryOut])
async def list_forum_categories(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all discussion categories for a course with thread statistics"""
    await verify_course_forum_access(course_id, current_user, db)

    q = (
        select(
            CourseForumCategory,
            func.count(ForumThread.id).label("thread_count")
        )
        .outerjoin(ForumThread, ForumThread.category_id == CourseForumCategory.id)
        .where(CourseForumCategory.course_id == course_id)
        .group_by(CourseForumCategory.id)
        .order_by(CourseForumCategory.display_order, CourseForumCategory.id)
    )
    res = await db.execute(q)
    rows = res.all()

    return [
        CourseForumCategoryOut(
            id=cat.id,
            course_id=cat.course_id,
            title=cat.title,
            description=cat.description,
            is_locked=cat.is_locked,
            display_order=cat.display_order,
            thread_count=count or 0,
            created_at=cat.created_at,
            updated_at=cat.updated_at,
        )
        for cat, count in rows
    ]


# ─── Thread Endpoints ─────────────────────────────────────────────────────────

@router.post("/api/courses/{course_id}/forums/threads", response_model=ForumThreadSummaryOut, status_code=201)
async def create_forum_thread(
    course_id: int,
    payload: ForumThreadCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Publish a new discussion thread with anti-XSS sanitized content"""
    course, is_instructor_or_admin = await verify_course_forum_access(course_id, current_user, db)

    # Validate category
    cat_res = await db.execute(
        select(CourseForumCategory).where(
            CourseForumCategory.id == payload.category_id,
            CourseForumCategory.course_id == course_id,
        )
    )
    category = cat_res.scalar_one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Forum category not found in this course"
        )

    if category.is_locked and not is_instructor_or_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This discussion category is locked for new topics."
        )

    if payload.is_pinned and not is_instructor_or_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only instructors and administrators can pin discussion threads."
        )

    sanitized_content = sanitize_rich_content(payload.content)

    thread = ForumThread(
        course_id=course_id,
        category_id=category.id,
        author_id=current_user.id,
        title=payload.title.strip(),
        content=sanitized_content,
        is_pinned=payload.is_pinned if is_instructor_or_admin else False,
        is_locked=False,
        view_count=0,
        reply_count=0,
    )
    db.add(thread)
    await db.commit()

    q = (
        select(ForumThread)
        .where(ForumThread.id == thread.id)
        .options(
            selectinload(ForumThread.category),
            selectinload(ForumThread.author),
        )
    )
    res = await db.execute(q)
    fresh_thread = res.scalar_one()

    author_name = fresh_thread.author.full_name if fresh_thread.author else "Unknown"

    return ForumThreadSummaryOut(
        id=fresh_thread.id,
        course_id=fresh_thread.course_id,
        category_id=fresh_thread.category_id,
        category_title=fresh_thread.category.title if fresh_thread.category else None,
        author_id=fresh_thread.author_id,
        author_name=author_name,
        title=fresh_thread.title,
        is_pinned=fresh_thread.is_pinned,
        is_locked=fresh_thread.is_locked,
        view_count=fresh_thread.view_count or 0,
        reply_count=fresh_thread.reply_count or 0,
        has_solution=False,
        created_at=fresh_thread.created_at,
        updated_at=fresh_thread.updated_at,
    )


@router.get("/api/courses/{course_id}/forums/threads", response_model=List[ForumThreadSummaryOut])
async def list_forum_threads(
    course_id: int,
    category_id: Optional[int] = Query(None, description="Filter by forum category"),
    search: Optional[str] = Query(None, description="Search keyword across title or content"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve discussion threads for a course with filtering and pinning priority"""
    await verify_course_forum_access(course_id, current_user, db)

    q = (
        select(ForumThread)
        .where(ForumThread.course_id == course_id)
        .options(
            selectinload(ForumThread.category),
            selectinload(ForumThread.author),
            selectinload(ForumThread.posts)
        )
    )

    if category_id is not None:
        q = q.where(ForumThread.category_id == category_id)

    if search:
        term = f"%{search.strip()}%"
        q = q.where(or_(ForumThread.title.ilike(term), ForumThread.content.ilike(term)))

    # Order pinned first, then newest updated
    q = q.order_by(desc(ForumThread.is_pinned), desc(ForumThread.updated_at))
    res = await db.execute(q)
    threads = res.scalars().all()

    items = []
    for t in threads:
        has_sol = any(p.is_solution for p in t.posts)
        author_name = t.author.full_name if t.author else "Unknown"
        items.append(
            ForumThreadSummaryOut(
                id=t.id,
                course_id=t.course_id,
                category_id=t.category_id,
                category_title=t.category.title if t.category else None,
                author_id=t.author_id,
                author_name=author_name,
                title=t.title,
                is_pinned=t.is_pinned,
                is_locked=t.is_locked,
                view_count=t.view_count or 0,
                reply_count=t.reply_count or 0,
                has_solution=has_sol,
                created_at=t.created_at,
                updated_at=t.updated_at,
            )
        )
    return items


@router.get("/api/forums/threads/{thread_id}", response_model=ForumThreadDetailOut)
async def get_forum_thread(
    thread_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch complete discussion thread with all replies, reactions, and view incrementation"""
    check_q = select(ForumThread.course_id).where(ForumThread.id == thread_id)
    res = await db.execute(check_q)
    course_id = res.scalar_one_or_none()
    if course_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Discussion thread not found"
        )

    await verify_course_forum_access(course_id, current_user, db)

    # Increment view count and commit prior to loading ORM objects
    await db.execute(
        update(ForumThread).where(ForumThread.id == thread_id).values(view_count=ForumThread.view_count + 1)
    )
    await db.commit()

    # Load thread freshly with eager relationships
    q = (
        select(ForumThread)
        .where(ForumThread.id == thread_id)
        .options(
            selectinload(ForumThread.category),
            selectinload(ForumThread.author),
            selectinload(ForumThread.posts).selectinload(ForumPost.author),
            selectinload(ForumThread.posts).selectinload(ForumPost.reactions),
        )
    )
    res = await db.execute(q)
    thread = res.scalar_one()

    posts_out = []
    for p in sorted(thread.posts, key=lambda x: (not x.is_solution, x.created_at)):
        has_reacted = any(r.user_id == current_user.id for r in p.reactions)
        p_author = p.author.full_name if p.author else "Unknown"
        posts_out.append(
            ForumPostOut(
                id=p.id,
                thread_id=p.thread_id,
                author_id=p.author_id,
                author_name=p_author,
                parent_post_id=p.parent_post_id,
                content=p.content,
                is_endorsed_by_instructor=p.is_endorsed_by_instructor,
                is_solution=p.is_solution,
                upvotes=p.upvotes or 0,
                user_has_reacted=has_reacted,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
        )

    author_name = thread.author.full_name if thread.author else "Unknown"
    return ForumThreadDetailOut(
        id=thread.id,
        course_id=thread.course_id,
        category_id=thread.category_id,
        category_title=thread.category.title if thread.category else None,
        author_id=thread.author_id,
        author_name=author_name,
        title=thread.title,
        content=thread.content,
        is_pinned=thread.is_pinned,
        is_locked=thread.is_locked,
        view_count=thread.view_count or 0,
        reply_count=thread.reply_count or 0,
        posts=posts_out,
        created_at=thread.created_at,
        updated_at=thread.updated_at,
    )


@router.patch("/api/forums/threads/{thread_id}", response_model=ForumThreadSummaryOut)
async def update_forum_thread(
    thread_id: int,
    payload: ForumThreadUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Modify thread content (author) or toggle pin/lock status (instructor/admin)"""
    q = (
        select(ForumThread)
        .where(ForumThread.id == thread_id)
        .options(
            selectinload(ForumThread.category),
            selectinload(ForumThread.author),
        )
    )
    res = await db.execute(q)
    thread = res.scalar_one_or_none()
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Discussion thread not found"
        )

    course, is_instructor_or_admin = await verify_course_forum_access(thread.course_id, current_user, db)
    is_author = thread.author_id == current_user.id

    if not (is_author or is_instructor_or_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to edit this discussion thread"
        )

    if payload.is_pinned is not None or payload.is_locked is not None:
        if not is_instructor_or_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only instructors and administrators can pin or lock threads."
            )
        if payload.is_pinned is not None:
            thread.is_pinned = payload.is_pinned
        if payload.is_locked is not None:
            thread.is_locked = payload.is_locked

    if payload.title is not None:
        thread.title = payload.title.strip()
    if payload.content is not None:
        thread.content = sanitize_rich_content(payload.content)

    if payload.category_id is not None:
        cat_check = await db.execute(
            select(CourseForumCategory).where(
                CourseForumCategory.id == payload.category_id,
                CourseForumCategory.course_id == thread.course_id,
            )
        )
        if not cat_check.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target forum category not found in this course"
            )
        thread.category_id = payload.category_id

    await db.commit()

    reload_q = (
        select(ForumThread)
        .where(ForumThread.id == thread_id)
        .options(
            selectinload(ForumThread.category),
            selectinload(ForumThread.author),
            selectinload(ForumThread.posts),
        )
    )
    res = await db.execute(reload_q)
    fresh_thread = res.scalar_one()

    has_sol = any(p.is_solution for p in fresh_thread.posts)
    author_name = fresh_thread.author.full_name if fresh_thread.author else "Unknown"

    return ForumThreadSummaryOut(
        id=fresh_thread.id,
        course_id=fresh_thread.course_id,
        category_id=fresh_thread.category_id,
        category_title=fresh_thread.category.title if fresh_thread.category else None,
        author_id=fresh_thread.author_id,
        author_name=author_name,
        title=fresh_thread.title,
        is_pinned=fresh_thread.is_pinned,
        is_locked=fresh_thread.is_locked,
        view_count=fresh_thread.view_count or 0,
        reply_count=fresh_thread.reply_count or 0,
        has_solution=has_sol,
        created_at=fresh_thread.created_at,
        updated_at=fresh_thread.updated_at,
    )


@router.delete("/api/forums/threads/{thread_id}", status_code=204)
async def delete_forum_thread(
    thread_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a discussion thread (Thread author or Course Instructor/Admin only)"""
    res = await db.execute(select(ForumThread).where(ForumThread.id == thread_id))
    thread = res.scalar_one_or_none()
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Discussion thread not found"
        )

    course, is_instructor_or_admin = await verify_course_forum_access(thread.course_id, current_user, db)
    if not (thread.author_id == current_user.id or is_instructor_or_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this discussion thread"
        )

    await db.delete(thread)
    await db.commit()


# ─── Post (Reply) Endpoints ───────────────────────────────────────────────────

@router.post("/api/forums/threads/{thread_id}/posts", response_model=ForumPostOut, status_code=201)
async def create_forum_post(
    thread_id: int,
    payload: ForumPostCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Post a reply to a discussion thread, supporting nested threaded comments"""
    q = (
        select(ForumThread)
        .where(ForumThread.id == thread_id)
        .options(selectinload(ForumThread.category))
    )
    res = await db.execute(q)
    thread = res.scalar_one_or_none()
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Discussion thread not found"
        )

    course, is_instructor_or_admin = await verify_course_forum_access(thread.course_id, current_user, db)

    if (thread.is_locked or (thread.category and thread.category.is_locked)) and not is_instructor_or_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This discussion thread is locked. No new replies can be submitted."
        )

    if payload.parent_post_id:
        parent_res = await db.execute(
            select(ForumPost).where(
                ForumPost.id == payload.parent_post_id,
                ForumPost.thread_id == thread_id,
            )
        )
        if not parent_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent reply not found in this thread"
            )

    sanitized_content = sanitize_rich_content(payload.content)

    post = ForumPost(
        thread_id=thread_id,
        author_id=current_user.id,
        parent_post_id=payload.parent_post_id,
        content=sanitized_content,
        is_endorsed_by_instructor=False,
        is_solution=False,
        upvotes=0,
    )
    db.add(post)

    thread.reply_count = (thread.reply_count or 0) + 1
    thread.updated_at = func.now()

    await db.commit()

    return await fetch_post_out(post.id, current_user.id, db)


@router.patch("/api/forums/posts/{post_id}", response_model=ForumPostOut)
async def update_forum_post(
    post_id: int,
    payload: ForumPostUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Edit reply content (Author only)"""
    q = (
        select(ForumPost)
        .where(ForumPost.id == post_id)
        .options(selectinload(ForumPost.thread))
    )
    res = await db.execute(q)
    post = res.scalar_one_or_none()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reply post not found"
        )

    await verify_course_forum_access(post.thread.course_id, current_user, db)

    if post.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to edit this reply"
        )

    post.content = sanitize_rich_content(payload.content)
    await db.commit()

    return await fetch_post_out(post.id, current_user.id, db)


@router.delete("/api/forums/posts/{post_id}", status_code=204)
async def delete_forum_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a reply (Author or Instructor/Admin)"""
    q = select(ForumPost).where(ForumPost.id == post_id).options(selectinload(ForumPost.thread))
    res = await db.execute(q)
    post = res.scalar_one_or_none()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reply post not found"
        )

    course, is_instructor_or_admin = await verify_course_forum_access(post.thread.course_id, current_user, db)
    if not (post.author_id == current_user.id or is_instructor_or_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this reply"
        )

    thread = post.thread
    if thread:
        thread.reply_count = max(0, (thread.reply_count or 1) - 1)

    await db.delete(post)
    await db.commit()


@router.post("/api/forums/posts/{post_id}/endorse", response_model=ForumPostOut)
async def endorse_forum_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Instructor endorsement toggle to highlight authoritative guidance"""
    q = (
        select(ForumPost)
        .where(ForumPost.id == post_id)
        .options(selectinload(ForumPost.thread))
    )
    res = await db.execute(q)
    post = res.scalar_one_or_none()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reply post not found"
        )

    course, is_instructor_or_admin = await verify_course_forum_access(post.thread.course_id, current_user, db)
    if not is_instructor_or_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only course instructors and administrators can endorse answers."
        )

    post.is_endorsed_by_instructor = not post.is_endorsed_by_instructor
    await db.commit()

    return await fetch_post_out(post.id, current_user.id, db)


@router.post("/api/forums/posts/{post_id}/solution", response_model=ForumPostOut)
async def toggle_post_solution(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark or unmark a post as the accepted solution (Thread author or Instructor/Admin)"""
    q = (
        select(ForumPost)
        .where(ForumPost.id == post_id)
        .options(selectinload(ForumPost.thread))
    )
    res = await db.execute(q)
    post = res.scalar_one_or_none()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reply post not found"
        )

    course, is_instructor_or_admin = await verify_course_forum_access(post.thread.course_id, current_user, db)
    is_thread_author = post.thread.author_id == current_user.id

    if not (is_thread_author or is_instructor_or_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the thread author or course instructors can mark an accepted solution."
        )

    if not post.is_solution:
        # Clear any existing solutions on this thread first
        other_posts = await db.execute(
            select(ForumPost).where(
                ForumPost.thread_id == post.thread_id,
                ForumPost.is_solution == True,
            )
        )
        for op in other_posts.scalars().all():
            op.is_solution = False
        post.is_solution = True
    else:
        post.is_solution = False

    await db.commit()

    return await fetch_post_out(post.id, current_user.id, db)


@router.post("/api/forums/posts/{post_id}/react", response_model=ForumPostOut)
async def react_to_forum_post(
    post_id: int,
    reaction_type: str = Query("like", description="Type of reaction (e.g. like, upvote)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Toggle a reaction or upvote on a forum post"""
    q = (
        select(ForumPost)
        .where(ForumPost.id == post_id)
        .options(selectinload(ForumPost.thread))
    )
    res = await db.execute(q)
    post = res.scalar_one_or_none()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reply post not found"
        )

    await verify_course_forum_access(post.thread.course_id, current_user, db)

    # Check existing reaction
    react_q = select(ForumPostReaction).where(
        ForumPostReaction.post_id == post_id,
        ForumPostReaction.user_id == current_user.id,
        ForumPostReaction.reaction_type == reaction_type,
    )
    react_res = await db.execute(react_q)
    existing_reaction = react_res.scalar_one_or_none()

    if existing_reaction:
        await db.delete(existing_reaction)
        post.upvotes = max(0, (post.upvotes or 1) - 1)
    else:
        new_reaction = ForumPostReaction(
            post_id=post_id,
            user_id=current_user.id,
            reaction_type=reaction_type,
        )
        db.add(new_reaction)
        post.upvotes = (post.upvotes or 0) + 1

    await db.commit()

    return await fetch_post_out(post.id, current_user.id, db)
