"""NSBM EduSphere — Alumni, Library, Sports, News, Admin, WebSocket Routers"""
# ─── ALUMNI ROUTER ────────────────────────────────────────────────────────────
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from backend.database import get_db
from backend.models import (
    User, Alumni, AlumniExperience, Mentorship,
    Book, BorrowRecord, BookReservation, BookStatus, BorrowStatus,
    Club, ClubMembership, ClubEvent, EventRegistration, SportsResult,
    News, NewsComment, NewsCategory,
    Student, Lecturer, Course, Enrollment, Notification
)
from backend.schemas import (
    AlumniExperienceCreate, NewsCreate, NewsCommentCreate, ClubEventCreate
)
from backend.utils.security import require_roles, get_current_user
from datetime import datetime, timedelta

# ── Alumni ─────────────────────────────────────────────────────────────────────
alumni_router = APIRouter(prefix="/api/alumni", tags=["Alumni"])

@alumni_router.get("/dashboard")
async def alumni_dashboard(
    current_user: User = Depends(require_roles("alumni", "admin")),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Alumni).where(Alumni.user_id == current_user.id)
        .options(selectinload(Alumni.user))
    )
    alumni = result.scalar_one_or_none()
    if not alumni:
        raise HTTPException(404, "Alumni profile not found")

    exp_q = await db.execute(
        select(func.count(AlumniExperience.id)).where(AlumniExperience.alumni_id == alumni.id)
    )
    total_alumni_q = await db.execute(select(func.count(Alumni.id)))
    mentorships_q = await db.execute(
        select(func.count(Mentorship.id)).where(Mentorship.mentor_id == alumni.id)
    )
    featured_exp_q = await db.execute(
        select(AlumniExperience).where(AlumniExperience.is_published == True)
        .order_by(AlumniExperience.likes.desc()).limit(5)
        .options(selectinload(AlumniExperience.alumni).selectinload(Alumni.user))
    )
    return {
        "alumni_id": alumni.alumni_id,
        "full_name": current_user.full_name,
        "graduation_year": alumni.graduation_year,
        "degree": alumni.degree,
        "current_position": alumni.current_position,
        "current_company": alumni.current_company,
        "industry": alumni.industry,
        "willing_to_mentor": alumni.willing_to_mentor,
        "location": alumni.location,
        "my_experiences": exp_q.scalar() or 0,
        "total_alumni_network": total_alumni_q.scalar() or 0,
        "active_mentorships": mentorships_q.scalar() or 0,
        "featured_stories": [
            {
                "id": e.id,
                "title": e.title,
                "author": e.alumni.user.full_name,
                "category": e.category,
                "likes": e.likes,
                "created_at": e.created_at.isoformat()
            }
            for e in featured_exp_q.scalars().all()
        ]
    }

@alumni_router.get("/network")
async def get_alumni_network(
    page: int = 1, size: int = 12,
    industry: Optional[str] = None,
    graduation_year: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Alumni).options(selectinload(Alumni.user))
    if industry:
        query = query.where(Alumni.industry == industry)
    if graduation_year:
        query = query.where(Alumni.graduation_year == graduation_year)
    query = query.offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    alumni = result.scalars().all()
    count = await db.execute(select(func.count(Alumni.id)))
    return {
        "items": [
            {
                "id": a.id,
                "alumni_id": a.alumni_id,
                "full_name": a.user.full_name,
                "graduation_year": a.graduation_year,
                "degree": a.degree,
                "current_position": a.current_position,
                "current_company": a.current_company,
                "industry": a.industry,
                "location": a.location,
                "willing_to_mentor": a.willing_to_mentor,
                "linkedin_url": a.linkedin_url
            }
            for a in alumni
        ],
        "total": count.scalar(),
        "page": page,
        "size": size
    }

