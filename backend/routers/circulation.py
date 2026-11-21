"""backend/routers/circulation.py
Enterprise Circulation and Borrowing Workflows Router
Provides end-to-end management of library checkouts, priority reservations,
loan renewals, returns, progressive overdue fine computations, and fine waivers.
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
    Book,
    BookStatus,
    BorrowRecord,
    BorrowStatus,
    BookReservation,
    LibraryFineRecord,
)
from backend.schemas import (
    BorrowRecordOut,
    BookReservationOut,
    LibraryFineRecordOut,
    CirculationCheckoutRequest,
    CirculationStatsOut,
)
from backend.utils.security import get_current_user, require_roles

router = APIRouter(prefix="/api/circulation", tags=["Circulation & Borrowing Workflows"])

DAILY_OVERDUE_FINE_RATE = 50.0  # LKR per day
MAX_BORROW_LIMIT = 5
MAX_RENEWALS_ALLOWED = 2
UNPAID_FINE_BLOCK_THRESHOLD = 500.0


def serialize_borrow(record: BorrowRecord) -> BorrowRecordOut:
    s_name = record.student.user.full_name if (record.student and record.student.user) else None
    return BorrowRecordOut(
        id=record.id,
        book_id=record.book_id,
        book_title=record.book.title if record.book else "Unknown Book",
        book_author=record.book.author if record.book else "Unknown Author",
        student_id=record.student_id,
        student_name=s_name,
        borrowed_at=record.borrowed_at,
        due_date=record.due_date,
        returned_at=record.returned_at,
        renewals_count=record.renewals_count,
        renewed_at=record.renewed_at,
        status=record.status.value if hasattr(record.status, "value") else str(record.status),
        fine_amount=record.fine_amount,
        fine_paid=record.fine_paid,
        notes=record.notes,
    )


# ─── Circulation Loans & Checkout ────────────────────────────────────────────

@router.get("/loans", response_model=List[BorrowRecordOut])
async def list_circulation_loans(
    student_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None),
    overdue_only: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve book borrowing records with automatic overdue status checking."""
    # Enforce student access boundary
    stu_res = await db.execute(select(Student).where(Student.user_id == current_user.id))
    current_student = stu_res.scalars().first()

    query = (
        select(BorrowRecord)
        .options(
            selectinload(BorrowRecord.book),
            selectinload(BorrowRecord.student).selectinload(Student.user),
        )
        .order_by(desc(BorrowRecord.borrowed_at))
        .offset(offset)
        .limit(limit)
    )

    filters = []
    if current_user.role not in ["admin", "librarian"]:
        if not current_student:
            return []
        filters.append(BorrowRecord.student_id == current_student.id)
    else:
        if student_id:
            filters.append(BorrowRecord.student_id == student_id)

    if status_filter and status_filter != "all":
        filters.append(BorrowRecord.status == status_filter)

    now = datetime.utcnow()
    if overdue_only:
        filters.append(
            and_(
                BorrowRecord.status == BorrowStatus.ACTIVE,
                BorrowRecord.due_date < now
            )
        )

    if filters:
        query = query.where(and_(*filters))

    res = await db.execute(query)
    records = res.scalars().all()

    # Update any active loans past due date to overdue
    for r in records:
        if r.status == BorrowStatus.ACTIVE and r.due_date < now:
            r.status = BorrowStatus.OVERDUE
            overdue_days = max(1, (now.date() - r.due_date.date()).days)
            r.fine_amount = round(overdue_days * DAILY_OVERDUE_FINE_RATE, 2)
    await db.commit()

    return [serialize_borrow(r) for r in records]


