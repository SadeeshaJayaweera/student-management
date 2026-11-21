from datetime import date, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import User, UserRole, Student
from backend.utils.security import hash_password, create_access_token


@pytest.mark.asyncio
async def test_student_billing_and_fee_management(
    client: AsyncClient,
    test_session: AsyncSession
):
    # 1. Setup Student and Admin users
    student_user = User(
        email="billing_student@nsbm.ac.lk",
        username="billing_student",
        hashed_password=hash_password("Pass123!"),
        full_name="Kavindu Madusanka",
        role=UserRole.STUDENT,
        is_active=True,
    )
    admin_user = User(
        email="billing_admin@nsbm.ac.lk",
        username="billing_admin",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Bursar Financial Admin",
        role=UserRole.ADMIN,
        is_active=True,
    )
    test_session.add_all([student_user, admin_user])
    await test_session.commit()

    student = Student(
        user_id=student_user.id,
        student_id="STU-FEE-01",
        faculty="Computing",
        department="Software Engineering",
        program="BSc Software Engineering",
        year_of_study=3,
        semester=1,
        gpa=3.75,
        credits_earned=90,
    )
    test_session.add(student)
    await test_session.commit()

    student_token = create_access_token({"sub": str(student_user.id), "role": "student"})
    admin_token = create_access_token({"sub": str(admin_user.id), "role": "admin"})

    student_headers = {"Authorization": f"Bearer {student_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Admin creates Fee Structure template
    fee_struct_payload = {
        "name": "BSc Software Engineering - Year 3",
        "program_id": None,
        "term_type": "semester",
        "total_amount": 350000.0,
        "currency": "LKR",
        "components": [
            {"name": "Tuition & Lectures", "amount": 280000.0, "is_optional": False},
            {"name": "Computing Lab & Cloud Infrastructure", "amount": 50000.0, "is_optional": False},
            {"name": "Library & Digital Resources", "amount": 20000.0, "is_optional": False},
        ]
    }
    res = await client.post("/api/billing/fee-structures", json=fee_struct_payload, headers=admin_headers)
    assert res.status_code == 201
    fs_data = res.json()
    assert fs_data["name"] == "BSc Software Engineering - Year 3"
    assert len(fs_data["components"]) == 3
    fee_struct_id = fs_data["id"]

    # 3. Student views available fee structures
    res = await client.get("/api/billing/fee-structures", headers=student_headers)
    assert res.status_code == 200
    structures = res.json()
    assert any(s["id"] == fee_struct_id for s in structures)

    # 4. Admin generates invoice for student with 2-part installment plan
    invoice_payload = {
        "student_id": student.id,
        "fee_structure_id": fee_struct_id,
        "academic_term": "Year 3 Semester 1 (2026)",
        "total_amount": 350000.0,
        "discount_amount": 25000.0,  # e.g. Dean's list scholarship
        "due_date": (date.today() + timedelta(days=30)).isoformat(),
        "payment_plan_type": "installment_2",
        "notes": "Includes 25,000 LKR merit discount",
        "items": [
            {"component_name": "Tuition Fee", "amount": 280000.0},
            {"component_name": "Lab Fee", "amount": 50000.0},
            {"component_name": "Library Fee", "amount": 20000.0},
        ]
    }
    res = await client.post("/api/billing/invoices", json=invoice_payload, headers=admin_headers)
    assert res.status_code == 201
    inv_data = res.json()
    assert inv_data["total_amount"] == 350000.0
    assert inv_data["discount_amount"] == 25000.0
    assert inv_data["balance_due"] == 325000.0
    assert inv_data["status"] == "unpaid"
    assert len(inv_data["items"]) == 3
    assert len(inv_data["installments"]) == 2
    invoice_id = inv_data["id"]

    # Check installments values
    inst_1 = inv_data["installments"][0]
    inst_2 = inv_data["installments"][1]
    assert inst_1["installment_number"] == 1
    assert inst_2["installment_number"] == 2
    assert round(inst_1["amount"] + inst_2["amount"], 2) == 325000.0

    # 5. Student queries their own invoices
    res = await client.get("/api/billing/invoices/my", headers=student_headers)
    assert res.status_code == 200
    my_invoices = res.json()
    assert len(my_invoices) >= 1
    my_inv = next(i for i in my_invoices if i["id"] == invoice_id)
    assert my_inv["balance_due"] == 325000.0
    assert len(my_inv["installments"]) == 2

    # 6. Student views individual invoice detail
    res = await client.get(f"/api/billing/invoices/{invoice_id}", headers=student_headers)
    assert res.status_code == 200
    detail = res.json()
    assert detail["id"] == invoice_id
    assert detail["student_name"] == "Kavindu Madusanka"

    # 7. Admin lists all invoices
    res = await client.get("/api/billing/admin/invoices", headers=admin_headers)
    assert res.status_code == 200
    admin_invoices = res.json()
    assert any(i["id"] == invoice_id for i in admin_invoices)

    # 8. Admin queries billing summary dashboard
    res = await client.get("/api/billing/summary", headers=admin_headers)
    assert res.status_code == 200
    summary = res.json()
    assert summary["total_invoiced"] >= 325000.0
    assert summary["total_outstanding"] >= 325000.0
    assert summary["invoices_count"] >= 1