@alumni_router.get("/experiences")
async def get_experiences(
    page: int = 1, size: int = 10,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(AlumniExperience).where(AlumniExperience.is_published == True)
    if category:
        query = query.where(AlumniExperience.category == category)
    query = query.options(selectinload(AlumniExperience.alumni).selectinload(Alumni.user))
    query = query.order_by(AlumniExperience.likes.desc())
    query = query.offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    items = result.scalars().all()
    return [
        {
            "id": e.id,
            "title": e.title,
            "content": e.content,
            "category": e.category,
            "tags": e.tags,
            "likes": e.likes,
            "author": e.alumni.user.full_name,
            "graduation_year": e.alumni.graduation_year,
            "company": e.alumni.current_company,
            "created_at": e.created_at.isoformat()
        }
        for e in items
    ]

@alumni_router.post("/experiences")
async def create_experience(
    payload: AlumniExperienceCreate,
    current_user: User = Depends(require_roles("alumni", "admin")),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Alumni).where(Alumni.user_id == current_user.id))
    alumni = result.scalar_one_or_none()
    if not alumni:
        raise HTTPException(404, "Alumni profile not found")
    exp = AlumniExperience(alumni_id=alumni.id, **payload.dict())
    db.add(exp)
    await db.commit()
    return {"message": "Experience shared successfully", "id": exp.id}

@alumni_router.post("/experiences/{exp_id}/like")
async def like_experience(exp_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(AlumniExperience).where(AlumniExperience.id == exp_id))
    exp = result.scalar_one_or_none()
    if not exp:
        raise HTTPException(404, "Experience not found")
    exp.likes += 1
    await db.commit()
    return {"likes": exp.likes}

@alumni_router.get("/mentors")
async def get_mentors(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Alumni).where(Alumni.willing_to_mentor == True)
        .options(selectinload(Alumni.user))
    )
    mentors = result.scalars().all()
    return [
        {
            "id": a.id,
            "full_name": a.user.full_name,
            "graduation_year": a.graduation_year,
            "industry": a.industry,
            "position": a.current_position,
            "company": a.current_company,
            "bio": a.bio
        }
        for a in mentors
    ]


# ── Library ────────────────────────────────────────────────────────────────────
library_router = APIRouter(prefix="/api/library", tags=["Library"])

@library_router.get("/catalog")
async def get_catalog(
    search: Optional[str] = None,
    category: Optional[str] = None,
    available_only: bool = False,
    page: int = 1, size: int = 12,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Book)
    if search:
        query = query.where(
            or_(
                Book.title.ilike(f"%{search}%"),
                Book.author.ilike(f"%{search}%"),
                Book.isbn.ilike(f"%{search}%"),
                Book.subject.ilike(f"%{search}%")
            )
        )
    if category:
        query = query.where(Book.category == category)
    if available_only:
        query = query.where(Book.available_copies > 0)

    count_q = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_q.scalar()
    result = await db.execute(query.offset((page - 1) * size).limit(size))
    books = result.scalars().all()
    return {
        "items": [
            {
                "id": b.id,
                "isbn": b.isbn,
                "title": b.title,
                "author": b.author,
                "publisher": b.publisher,
                "year": b.year,
                "category": b.category,
                "subject": b.subject,
                "description": b.description,
                "cover_url": b.cover_url,
                "total_copies": b.total_copies,
                "available_copies": b.available_copies,
                "status": b.status.value,
                "is_ebook": b.is_ebook,
                "location": b.location
            }
            for b in books
        ],
        "total": total, "page": page, "size": size,
        "pages": (total + size - 1) // size
    }

@library_router.get("/categories")
async def get_categories(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Book.category, func.count(Book.id)).group_by(Book.category))
    return [{"category": r[0], "count": r[1]} for r in result.all()]