@router.post("/checkout", response_model=BorrowRecordOut, status_code=status.HTTP_201_CREATED)
async def checkout_book(
    payload: CirculationCheckoutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Checkout a physical book copy with limit, fine, and reservation checking."""
    # Identify target student
    target_student_id = payload.student_id
    if current_user.role not in ["admin", "librarian"]:
        stu_res = await db.execute(select(Student).where(Student.user_id == current_user.id))
        curr_stu = stu_res.scalars().first()
        if not curr_stu:
            raise HTTPException(status_code=403, detail="Student profile not found.")
        target_student_id = curr_stu.id
    else:
        if not target_student_id:
            raise HTTPException(status_code=400, detail="Staff checkout requires target student_id.")

    # Check student active borrows limit
    active_cnt_res = await db.execute(
        select(func.count(BorrowRecord.id)).where(
            and_(
                BorrowRecord.student_id == target_student_id,
                BorrowRecord.status.in_([BorrowStatus.ACTIVE, BorrowStatus.OVERDUE]),
            )
        )
    )
    if (active_cnt_res.scalar() or 0) >= MAX_BORROW_LIMIT:
        raise HTTPException(
            status_code=400,
            detail=f"Borrowing limit exceeded. Maximum {MAX_BORROW_LIMIT} active books allowed."
        )

    # Check outstanding unpaid library fines
    fines_res = await db.execute(
        select(func.sum(LibraryFineRecord.amount)).where(
            and_(
                LibraryFineRecord.student_id == target_student_id,
                LibraryFineRecord.status == "unpaid",
            )
        )
    )
    unpaid_total = fines_res.scalar() or 0.0
    if unpaid_total >= UNPAID_FINE_BLOCK_THRESHOLD:
        raise HTTPException(
            status_code=403,
            detail=f"Borrowing suspended: Unpaid library fines (LKR {unpaid_total:.2f}) exceed policy threshold (LKR {UNPAID_FINE_BLOCK_THRESHOLD:.2f})."
        )

    # Find and check book
    book_res = await db.execute(select(Book).where(Book.id == payload.book_id))
    book = book_res.scalars().first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found.")

    if book.available_copies <= 0:
        raise HTTPException(
            status_code=400,
            detail="No copies currently available on shelves. Please place a reservation."
        )

    # Calculate due date (14 days for standard loan)
    borrow_date = datetime.utcnow()
    due_date = borrow_date + timedelta(days=14)

    record = BorrowRecord(
        book_id=book.id,
        student_id=target_student_id,
        borrowed_at=borrow_date,
        due_date=due_date,
        status=BorrowStatus.ACTIVE,
        renewals_count=0,
        fine_amount=0.0,
        fine_paid=False,
    )
    book.available_copies -= 1
    if book.available_copies == 0:
        book.status = BookStatus.BORROWED

    db.add(record)
    await db.commit()

    # Reload with relations
    reload_res = await db.execute(
        select(BorrowRecord)
        .options(
            selectinload(BorrowRecord.book),
            selectinload(BorrowRecord.student).selectinload(Student.user),
        )
        .where(BorrowRecord.id == record.id)
    )
    loaded = reload_res.scalars().first()
    return serialize_borrow(loaded)


@router.post("/renew/{borrow_id}", response_model=BorrowRecordOut)
async def renew_circulation_loan(
    borrow_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Renew an active borrowing record for an additional 14 days."""
    res = await db.execute(
        select(BorrowRecord)
        .options(
            selectinload(BorrowRecord.book),
            selectinload(BorrowRecord.student).selectinload(Student.user),
        )
        .where(BorrowRecord.id == borrow_id)
    )
    record = res.scalars().first()
    if not record:
        raise HTTPException(status_code=404, detail="Borrow record not found.")

    # Authorization
    if current_user.role not in ["admin", "librarian"]:
        stu_res = await db.execute(select(Student).where(Student.user_id == current_user.id))
        curr_stu = stu_res.scalars().first()
        if not curr_stu or record.student_id != curr_stu.id:
            raise HTTPException(status_code=403, detail="Unauthorized access to this loan.")

    if record.status != BorrowStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Only active loans can be renewed.")

    if record.renewals_count >= MAX_RENEWALS_ALLOWED:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum renewal limit reached ({MAX_RENEWALS_ALLOWED} times allowed)."
        )

    # Check if another student has reserved this book
    res_queue = await db.execute(
        select(BookReservation).where(
            and_(
                BookReservation.book_id == record.book_id,
                BookReservation.status == "active",
                BookReservation.student_id != record.student_id,
            )
        )
    )
    if res_queue.scalars().first():
        raise HTTPException(
            status_code=400,
            detail="Cannot renew: Another student is in the reservation queue for this book."
        )

    record.due_date = record.due_date + timedelta(days=14)
    record.renewals_count += 1
    record.renewed_at = datetime.utcnow()
    await db.commit()
    await db.refresh(record)

    return serialize_borrow(record)


