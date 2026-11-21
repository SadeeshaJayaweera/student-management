"""backend/routers/payments.py
Enterprise Payment Gateway Integration and Financial Auditing Router
Handles institutional tuition payments, gateway checkout redirection,
cryptographic webhook HMAC signature validation, automated receipt generation,
and immutable financial audit ledger logging.
"""

import hmac
import hashlib
import uuid
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.models import (
    User,
    Student,
    StudentInvoice,
    InvoicePaymentInstallment,
    PaymentTransaction,
    PaymentReceipt,
    FinancialAuditLog,
)
from backend.schemas import (
    PaymentCheckoutRequest,
    PaymentCheckoutResponse,
    PaymentWebhookPayload,
    PaymentTransactionOut,
    PaymentReceiptOut,
    FinancialAuditLogOut,
    ManualPaymentRecordRequest,
)
from backend.utils.security import get_current_user, require_roles
from backend.config import settings

router = APIRouter(prefix="/api/payments", tags=["Payment Gateway & Financial Auditing"])

WEBHOOK_SECRET = getattr(settings, "payment_webhook_secret", "nsbm-pay-secret-key-2026-production")


def compute_signature(txn_ref: str, gateway_ref: str, amount: float, status_str: str) -> str:
    """Compute HMAC-SHA256 signature for payment verification."""
    message = f"{txn_ref}:{gateway_ref}:{amount:.2f}:{status_str}"
    return hmac.new(
        WEBHOOK_SECRET.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


# ─── Student Payment Flow Endpoints ──────────────────────────────────────────

@router.post("/checkout", response_model=PaymentCheckoutResponse, status_code=status.HTTP_201_CREATED)
async def initiate_payment_checkout(
    payload: PaymentCheckoutRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Initiate an online payment checkout session with idempotency controls."""
    # Find student
    stu_res = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = stu_res.scalars().first()
    if not student:
        raise HTTPException(status_code=403, detail="Only registered students can initiate payments.")

    # Find invoice
    inv_res = await db.execute(
        select(StudentInvoice)
        .options(selectinload(StudentInvoice.installments))
        .where(StudentInvoice.id == payload.invoice_id)
    )
    invoice = inv_res.scalars().first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found.")

    if invoice.student_id != student.id:
        raise HTTPException(status_code=403, detail="Unauthorized access to this invoice.")

    if invoice.balance_due <= 0 or invoice.status == "paid":
        raise HTTPException(status_code=400, detail="This invoice has already been fully paid.")

    # Determine payable amount
    installment = None
    if payload.installment_id:
        inst_res = await db.execute(
            select(InvoicePaymentInstallment).where(
                and_(
                    InvoicePaymentInstallment.id == payload.installment_id,
                    InvoicePaymentInstallment.invoice_id == invoice.id,
                )
            )
        )
        installment = inst_res.scalars().first()
        if not installment:
            raise HTTPException(status_code=404, detail="Installment not found on this invoice.")
        if installment.status == "paid":
            raise HTTPException(status_code=400, detail="This installment is already paid.")
        payable_amount = installment.amount
    else:
        payable_amount = invoice.balance_due

    # Check idempotency key if supplied
    if payload.idempotency_key:
        exist_txn = await db.execute(
            select(PaymentTransaction).where(
                PaymentTransaction.idempotency_key == payload.idempotency_key
            )
        )
        existing = exist_txn.scalars().first()
        if existing:
            return PaymentCheckoutResponse(
                transaction_id=existing.id,
                transaction_ref=existing.transaction_ref,
                amount=existing.amount,
                currency=existing.currency,
                status=existing.status,
                gateway=existing.gateway,
                checkout_url=f"https://sandbox.payhere.lk/pay/{existing.transaction_ref}",
                checkout_params={"order_id": existing.transaction_ref, "amount": existing.amount},
            )

    txn_ref = f"TXN-{uuid.uuid4().hex[:10].upper()}"
    client_ip = request.client.host if request.client else None

    txn = PaymentTransaction(
        invoice_id=invoice.id,
        installment_id=installment.id if installment else None,
        student_id=student.id,
        transaction_ref=txn_ref,
        gateway=payload.gateway,
        amount=payable_amount,
        currency=invoice.currency,
        status="pending",
        payment_method=payload.payment_method,
        idempotency_key=payload.idempotency_key,
        payer_email=current_user.email,
        created_at=datetime.utcnow(),
    )
    db.add(txn)
    await db.commit()
    await db.refresh(txn)

    # Log financial audit event
    audit = FinancialAuditLog(
        transaction_id=txn.id,
        invoice_id=invoice.id,
        actor_user_id=current_user.id,
        action="checkout_initiated",
        old_status=None,
        new_status="pending",
        amount=payable_amount,
        ip_address=client_ip,
        details={
            "gateway": payload.gateway,
            "method": payload.payment_method,
            "installment_id": installment.id if installment else None,
            "invoice_number": invoice.invoice_number,
        },
        created_at=datetime.utcnow(),
    )
    db.add(audit)
    await db.commit()

    return PaymentCheckoutResponse(
        transaction_id=txn.id,
        transaction_ref=txn_ref,
        amount=payable_amount,
        currency=invoice.currency,
        status="pending",
        gateway=payload.gateway,
        checkout_url=f"https://sandbox.payhere.lk/pay/{txn_ref}",
        checkout_params={
            "merchant_id": "NSBM_EDU_01",
            "order_id": txn_ref,
            "items": f"Tuition Payment: {invoice.invoice_number}",
            "amount": payable_amount,
            "currency": invoice.currency,
            "first_name": current_user.full_name,
            "email": current_user.email,
        },
    )


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def payment_gateway_webhook(
    payload: PaymentWebhookPayload,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Cryptographic webhook handler verifying HMAC signatures from payment gateways."""
    # Verify HMAC signature
    expected_sig = compute_signature(
        payload.transaction_ref,
        payload.gateway_reference,
        payload.amount,
        payload.status
    )
    if not hmac.compare_digest(expected_sig, payload.signature):
        raise HTTPException(status_code=400, detail="Invalid cryptographic HMAC signature.")

    # Find transaction
    txn_res = await db.execute(
        select(PaymentTransaction).where(
            PaymentTransaction.transaction_ref == payload.transaction_ref
        )
    )
    txn = txn_res.scalars().first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found.")

    # Idempotent processing
    if txn.status == "completed":
        return {"status": "already_processed", "transaction_ref": txn.transaction_ref}

    client_ip = request.client.host if request.client else None
    old_status = txn.status

    if payload.status == "completed":
        txn.status = "completed"
        txn.gateway_reference = payload.gateway_reference
        if payload.payer_email:
            txn.payer_email = payload.payer_email
        txn.updated_at = datetime.utcnow()

        # Update invoice
        inv_res = await db.execute(
            select(StudentInvoice).where(StudentInvoice.id == txn.invoice_id)
        )
        invoice = inv_res.scalars().first()
        if invoice:
            invoice.paid_amount = round(invoice.paid_amount + txn.amount, 2)
            invoice.balance_due = max(0.0, round(invoice.balance_due - txn.amount, 2))
            if invoice.balance_due <= 0.0:
                invoice.status = "paid"
            else:
                invoice.status = "partially_paid"
            invoice.updated_at = datetime.utcnow()

        # Update installment if linked
        if txn.installment_id:
            inst_res = await db.execute(
                select(InvoicePaymentInstallment).where(
                    InvoicePaymentInstallment.id == txn.installment_id
                )
            )
            installment = inst_res.scalars().first()
            if installment:
                installment.status = "paid"
                installment.paid_at = datetime.utcnow()

        # Generate Payment Receipt
        rcp_num = f"RCP-{datetime.utcnow().year}-{uuid.uuid4().hex[:8].upper()}"
        receipt = PaymentReceipt(
            transaction_id=txn.id,
            invoice_id=txn.invoice_id,
            receipt_number=rcp_num,
            receipt_url=f"/receipts/{rcp_num}.pdf",
            amount_paid=txn.amount,
            currency=txn.currency,
            payment_method=txn.payment_method,
            issued_at=datetime.utcnow(),
            generated_by="gateway_webhook",
        )
        db.add(receipt)

        # Audit Log
        audit = FinancialAuditLog(
            transaction_id=txn.id,
            invoice_id=txn.invoice_id,
            actor_user_id=None,
            action="webhook_verified",
            old_status=old_status,
            new_status="completed",
            amount=txn.amount,
            ip_address=client_ip,
            details={
                "gateway_ref": payload.gateway_reference,
                "receipt_number": rcp_num,
                "invoice_balance": invoice.balance_due if invoice else None,
            },
            created_at=datetime.utcnow(),
        )
        db.add(audit)
        await db.commit()

        return {"status": "success", "receipt_number": rcp_num, "transaction_ref": txn.transaction_ref}

    else:
        # Failed payment
        txn.status = "failed"
        txn.error_message = payload.error_message or "Payment failed at gateway."
        txn.updated_at = datetime.utcnow()

        audit = FinancialAuditLog(
            transaction_id=txn.id,
            invoice_id=txn.invoice_id,
            actor_user_id=None,
            action="payment_failed",
            old_status=old_status,
            new_status="failed",
            amount=txn.amount,
            ip_address=client_ip,
            details={"error": txn.error_message},
            created_at=datetime.utcnow(),
        )
        db.add(audit)
        await db.commit()

        return {"status": "failed", "transaction_ref": txn.transaction_ref}


@router.get("/my-transactions", response_model=List[PaymentTransactionOut])
async def list_my_transactions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve all payment transactions and receipts for the logged-in student."""
    stu_res = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = stu_res.scalars().first()
    if not student:
        return []

    res = await db.execute(
        select(PaymentTransaction)
        .options(selectinload(PaymentTransaction.receipt))
        .where(PaymentTransaction.student_id == student.id)
        .order_by(desc(PaymentTransaction.created_at))
    )
    return res.scalars().all()


@router.get("/receipts/{receipt_number}", response_model=PaymentReceiptOut)
async def get_receipt_by_number(
    receipt_number: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch official payment receipt for printing or verification."""
    res = await db.execute(
        select(PaymentReceipt)
        .options(selectinload(PaymentReceipt.invoice))
        .where(PaymentReceipt.receipt_number == receipt_number)
    )
    receipt = res.scalars().first()
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found.")

    # Authorization
    if current_user.role not in ["admin", "accountant"]:
        stu_res = await db.execute(select(Student).where(Student.user_id == current_user.id))
        student = stu_res.scalars().first()
        if not student or receipt.invoice.student_id != student.id:
            raise HTTPException(status_code=403, detail="Unauthorized access to receipt.")

    return receipt


# ─── Finance Administration & Audit Endpoints ────────────────────────────────

@router.post("/admin/manual-record", response_model=PaymentReceiptOut, status_code=status.HTTP_201_CREATED)
async def record_manual_payment(
    payload: ManualPaymentRecordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "accountant")),
):
    """Bursar/finance staff recording of offline bank transfer or cash payments."""
    inv_res = await db.execute(
        select(StudentInvoice).where(StudentInvoice.id == payload.invoice_id)
    )
    invoice = inv_res.scalars().first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found.")

    installment = None
    if payload.installment_id:
        inst_res = await db.execute(
            select(InvoicePaymentInstallment).where(
                and_(
                    InvoicePaymentInstallment.id == payload.installment_id,
                    InvoicePaymentInstallment.invoice_id == invoice.id,
                )
            )
        )
        installment = inst_res.scalars().first()

    txn_ref = f"MAN-{uuid.uuid4().hex[:10].upper()}"
    client_ip = request.client.host if request.client else None

    txn = PaymentTransaction(
        invoice_id=invoice.id,
        installment_id=installment.id if installment else None,
        student_id=invoice.student_id,
        transaction_ref=txn_ref,
        gateway="offline_manual",
        gateway_reference=payload.reference_note,
        amount=payload.amount,
        currency=invoice.currency,
        status="completed",
        payment_method=payload.payment_method,
        payer_email=None,
        created_at=datetime.utcnow(),
    )
    db.add(txn)
    await db.commit()
    await db.refresh(txn)

    # Update invoice balance
    invoice.paid_amount = round(invoice.paid_amount + payload.amount, 2)
    invoice.balance_due = max(0.0, round(invoice.balance_due - payload.amount, 2))
    if invoice.balance_due <= 0.0:
        invoice.status = "paid"
    else:
        invoice.status = "partially_paid"
    invoice.updated_at = datetime.utcnow()

    # Update installment if linked
    if installment:
        installment.status = "paid"
        installment.paid_at = datetime.utcnow()

    # Create official receipt
    rcp_num = f"RCP-MAN-{datetime.utcnow().year}-{uuid.uuid4().hex[:8].upper()}"
    receipt = PaymentReceipt(
        transaction_id=txn.id,
        invoice_id=invoice.id,
        receipt_number=rcp_num,
        receipt_url=f"/receipts/{rcp_num}.pdf",
        amount_paid=payload.amount,
        currency=invoice.currency,
        payment_method=payload.payment_method,
        issued_at=datetime.utcnow(),
        generated_by=current_user.full_name,
    )
    db.add(receipt)

    # Financial Audit Log
    audit = FinancialAuditLog(
        transaction_id=txn.id,
        invoice_id=invoice.id,
        actor_user_id=current_user.id,
        action="manual_payment_recorded",
        old_status=None,
        new_status="completed",
        amount=payload.amount,
        ip_address=client_ip,
        details={
            "recorded_by": current_user.full_name,
            "reference_note": payload.reference_note,
            "method": payload.payment_method,
            "receipt_number": rcp_num,
        },
        created_at=datetime.utcnow(),
    )
    db.add(audit)
    await db.commit()
    await db.refresh(receipt)

    return receipt


@router.get("/admin/audit-ledger", response_model=List[FinancialAuditLogOut])
async def list_financial_audit_ledger(
    action: Optional[str] = Query(None),
    invoice_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "accountant")),
):
    """Institutional immutable financial audit ledger with multi-field filtering."""
    query = (
        select(FinancialAuditLog)
        .options(selectinload(FinancialAuditLog.actor))
        .order_by(desc(FinancialAuditLog.created_at))
        .offset(offset)
        .limit(limit)
    )
    filters = []
    if action:
        filters.append(FinancialAuditLog.action == action)
    if invoice_id:
        filters.append(FinancialAuditLog.invoice_id == invoice_id)

    if filters:
        query = query.where(and_(*filters))

    res = await db.execute(query)
    logs = res.scalars().all()

    return [
        FinancialAuditLogOut(
            id=log.id,
            transaction_id=log.transaction_id,
            invoice_id=log.invoice_id,
            actor_user_id=log.actor_user_id,
            actor_name=log.actor.full_name if log.actor else "System / Webhook",
            action=log.action,
            old_status=log.old_status,
            new_status=log.new_status,
            amount=log.amount,
            ip_address=log.ip_address,
            details=log.details,
            created_at=log.created_at,
        )
        for log in logs
    ]