@library_router.post("/borrow/{book_id}")
async def borrow_book(
    book_id: int,
    current_user: User = Depends(require_roles("student", "admin")),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(404, "Book not found")
    if book.available_copies < 1:
        raise HTTPException(400, "No copies available. Please reserve.")

    stu_result = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = stu_result.scalar_one_or_none()
    if not student:
        raise HTTPException(404, "Student profile not found")

    # Check active borrows limit
    active_q = await db.execute(
        select(func.count(BorrowRecord.id)).where(
            and_(BorrowRecord.student_id == student.id, BorrowRecord.status == "active")
        )
    )
    if (active_q.scalar() or 0) >= 5:
        raise HTTPException(400, "Maximum borrow limit reached (5 books)")

    due = datetime.utcnow() + timedelta(days=14)
    borrow = BorrowRecord(
        book_id=book.id, student_id=student.id,
        due_date=due, status=BorrowStatus.ACTIVE
    )
    book.available_copies -= 1
    if book.available_copies == 0:
        book.status = BookStatus.BORROWED
    db.add(borrow)
    await db.commit()
    return {"message": f"Book borrowed successfully. Due: {due.strftime('%Y-%m-%d')}", "due_date": due.isoformat()}

@library_router.post("/return/{borrow_id}")
async def return_book(
    borrow_id: int,
    current_user: User = Depends(require_roles("student", "admin", "librarian")),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(BorrowRecord).where(BorrowRecord.id == borrow_id)
        .options(selectinload(BorrowRecord.book))
    )
    borrow = result.scalar_one_or_none()
    if not borrow:
        raise HTTPException(404, "Borrow record not found")

    now = datetime.utcnow()
    borrow.returned_at = now
    borrow.status = BorrowStatus.RETURNED

    # Calculate fine if overdue
    if now > borrow.due_date:
        days_overdue = (now - borrow.due_date).days
        borrow.fine_amount = days_overdue * 5.0  # LKR 5 per day

    borrow.book.available_copies += 1
    borrow.book.status = BookStatus.AVAILABLE
    await db.commit()
    return {"message": "Book returned", "fine": borrow.fine_amount}

@library_router.get("/my-borrows")
async def my_borrows(
    current_user: User = Depends(require_roles("student", "admin")),
    db: AsyncSession = Depends(get_db)
):
    stu_result = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = stu_result.scalar_one_or_none()
    if not student:
        raise HTTPException(404, "Student not found")

    borrows_q = await db.execute(
        select(BorrowRecord).where(BorrowRecord.student_id == student.id)
        .options(selectinload(BorrowRecord.book))
        .order_by(BorrowRecord.borrowed_at.desc())
    )
    borrows = borrows_q.scalars().all()
    now = datetime.utcnow()
    return [
        {
            "id": b.id,
            "book": b.book.title,
            "author": b.book.author,
            "isbn": b.book.isbn,
            "borrowed_at": b.borrowed_at.isoformat(),
            "due_date": b.due_date.isoformat(),
            "returned_at": b.returned_at.isoformat() if b.returned_at else None,
            "status": b.status.value,
            "fine": b.fine_amount,
            "days_remaining": max(0, (b.due_date - now).days) if b.status.value == "active" else 0
        }
        for b in borrows
    ]


# ── Sports & Clubs ─────────────────────────────────────────────────────────────
sports_router = APIRouter(prefix="/api/sports", tags=["Sports & Clubs"])

@sports_router.get("/clubs")
async def get_clubs(
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Club).where(Club.is_active == True)
    if category:
        query = query.where(Club.category == category)
    query = query.options(selectinload(Club.memberships))
    result = await db.execute(query)
    clubs = result.scalars().all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "description": c.description,
            "category": c.category.value,
            "logo_url": c.logo_url,
            "cover_url": c.cover_url,
            "president_name": c.president_name,
            "achievements": c.achievements,
            "meeting_schedule": c.meeting_schedule,
            "member_count": len([m for m in c.memberships if m.is_active]),
            "max_members": c.max_members
        }
        for c in clubs
    ]

