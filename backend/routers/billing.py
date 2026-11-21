"""backend/routers/billing.py
Enterprise Student Billing and Fee Management Router
Handles institutional tuition billing, installment payment plans,
invoice generation, fee component breakdowns, and financial ledger auditing.
"""

import uuid
from datetime import date, datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.models import (
    User,
    Student,
    FeeStructure,
    FeeComponent,
    StudentInvoice,
    InvoiceItem,
    InvoicePaymentInstallment,
)
from backend.schemas import (
    FeeStructureCreate,
    FeeStructureOut,
    StudentInvoiceCreate,
    StudentInvoiceOut,
    InvoiceItemOut,
    InvoiceInstallmentOut,
    BillingSummaryOut,
)
from backend.utils.security import get_current_user, require_roles

router = APIRouter(prefix="/api/billing", tags=["Student Billing & Fee Management"])


def generate_invoice_number() -> str:
    now = datetime.utcnow()
    rand_suffix = uuid.uuid4().hex[:6].upper()
    return f"INV-{now.year}-{rand_suffix}"


def serialize_invoice(inv: StudentInvoice) -> StudentInvoiceOut:
    s_name = inv.student.user.full_name if (inv.student and inv.student.user) else None
    s_num = inv.student.student_id if inv.student else None

    items_out = [
        InvoiceItemOut(
            id=item.id,
            invoice_id=item.invoice_id,
            component_name=item.component_name,
            amount=item.amount,
        )
        for item in (inv.items or [])
    ]

    inst_out = [
        InvoiceInstallmentOut(
            id=inst.id,
            invoice_id=inst.invoice_id,
            installment_number=inst.installment_number,
            amount=inst.amount,
            due_date=inst.due_date,
            status=inst.status,
            paid_at=inst.paid_at,
        )
        for inst in (inv.installments or [])
    ]

    return StudentInvoiceOut(
        id=inv.id,
        invoice_number=inv.invoice_number,
        institution_id=inv.institution_id,
        student_id=inv.student_id,
        student_name=s_name,
        student_number=s_num,
        fee_structure_id=inv.fee_structure_id,
        academic_term=inv.academic_term,
        total_amount=inv.total_amount,
        discount_amount=inv.discount_amount,
        paid_amount=inv.paid_amount,
        balance_due=inv.balance_due,
        currency=inv.currency,
        issue_date=inv.issue_date,
        due_date=inv.due_date,
        status=inv.status,
        payment_plan_type=inv.payment_plan_type,
        notes=inv.notes,
        created_at=inv.created_at,
        items=items_out,
        installments=inst_out,
    )


# ─── Student Invoices Endpoints ──────────────────────────────────────────────

@router.get("/invoices/my", response_model=List[StudentInvoiceOut])
async def list_my_invoices(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve all fee invoices and installment payment plans for current student."""
    stu_res = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = stu_res.scalars().first()
    if not student:
        return []

    res = await db.execute(
        select(StudentInvoice)
        .options(
            selectinload(StudentInvoice.student).selectinload(Student.user),
            selectinload(StudentInvoice.items),
            selectinload(StudentInvoice.installments),
        )
        .where(StudentInvoice.student_id == student.id)
        .order_by(desc(StudentInvoice.created_at))
    )
    invoices = res.scalars().all()
    return [serialize_invoice(inv) for inv in invoices]


@router.get("/invoices/{invoice_id}", response_model=StudentInvoiceOut)
async def get_invoice_detail(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve detailed fee invoice with line-item breakdown."""
    res = await db.execute(
        select(StudentInvoice)
        .options(
            selectinload(StudentInvoice.student).selectinload(Student.user),
            selectinload(StudentInvoice.items),
            selectinload(StudentInvoice.installments),
        )
        .where(StudentInvoice.id == invoice_id)
    )
    inv = res.scalars().first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found.")

    # Authorization: Student owner or Admin/Staff
    stu_res = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = stu_res.scalars().first()
    if current_user.role not in ["admin", "accountant", "registrar"]:
        if not student or inv.student_id != student.id:
            raise HTTPException(status_code=403, detail="Unauthorized access to invoice.")

    return serialize_invoice(inv)


# ─── Admin / Finance Management Endpoints ─────────────────────────────────────

@router.get("/admin/invoices", response_model=List[StudentInvoiceOut])
async def list_admin_invoices(
    student_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None),
    term: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "accountant")),
):
    """Finance staff / admin invoice ledger with multi-criteria filtering."""
    filters = []
    if student_id:
        filters.append(StudentInvoice.student_id == student_id)
    if status_filter and status_filter != "all":
        filters.append(StudentInvoice.status == status_filter)
    if term:
        filters.append(StudentInvoice.academic_term == term)

    query = (
        select(StudentInvoice)
        .options(
            selectinload(StudentInvoice.student).selectinload(Student.user),
            selectinload(StudentInvoice.items),
            selectinload(StudentInvoice.installments),
        )
        .order_by(desc(StudentInvoice.created_at))
        .offset(offset)
        .limit(limit)
    )
    if filters:
        query = query.where(and_(*filters))

    res = await db.execute(query)
    invoices = res.scalars().all()
    return [serialize_invoice(inv) for inv in invoices]