@router.post("/return/{borrow_id}", response_model=BorrowRecordOut)
async def return_circulation_loan(
    borrow_id: int,
    notes: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("student", "admin", "librarian")),
):
    """Process return of borrowed book, calculating any progressive overdue fines."""
    res = await db.execute(
        select(BorrowRecord)
        .options(
            selectinload(BorrowRecord.book),
            selectinload(BorrowRecord.student).selectinload(Student.user),
        )
        .where(BorrowRecord.id == borrow_id)
    )
    record = res.scalars().first()
    if not record:
        raise HTTPException(status_code=404, detail="Borrow record not found.")

    if record.returned_at is not None or record.status == BorrowStatus.RETURNED:
        raise HTTPException(status_code=400, detail="This book has already been returned.")

    now = datetime.utcnow()
    record.returned_at = now
    record.status = BorrowStatus.RETURNED
    if notes:
        record.notes = notes

    # Restock book inventory
    if record.book:
        record.book.available_copies += 1
        record.book.status = BookStatus.AVAILABLE

    # Overdue fine calculation
    if now > record.due_date:
        overdue_days = max(1, (now.date() - record.due_date.date()).days)
        fine_amount = round(overdue_days * DAILY_OVERDUE_FINE_RATE, 2)
        record.fine_amount = fine_amount
        record.fine_paid = False

        fine_rec = LibraryFineRecord(
            borrow_id=record.id,
            student_id=record.student_id,
            amount=fine_amount,
            overdue_days=overdue_days,
            status="unpaid",
            created_at=now,
        )
        db.add(fine_rec)

    # Check reservation queue for priority notification
    res_item = await db.execute(
        select(BookReservation)
        .where(
            and_(
                BookReservation.book_id == record.book_id,
                BookReservation.status == "active",
            )
        )
        .order_by(BookReservation.priority_number.asc(), BookReservation.reserved_at.asc())
    )
    first_res = res_item.scalars().first()
    if first_res:
        first_res.notified_at = now

    await db.commit()
    await db.refresh(record)
    return serialize_borrow(record)


# ─── Priority Book Reservations ──────────────────────────────────────────────

