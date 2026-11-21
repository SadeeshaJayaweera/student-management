import hmac
import hashlib
from datetime import date, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import (
    User, UserRole, Student, StudentInvoice, InvoicePaymentInstallment
)
from backend.utils.security import hash_password, create_access_token
from backend.routers.payments import WEBHOOK_SECRET


@pytest.mark.asyncio
async def test_payment_gateway_and_financial_auditing(
    client: AsyncClient,
    test_session: AsyncSession
):
    # 1. Setup Student and Admin users
    student_user = User(
        email="pay_student@nsbm.ac.lk",
        username="pay_student",
        hashed_password=hash_password("Pass123!"),
        full_name="Thisara Perera",
        role=UserRole.STUDENT,
        is_active=True,
    )
    admin_user = User(
        email="pay_admin@nsbm.ac.lk",
        username="pay_admin",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Chief Bursar",
        role=UserRole.ADMIN,
        is_active=True,
    )
    test_session.add_all([student_user, admin_user])
    await test_session.commit()

    student = Student(
        user_id=student_user.id,
        student_id="STU-PAY-01",
        faculty="Computing",
        department="Software Engineering",
        program="BSc Software Engineering",
        year_of_study=2,
        semester=2,
        gpa=3.8,
        credits_earned=60,
    )
    test_session.add(student)
    await test_session.commit()

    # Create Invoice with 2 installments
    invoice = StudentInvoice(
        invoice_number="INV-2026-PAY001",
        student_id=student.id,
        academic_term="Year 2 Semester 2",
        total_amount=200000.0,
        discount_amount=0.0,
        paid_amount=0.0,
        balance_due=200000.0,
        currency="LKR",
        issue_date=date.today(),
        due_date=date.today() + timedelta(days=30),
        status="unpaid",
        payment_plan_type="installment_2",
    )
    test_session.add(invoice)
    await test_session.commit()
    await test_session.refresh(invoice)

    inst1 = InvoicePaymentInstallment(
        invoice_id=invoice.id,
        installment_number=1,
        amount=100000.0,
        due_date=date.today() + timedelta(days=15),
        status="pending",
    )
    inst2 = InvoicePaymentInstallment(
        invoice_id=invoice.id,
        installment_number=2,
        amount=100000.0,
        due_date=date.today() + timedelta(days=45),
        status="pending",
    )
    test_session.add_all([inst1, inst2])
    await test_session.commit()
    await test_session.refresh(inst1)
    await test_session.refresh(inst2)

    student_token = create_access_token({"sub": str(student_user.id), "role": "student"})
    admin_token = create_access_token({"sub": str(admin_user.id), "role": "admin"})
    student_headers = {"Authorization": f"Bearer {student_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Student initiates checkout for installment 1
    checkout_payload = {
        "invoice_id": invoice.id,
        "installment_id": inst1.id,
        "payment_method": "credit_card",
        "gateway": "payhere",
    }
    res = await client.post("/api/payments/checkout", json=checkout_payload, headers=student_headers)
    assert res.status_code == 201
    checkout_data = res.json()
    txn_ref = checkout_data["transaction_ref"]
    assert checkout_data["amount"] == 100000.0
    assert checkout_data["status"] == "pending"
    assert "payhere" in checkout_data["checkout_url"]

    # 3. Simulate Invalid Webhook Signature -> Should fail with 400
    invalid_webhook_payload = {
        "transaction_ref": txn_ref,
        "gateway_reference": "GATEWAY-REF-9999",
        "status": "completed",
        "amount": 100000.0,
        "currency": "LKR",
        "signature": "bogus_invalid_signature_hash",
    }
    res = await client.post("/api/payments/webhook", json=invalid_webhook_payload)
    assert res.status_code == 400
    assert "Invalid cryptographic HMAC signature" in res.json()["detail"]

    # 4. Valid Webhook Signature Computation & Delivery
    gateway_ref = "PAYHERE-GW-883719"
    amount = 100000.0
    status_str = "completed"
    msg = f"{txn_ref}:{gateway_ref}:{amount:.2f}:{status_str}"
    valid_signature = hmac.new(
        WEBHOOK_SECRET.encode("utf-8"),
        msg.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    valid_webhook_payload = {
        "transaction_ref": txn_ref,
        "gateway_reference": gateway_ref,
        "status": "completed",
        "amount": amount,
        "currency": "LKR",
        "signature": valid_signature,
        "payer_email": "pay_student@nsbm.ac.lk",
    }
    res = await client.post("/api/payments/webhook", json=valid_webhook_payload)
    assert res.status_code == 200
    webhook_res = res.json()
    assert webhook_res["status"] == "success"
    receipt_number = webhook_res["receipt_number"]
    assert receipt_number.startswith("RCP-")

    # 5. Check invoice status was updated to partially_paid and inst1 marked paid
    res = await client.get(f"/api/billing/invoices/{invoice.id}", headers=student_headers)
    assert res.status_code == 200
    updated_inv = res.json()
    assert updated_inv["status"] == "partially_paid"
    assert updated_inv["paid_amount"] == 100000.0
    assert updated_inv["balance_due"] == 100000.0

    # 6. Student views transaction history
    res = await client.get("/api/payments/my-transactions", headers=student_headers)
    assert res.status_code == 200
    txns = res.json()
    assert len(txns) >= 1
    my_txn = next(t for t in txns if t["transaction_ref"] == txn_ref)
    assert my_txn["status"] == "completed"
    assert my_txn["receipt"]["receipt_number"] == receipt_number

    # 7. Student retrieves official receipt
    res = await client.get(f"/api/payments/receipts/{receipt_number}", headers=student_headers)
    assert res.status_code == 200
    receipt_data = res.json()
    assert receipt_data["receipt_number"] == receipt_number
    assert receipt_data["amount_paid"] == 100000.0

    # 8. Admin records manual payment for installment 2 (Offline Bank Deposit)
    manual_payload = {
        "invoice_id": invoice.id,
        "installment_id": inst2.id,
        "amount": 100000.0,
        "payment_method": "bank_transfer",
        "reference_note": "BOC-DEP-SLIP-77192",
    }
    res = await client.post("/api/payments/admin/manual-record", json=manual_payload, headers=admin_headers)
    assert res.status_code == 201
    manual_receipt = res.json()
    assert manual_receipt["receipt_number"].startswith("RCP-MAN-")

    # Verify invoice is now fully paid
    res = await client.get(f"/api/billing/invoices/{invoice.id}", headers=student_headers)
    assert res.status_code == 200
    fully_paid_inv = res.json()
    assert fully_paid_inv["status"] == "paid"
    assert fully_paid_inv["balance_due"] == 0.0
    assert fully_paid_inv["paid_amount"] == 200000.0

    # 9. Admin inspects immutable financial audit ledger
    res = await client.get("/api/payments/admin/audit-ledger", headers=admin_headers)
    assert res.status_code == 200
    logs = res.json()
    actions = [l["action"] for l in logs]
    assert "checkout_initiated" in actions
    assert "webhook_verified" in actions
    assert "manual_payment_recorded" in actions