@router.post("/invoices", response_model=StudentInvoiceOut, status_code=status.HTTP_201_CREATED)
async def create_student_invoice(
    payload: StudentInvoiceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "accountant")),
):
    """Generate a student tuition or institutional fee invoice with optional installment plans."""
    stu_res = await db.execute(select(Student).where(Student.id == payload.student_id))
    student = stu_res.scalars().first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    net_balance = max(0.0, payload.total_amount - payload.discount_amount)
    inv_num = generate_invoice_number()
    today = date.today()

    inv = StudentInvoice(
        invoice_number=inv_num,
        student_id=payload.student_id,
        fee_structure_id=payload.fee_structure_id,
        academic_term=payload.academic_term,
        total_amount=payload.total_amount,
        discount_amount=payload.discount_amount,
        paid_amount=0.0,
        balance_due=net_balance,
        currency="LKR",
        issue_date=today,
        due_date=payload.due_date,
        status="unpaid",
        payment_plan_type=payload.payment_plan_type,
        notes=payload.notes,
        created_at=datetime.utcnow(),
    )
    db.add(inv)
    await db.commit()
    await db.refresh(inv)

    # Add line items if provided
    items_to_add = []
    if payload.items:
        for it in payload.items:
            items_to_add.append(
                InvoiceItem(
                    invoice_id=inv.id,
                    component_name=it.component_name,
                    amount=it.amount,
                )
            )
    else:
        # Default tuition component
        items_to_add.append(
            InvoiceItem(
                invoice_id=inv.id,
                component_name="Tuition & Academic Module Delivery",
                amount=payload.total_amount,
            )
        )
    db.add_all(items_to_add)

    # Generate payment plan installments
    installments_to_add = []
    if payload.payment_plan_type == "installment_2":
        part = round(net_balance / 2.0, 2)
        installments_to_add.append(
            InvoicePaymentInstallment(
                invoice_id=inv.id,
                installment_number=1,
                amount=part,
                due_date=payload.due_date,
                status="pending",
            )
        )
        installments_to_add.append(
            InvoicePaymentInstallment(
                invoice_id=inv.id,
                installment_number=2,
                amount=round(net_balance - part, 2),
                due_date=payload.due_date + timedelta(days=60),
                status="pending",
            )
        )
    elif payload.payment_plan_type == "installment_3":
        part = round(net_balance / 3.0, 2)
        installments_to_add.append(
            InvoicePaymentInstallment(
                invoice_id=inv.id,
                installment_number=1,
                amount=part,
                due_date=payload.due_date,
                status="pending",
            )
        )
        installments_to_add.append(
            InvoicePaymentInstallment(
                invoice_id=inv.id,
                installment_number=2,
                amount=part,
                due_date=payload.due_date + timedelta(days=45),
                status="pending",
            )
        )
        installments_to_add.append(
            InvoicePaymentInstallment(
                invoice_id=inv.id,
                installment_number=3,
                amount=round(net_balance - (part * 2), 2),
                due_date=payload.due_date + timedelta(days=90),
                status="pending",
            )
        )
    else:
        installments_to_add.append(
            InvoicePaymentInstallment(
                invoice_id=inv.id,
                installment_number=1,
                amount=net_balance,
                due_date=payload.due_date,
                status="pending",
            )
        )
    db.add_all(installments_to_add)
    await db.commit()

    # Reload with relations
    reload_res = await db.execute(
        select(StudentInvoice)
        .options(
            selectinload(StudentInvoice.student).selectinload(Student.user),
            selectinload(StudentInvoice.items),
            selectinload(StudentInvoice.installments),
        )
        .where(StudentInvoice.id == inv.id)
    )
    loaded = reload_res.scalars().first()
    return serialize_invoice(loaded)