@router.post("/reserve/{book_id}", response_model=BookReservationOut, status_code=status.HTTP_201_CREATED)
async def reserve_book(
    book_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Place a reservation on a checked-out book in the priority queue."""
    stu_res = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = stu_res.scalars().first()
    if not student:
        raise HTTPException(status_code=403, detail="Student profile not found.")

    book_res = await db.execute(select(Book).where(Book.id == book_id))
    book = book_res.scalars().first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found.")

    if book.available_copies > 0:
        raise HTTPException(
            status_code=400,
            detail="Copies are currently available on shelves. Please borrow directly instead of reserving."
        )

    # Check existing active reservation by this student
    exist_res = await db.execute(
        select(BookReservation).where(
            and_(
                BookReservation.book_id == book_id,
                BookReservation.student_id == student.id,
                BookReservation.status == "active",
            )
        )
    )
    if exist_res.scalars().first():
        raise HTTPException(status_code=400, detail="You already have an active reservation for this book.")

    # Calculate priority number
    count_res = await db.execute(
        select(func.count(BookReservation.id)).where(
            and_(
                BookReservation.book_id == book_id,
                BookReservation.status == "active",
            )
        )
    )
    p_num = (count_res.scalar() or 0) + 1

    now = datetime.utcnow()
    res_obj = BookReservation(
        book_id=book.id,
        student_id=student.id,
        priority_number=p_num,
        reserved_at=now,
        expires_at=now + timedelta(days=7),
        status="active",
    )
    db.add(res_obj)
    await db.commit()
    await db.refresh(res_obj)

    return BookReservationOut(
        id=res_obj.id,
        book_id=book.id,
        book_title=book.title,
        student_id=student.id,
        student_name=current_user.full_name,
        priority_number=p_num,
        reserved_at=res_obj.reserved_at,
        expires_at=res_obj.expires_at,
        notified_at=res_obj.notified_at,
        status=res_obj.status,
    )


@router.delete("/reservations/{reservation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_book_reservation(
    reservation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel an active book reservation."""
    res = await db.execute(
        select(BookReservation).where(BookReservation.id == reservation_id)
    )
    reservation = res.scalars().first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found.")

    if current_user.role not in ["admin", "librarian"]:
        stu_res = await db.execute(select(Student).where(Student.user_id == current_user.id))
        curr_stu = stu_res.scalars().first()
        if not curr_stu or reservation.student_id != curr_stu.id:
            raise HTTPException(status_code=403, detail="Unauthorized access to reservation.")

    reservation.status = "cancelled"
    await db.commit()
    return None


@router.get("/my-reservations", response_model=List[BookReservationOut])
async def list_my_reservations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List active reservations for current student."""
    stu_res = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = stu_res.scalars().first()
    if not student:
        return []

    res = await db.execute(
        select(BookReservation)
        .options(selectinload(BookReservation.book))
        .where(
            and_(
                BookReservation.student_id == student.id,
                BookReservation.status == "active",
            )
        )
        .order_by(BookReservation.reserved_at.desc())
    )
    reservations = res.scalars().all()

    return [
        BookReservationOut(
            id=r.id,
            book_id=r.book_id,
            book_title=r.book.title if r.book else "Unknown",
            student_id=student.id,
            student_name=current_user.full_name,
            priority_number=r.priority_number,
            reserved_at=r.reserved_at,
            expires_at=r.expires_at,
            notified_at=r.notified_at,
            status=r.status,
        )
        for r in reservations
    ]


# ─── Library Fines & Waivers ─────────────────────────────────────────────────

@router.get("/fines", response_model=List[LibraryFineRecordOut])
async def list_library_fines(
    student_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List overdue library fines with student/admin scope."""
    query = (
        select(LibraryFineRecord)
        .options(
            selectinload(LibraryFineRecord.borrow).selectinload(BorrowRecord.book),
            selectinload(LibraryFineRecord.student).selectinload(Student.user),
            selectinload(LibraryFineRecord.waived_by),
        )
        .order_by(desc(LibraryFineRecord.created_at))
    )

    filters = []
    if current_user.role not in ["admin", "librarian"]:
        stu_res = await db.execute(select(Student).where(Student.user_id == current_user.id))
        student = stu_res.scalars().first()
        if not student:
            return []
        filters.append(LibraryFineRecord.student_id == student.id)
    else:
        if student_id:
            filters.append(LibraryFineRecord.student_id == student_id)

    if status_filter and status_filter != "all":
        filters.append(LibraryFineRecord.status == status_filter)

    if filters:
        query = query.where(and_(*filters))

    res = await db.execute(query)
    fines = res.scalars().all()

    return [
        LibraryFineRecordOut(
            id=f.id,
            borrow_id=f.borrow_id,
            student_id=f.student_id,
            student_name=f.student.user.full_name if (f.student and f.student.user) else None,
            book_title=f.borrow.book.title if (f.borrow and f.borrow.book) else None,
            amount=f.amount,
            overdue_days=f.overdue_days,
            status=f.status,
            waived_by_name=f.waived_by.full_name if f.waived_by else None,
            waiver_reason=f.waiver_reason,
            paid_at=f.paid_at,
            created_at=f.created_at,
        )
        for f in fines
    ]


@router.post("/fines/{fine_id}/pay", response_model=LibraryFineRecordOut)
async def pay_library_fine(
    fine_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Settle an outstanding library fine."""
    res = await db.execute(
        select(LibraryFineRecord)
        .options(
            selectinload(LibraryFineRecord.borrow).selectinload(BorrowRecord.book),
            selectinload(LibraryFineRecord.student).selectinload(Student.user),
            selectinload(LibraryFineRecord.waived_by),
        )
        .where(LibraryFineRecord.id == fine_id)
    )
    fine = res.scalars().first()
    if not fine:
        raise HTTPException(status_code=404, detail="Fine record not found.")

    if fine.status == "paid":
        raise HTTPException(status_code=400, detail="This fine is already settled.")

    fine.status = "paid"
    fine.paid_at = datetime.utcnow()
    if fine.borrow:
        fine.borrow.fine_paid = True

    await db.commit()
    await db.refresh(fine)

    return LibraryFineRecordOut(
        id=fine.id,
        borrow_id=fine.borrow_id,
        student_id=fine.student_id,
        student_name=fine.student.user.full_name if (fine.student and fine.student.user) else None,
        book_title=fine.borrow.book.title if (fine.borrow and fine.borrow.book) else None,
        amount=fine.amount,
        overdue_days=fine.overdue_days,
        status=fine.status,
        waived_by_name=None,
        waiver_reason=None,
        paid_at=fine.paid_at,
        created_at=fine.created_at,
    )


@router.post("/fines/{fine_id}/waive", response_model=LibraryFineRecordOut)
async def waive_library_fine(
    fine_id: int,
    reason: str = Query(..., min_length=3),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "librarian")),
):
    """Authorize waiver of a student library fine with recorded justification."""
    res = await db.execute(
        select(LibraryFineRecord)
        .options(
            selectinload(LibraryFineRecord.borrow).selectinload(BorrowRecord.book),
            selectinload(LibraryFineRecord.student).selectinload(Student.user),
        )
        .where(LibraryFineRecord.id == fine_id)
    )
    fine = res.scalars().first()
    if not fine:
        raise HTTPException(status_code=404, detail="Fine record not found.")

    fine.status = "waived"
    fine.waived_by_user_id = current_user.id
    fine.waiver_reason = reason
    if fine.borrow:
        fine.borrow.fine_paid = True

    await db.commit()
    await db.refresh(fine)

    return LibraryFineRecordOut(
        id=fine.id,
        borrow_id=fine.borrow_id,
        student_id=fine.student_id,
        student_name=fine.student.user.full_name if (fine.student and fine.student.user) else None,
        book_title=fine.borrow.book.title if (fine.borrow and fine.borrow.book) else None,
        amount=fine.amount,
        overdue_days=fine.overdue_days,
        status=fine.status,
        waived_by_name=current_user.full_name,
        waiver_reason=fine.waiver_reason,
        paid_at=None,
        created_at=fine.created_at,
    )


# ─── Circulation Analytics ───────────────────────────────────────────────────

@router.get("/stats", response_model=CirculationStatsOut)
async def get_circulation_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Key circulation desk indicators: active loans, overdue counts, and fine collections."""
    active_q = await db.execute(
        select(func.count(BorrowRecord.id)).where(BorrowRecord.status == BorrowStatus.ACTIVE)
    )
    overdue_q = await db.execute(
        select(func.count(BorrowRecord.id)).where(
            or_(
                BorrowRecord.status == BorrowStatus.OVERDUE,
                and_(BorrowRecord.status == BorrowStatus.ACTIVE, BorrowRecord.due_date < datetime.utcnow())
            )
        )
    )
    res_q = await db.execute(
        select(func.count(BookReservation.id)).where(BookReservation.status == "active")
    )
    unpaid_q = await db.execute(
        select(func.sum(LibraryFineRecord.amount)).where(LibraryFineRecord.status == "unpaid")
    )
    collected_q = await db.execute(
        select(func.sum(LibraryFineRecord.amount)).where(LibraryFineRecord.status == "paid")
    )

    return CirculationStatsOut(
        active_loans_count=active_q.scalar() or 0,
        overdue_loans_count=overdue_q.scalar() or 0,
        active_reservations_count=res_q.scalar() or 0,
        unpaid_fines_total=round(unpaid_q.scalar() or 0.0, 2),
        collected_fines_total=round(collected_q.scalar() or 0.0, 2),
    )
