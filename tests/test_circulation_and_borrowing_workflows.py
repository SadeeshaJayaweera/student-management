from datetime import datetime, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import (
    User, UserRole, Student, Book, BookStatus, BorrowRecord, BorrowStatus
)
from backend.utils.security import hash_password, create_access_token


@pytest.mark.asyncio
async def test_circulation_and_borrowing_workflows(
    client: AsyncClient,
    test_session: AsyncSession
):
    # 1. Setup Student 1, Student 2, and Librarian users
    student1_user = User(
        email="circ_stu1@nsbm.ac.lk",
        username="circ_stu1",
        hashed_password=hash_password("Pass123!"),
        full_name="Kasun Bandara",
        role=UserRole.STUDENT,
        is_active=True,
    )
    student2_user = User(
        email="circ_stu2@nsbm.ac.lk",
        username="circ_stu2",
        hashed_password=hash_password("Pass123!"),
        full_name="Dilani Jayawardena",
        role=UserRole.STUDENT,
        is_active=True,
    )
    librarian_user = User(
        email="circ_librarian@nsbm.ac.lk",
        username="circ_librarian",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Senior Circulation Officer",
        role=UserRole.ADMIN,
        is_active=True,
    )
    test_session.add_all([student1_user, student2_user, librarian_user])
    await test_session.commit()

    stu1 = Student(
        user_id=student1_user.id,
        student_id="STU-CIRC-01",
        faculty="Computing",
        department="Software Engineering",
        program="BSc Software Engineering",
        year_of_study=2,
        semester=1,
        gpa=3.5,
        credits_earned=60,
    )
    stu2 = Student(
        user_id=student2_user.id,
        student_id="STU-CIRC-02",
        faculty="Computing",
        department="Software Engineering",
        program="BSc Software Engineering",
        year_of_study=2,
        semester=1,
        gpa=3.7,
        credits_earned=60,
    )
    test_session.add_all([stu1, stu2])

    book = Book(
        isbn="978-0132350884",
        title="Clean Code: A Handbook of Agile Software Craftsmanship",
        author="Robert C. Martin",
        publisher="Prentice Hall",
        year=2008,
        category="Computer Science",
        subject="Software Engineering",
        total_copies=1,
        available_copies=1,
        status=BookStatus.AVAILABLE,
    )
    test_session.add(book)
    await test_session.commit()

    s1_token = create_access_token({"sub": str(student1_user.id), "role": "student"})
    s2_token = create_access_token({"sub": str(student2_user.id), "role": "student"})
    lib_token = create_access_token({"sub": str(librarian_user.id), "role": "admin"})

    s1_headers = {"Authorization": f"Bearer {s1_token}"}
    s2_headers = {"Authorization": f"Bearer {s2_token}"}
    lib_headers = {"Authorization": f"Bearer {lib_token}"}

    # 2. Student 1 checks out the only copy of Clean Code
    checkout_payload = {"book_id": book.id}
    res = await client.post("/api/circulation/checkout", json=checkout_payload, headers=s1_headers)
    assert res.status_code == 201
    borrow_data = res.json()
    borrow_id = borrow_data["id"]
    assert borrow_data["book_title"] == "Clean Code: A Handbook of Agile Software Craftsmanship"
    assert borrow_data["status"] == "active"
    assert borrow_data["renewals_count"] == 0

    # Verify book copies updated
    await test_session.refresh(book)
    assert book.available_copies == 0
    assert book.status == BookStatus.BORROWED

    # 3. Student 2 attempts to checkout -> Blocked (No copies available)
    res = await client.post("/api/circulation/checkout", json=checkout_payload, headers=s2_headers)
    assert res.status_code == 400
    assert "No copies currently available" in res.json()["detail"]

    # 4. Student 2 places priority reservation
    res = await client.post(f"/api/circulation/reserve/{book.id}", headers=s2_headers)
    assert res.status_code == 201
    res_data = res.json()
    reservation_id = res_data["id"]
    assert res_data["priority_number"] == 1
    assert res_data["status"] == "active"

    # 5. Student 1 attempts to renew -> Blocked because Student 2 is reserved!
    res = await client.post(f"/api/circulation/renew/{borrow_id}", headers=s1_headers)
    assert res.status_code == 400
    assert "reservation queue" in res.json()["detail"]

    # 6. Student 2 cancels reservation
    res = await client.delete(f"/api/circulation/reservations/{reservation_id}", headers=s2_headers)
    assert res.status_code == 204

    # 7. Student 1 now renews loan successfully
    res = await client.post(f"/api/circulation/renew/{borrow_id}", headers=s1_headers)
    assert res.status_code == 200
    renewed = res.json()
    assert renewed["renewals_count"] == 1

    # 8. Student 1 returns book
    res = await client.post(f"/api/circulation/return/{borrow_id}", headers=s1_headers)
    assert res.status_code == 200
    returned_data = res.json()
    assert returned_data["status"] == "returned"
    assert returned_data["returned_at"] is not None

    # Verify book copy restocked
    await test_session.refresh(book)
    assert book.available_copies == 1
    assert book.status == BookStatus.AVAILABLE

    # 9. Overdue loan and fine waiver workflow
    # Create overdue loan directly in test_session
    overdue_borrow = BorrowRecord(
        book_id=book.id,
        student_id=stu1.id,
        borrowed_at=datetime.utcnow() - timedelta(days=20),
        due_date=datetime.utcnow() - timedelta(days=6),  # 6 days overdue
        status=BorrowStatus.ACTIVE,
        renewals_count=0,
    )
    test_session.add(overdue_borrow)
    await test_session.commit()
    await test_session.refresh(overdue_borrow)

    # Return overdue book -> auto-creates LibraryFineRecord
    res = await client.post(f"/api/circulation/return/{overdue_borrow.id}", headers=s1_headers)
    assert res.status_code == 200
    overdue_ret = res.json()
    assert overdue_ret["fine_amount"] >= 300.0  # 6 days * 50 LKR = 300 LKR

    # Query fines list
    res = await client.get("/api/circulation/fines", headers=s1_headers)
    assert res.status_code == 200
    fines = res.json()
    assert len(fines) >= 1
    fine_id = fines[0]["id"]
    assert fines[0]["status"] == "unpaid"

    # Librarian waives fine
    res = await client.post(f"/api/circulation/fines/{fine_id}/waive?reason=Academic+appeal+granted", headers=lib_headers)
    assert res.status_code == 200
    waived = res.json()
    assert waived["status"] == "waived"
    assert waived["waiver_reason"] == "Academic appeal granted"

    # 10. Check Circulation Stats
    res = await client.get("/api/circulation/stats", headers=lib_headers)
    assert res.status_code == 200
    stats = res.json()
    assert "active_loans_count" in stats
    assert "overdue_loans_count" in stats