# ─── Fee Structure Templates ──────────────────────────────────────────────────

@router.post("/fee-structures", response_model=FeeStructureOut, status_code=status.HTTP_201_CREATED)
async def create_fee_structure(
    payload: FeeStructureCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "accountant")),
):
    """Define institutional fee structure template with component breakdowns."""
    fee_struct = FeeStructure(
        name=payload.name,
        program_id=payload.program_id,
        term_type=payload.term_type,
        total_amount=payload.total_amount,
        currency=payload.currency,
        is_active=True,
        created_at=datetime.utcnow(),
    )
    db.add(fee_struct)
    await db.commit()
    await db.refresh(fee_struct)

    comps = []
    if payload.components:
        for c in payload.components:
            comps.append(
                FeeComponent(
                    fee_structure_id=fee_struct.id,
                    name=c.name,
                    amount=c.amount,
                    is_optional=c.is_optional,
                    description=c.description,
                )
            )
    else:
        comps.append(
            FeeComponent(
                fee_structure_id=fee_struct.id,
                name="Tuition Fee",
                amount=payload.total_amount,
                is_optional=False,
            )
        )
    db.add_all(comps)
    await db.commit()

    res = await db.execute(
        select(FeeStructure)
        .options(selectinload(FeeStructure.components))
        .where(FeeStructure.id == fee_struct.id)
    )
    return res.scalars().first()


@router.get("/fee-structures", response_model=List[FeeStructureOut])
async def list_fee_structures(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all available institutional fee structures."""
    res = await db.execute(
        select(FeeStructure)
        .options(selectinload(FeeStructure.components))
        .where(FeeStructure.is_active == True)
        .order_by(FeeStructure.name.asc())
    )
    return res.scalars().all()


@router.get("/summary", response_model=BillingSummaryOut)
async def get_billing_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "accountant")),
):
    """Institutional billing KPI summary: receivables, collections, and overdue rates."""
    res = await db.execute(select(StudentInvoice))
    all_invoices = res.scalars().all()

    tot_invoiced = sum(i.total_amount - i.discount_amount for i in all_invoices)
    tot_collected = sum(i.paid_amount for i in all_invoices)
    tot_outstanding = sum(i.balance_due for i in all_invoices)
    today = date.today()
    tot_overdue = sum(i.balance_due for i in all_invoices if i.due_date < today and i.balance_due > 0)

    paid_cnt = sum(1 for i in all_invoices if i.status == "paid")
    overdue_cnt = sum(1 for i in all_invoices if i.due_date < today and i.balance_due > 0)

    return BillingSummaryOut(
        total_invoiced=round(tot_invoiced, 2),
        total_collected=round(tot_collected, 2),
        total_outstanding=round(tot_outstanding, 2),
        total_overdue=round(tot_overdue, 2),
        invoices_count=len(all_invoices),
        paid_invoices_count=paid_cnt,
        overdue_invoices_count=overdue_cnt,
        currency="LKR",
    )