@sports_router.post("/clubs/{club_id}/join")
async def join_club(
    club_id: int,
    current_user: User = Depends(require_roles("student")),
    db: AsyncSession = Depends(get_db)
):
    stu_result = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = stu_result.scalar_one_or_none()
    if not student:
        raise HTTPException(404, "Student not found")

    existing = await db.execute(
        select(ClubMembership).where(
            and_(ClubMembership.club_id == club_id, ClubMembership.student_id == student.id)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Already a member")

    membership = ClubMembership(club_id=club_id, student_id=student.id, role="member")
    db.add(membership)
    await db.commit()
    return {"message": "Joined club successfully"}

@sports_router.get("/events")
async def get_events(
    upcoming_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(ClubEvent).options(selectinload(ClubEvent.club))
    if upcoming_only:
        query = query.where(ClubEvent.event_date > datetime.utcnow())
    query = query.order_by(ClubEvent.event_date.asc()).limit(20)
    result = await db.execute(query)
    events = result.scalars().all()
    return [
        {
            "id": e.id,
            "title": e.title,
            "description": e.description,
            "club": e.club.name,
            "club_category": e.club.category.value,
            "event_date": e.event_date.isoformat(),
            "location": e.location,
            "max_participants": e.max_participants,
            "registration_required": e.registration_required,
            "image_url": e.image_url
        }
        for e in events
    ]

@sports_router.post("/events/{event_id}/register")
async def register_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing = await db.execute(
        select(EventRegistration).where(
            and_(EventRegistration.event_id == event_id, EventRegistration.user_id == current_user.id)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Already registered")
    reg = EventRegistration(event_id=event_id, user_id=current_user.id)
    db.add(reg)
    await db.commit()
    return {"message": "Registered for event"}

@sports_router.get("/results")
async def get_sports_results(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(SportsResult).order_by(SportsResult.event_date.desc()).limit(20)
    )
    results = result.scalars().all()
    return [
        {
            "id": r.id,
            "event": r.event_name,
            "opponent": r.opponent,
            "result": r.result,
            "score": r.score,
            "date": r.event_date.isoformat(),
            "location": r.location
        }
        for r in results
    ]


# ── News ───────────────────────────────────────────────────────────────────────
news_router = APIRouter(prefix="/api/news", tags=["News"])

@news_router.get("")
async def get_news(
    category: Optional[str] = None,
    featured: Optional[bool] = None,
    search: Optional[str] = None,
    page: int = 1, size: int = 9,
    db: AsyncSession = Depends(get_db)
):
    query = select(News).where(News.is_published == True)
    if category:
        query = query.where(News.category == category)
    if featured is not None:
        query = query.where(News.is_featured == featured)
    if search:
        query = query.where(
            or_(News.title.ilike(f"%{search}%"), News.summary.ilike(f"%{search}%"))
        )
    query = query.options(selectinload(News.author))
    query = query.order_by(News.published_at.desc())

    count_q = await db.execute(select(func.count()).select_from(
        select(News).where(News.is_published == True).subquery()
    ))
    total = count_q.scalar()
    result = await db.execute(query.offset((page - 1) * size).limit(size))
    articles = result.scalars().all()
    return {
        "items": [
            {
                "id": n.id,
                "title": n.title,
                "slug": n.slug,
                "summary": n.summary,
                "category": n.category.value,
                "author": n.author.full_name,
                "cover_image_url": n.cover_image_url,
                "tags": n.tags,
                "views": n.views,
                "is_featured": n.is_featured,
                "published_at": n.published_at.isoformat()
            }
            for n in articles
        ],
        "total": total, "page": page, "size": size,
        "pages": (total + size - 1) // size
    }

@news_router.get("/{news_id}")
async def get_news_article(
    news_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(News).where(News.id == news_id)
        .options(
            selectinload(News.author),
            selectinload(News.comments).selectinload(NewsComment.user)
        )
    )
    news = result.scalar_one_or_none()
    if not news:
        raise HTTPException(404, "Article not found")
    news.views += 1
    await db.commit()
    return {
        "id": news.id,
        "title": news.title,
        "content": news.content,
        "summary": news.summary,
        "category": news.category.value,
        "author": news.author.full_name,
        "cover_image_url": news.cover_image_url,
        "tags": news.tags,
        "views": news.views,
        "is_featured": news.is_featured,
        "published_at": news.published_at.isoformat(),
        "comments": [
            {
                "id": c.id,
                "user": c.user.full_name,
                "content": c.content,
                "created_at": c.created_at.isoformat()
            }
            for c in news.comments
        ]
    }

@news_router.post("/{news_id}/comments")
async def add_comment(
    news_id: int,
    payload: NewsCommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    comment = NewsComment(news_id=news_id, user_id=current_user.id, content=payload.content)
    db.add(comment)
    await db.commit()
    return {"message": "Comment added"}

@news_router.post("")
async def create_news(
    payload: NewsCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "lecturer"))
):
    import re
    slug = re.sub(r'[^a-z0-9]+', '-', payload.title.lower()).strip('-')
    slug = f"{slug}-{int(datetime.utcnow().timestamp())}"
    news = News(
        title=payload.title,
        slug=slug,
        content=payload.content,
        summary=payload.summary,
        category=payload.category,
        author_id=current_user.id,
        tags=payload.tags,
        is_featured=payload.is_featured,
        is_published=True
    )
    db.add(news)
    await db.commit()
    return {"message": "Article published", "id": news.id}


# ── Admin ──────────────────────────────────────────────────────────────────────
admin_router = APIRouter(prefix="/api/admin", tags=["Admin"])

@admin_router.get("/dashboard")
async def admin_dashboard(
    current_user: User = Depends(require_roles("admin")),
    db: AsyncSession = Depends(get_db)
):
    stats = {}
    for model, key in [
        (Student, "total_students"), (Lecturer, "total_lecturers"),
        (Alumni, "total_alumni"), (Course, "total_courses"),
        (Book, "total_books"), (Club, "total_clubs"), (News, "total_news")
    ]:
        q = await db.execute(select(func.count(model.id)))
        stats[key] = q.scalar() or 0

    borrow_q = await db.execute(
        select(func.count(BorrowRecord.id)).where(BorrowRecord.status == "active")
    )
    stats["active_borrows"] = borrow_q.scalar() or 0

    recent_users_q = await db.execute(
        select(User).order_by(User.created_at.desc()).limit(8)
    )
    recent_users = recent_users_q.scalars().all()
    stats["recent_registrations"] = [
        {"id": u.id, "name": u.full_name, "role": u.role, "email": u.email,
         "created_at": u.created_at.isoformat()}
        for u in recent_users
    ]
    return stats

@admin_router.get("/users")
async def list_users(
    role: Optional[str] = None,
    page: int = 1, size: int = 20,
    current_user: User = Depends(require_roles("admin")),
    db: AsyncSession = Depends(get_db)
):
    query = select(User)
    if role:
        query = query.where(User.role == role)
    count_q = await db.execute(select(func.count(User.id)))
    total = count_q.scalar()
    result = await db.execute(query.offset((page - 1) * size).limit(size))
    users = result.scalars().all()
    return {
        "items": [
            {"id": u.id, "full_name": u.full_name, "email": u.email,
             "username": u.username, "role": u.role, "is_active": u.is_active,
             "created_at": u.created_at.isoformat()}
            for u in users
        ],
        "total": total, "page": page, "size": size
    }

@admin_router.patch("/users/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: int,
    current_user: User = Depends(require_roles("admin")),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
    user.is_active = not user.is_active
    await db.commit()
    return {"message": f"User {'activated' if user.is_active else 'deactivated'}", "is_active": user.is_active}


# ── WebSocket ──────────────────────────────────────────────────────────────────
from fastapi import WebSocket, WebSocketDisconnect
import json

ws_router = APIRouter(tags=["WebSocket"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)

    async def send_personal(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            for ws in self.active_connections[user_id]:
                try:
                    await ws.send_json(message)
                except:
                    pass

    async def broadcast(self, message: dict):
        for user_id, connections in self.active_connections.items():
            for ws in connections:
                try:
                    await ws.send_json(message)
                except:
                    pass

manager = ConnectionManager()

@ws_router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(websocket, user_id)
    try:
        await websocket.send_json({"type": "connected", "message": "Connected to NSBM EduSphere"})
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
