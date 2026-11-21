"""add_student_billing_and_fee_management

Revision ID: i90a1b2c3d4e
Revises: h89c0d1e2f3a
Create Date: 2026-11-21 21:55:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'i90a1b2c3d4e'
down_revision = 'h89c0d1e2f3a'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'fee_structures',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('institution_id', sa.Integer(), sa.ForeignKey('institutions.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('program_id', sa.Integer(), sa.ForeignKey('programs.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('term_type', sa.String(length=50), nullable=False, server_default='semester'),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='LKR'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        'fee_components',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('fee_structure_id', sa.Integer(), sa.ForeignKey('fee_structures.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('is_optional', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('description', sa.Text(), nullable=True),
    )

    op.create_table(
        'student_invoices',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('invoice_number', sa.String(length=50), unique=True, index=True, nullable=False),
        sa.Column('institution_id', sa.Integer(), sa.ForeignKey('institutions.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('fee_structure_id', sa.Integer(), sa.ForeignKey('fee_structures.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('academic_term', sa.String(length=50), nullable=False),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('discount_amount', sa.Float(), nullable=False, server_default=sa.text('0.0')),
        sa.Column('paid_amount', sa.Float(), nullable=False, server_default=sa.text('0.0')),
        sa.Column('balance_due', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='LKR'),
        sa.Column('issue_date', sa.Date(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='unpaid'),
        sa.Column('payment_plan_type', sa.String(length=30), nullable=False, server_default='full'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        'invoice_items',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('invoice_id', sa.Integer(), sa.ForeignKey('student_invoices.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('component_name', sa.String(length=255), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
    )

    op.create_table(
        'invoice_payment_installments',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('invoice_id', sa.Integer(), sa.ForeignKey('student_invoices.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('installment_number', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='pending'),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_table('invoice_payment_installments')
    op.drop_table('invoice_items')
    op.drop_table('student_invoices')
    op.drop_table('fee_components')
    op.drop_table('fee_structures')
