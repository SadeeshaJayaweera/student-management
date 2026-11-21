"""add_payment_gateway_and_financial_auditing

Revision ID: j01b2c3d4e5f
Revises: i90a1b2c3d4e
Create Date: 2026-11-21 23:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'j01b2c3d4e5f'
down_revision = 'i90a1b2c3d4e'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'payment_transactions',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('invoice_id', sa.Integer(), sa.ForeignKey('student_invoices.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('installment_id', sa.Integer(), sa.ForeignKey('invoice_payment_installments.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('transaction_ref', sa.String(length=100), unique=True, index=True, nullable=False),
        sa.Column('gateway', sa.String(length=50), nullable=False, server_default='payhere'),
        sa.Column('gateway_reference', sa.String(length=150), nullable=True, index=True),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='LKR'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='pending'),
        sa.Column('payment_method', sa.String(length=50), nullable=False, server_default='credit_card'),
        sa.Column('idempotency_key', sa.String(length=120), unique=True, nullable=True, index=True),
        sa.Column('payer_email', sa.String(length=255), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        'payment_receipts',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('transaction_id', sa.Integer(), sa.ForeignKey('payment_transactions.id', ondelete='CASCADE'), unique=True, nullable=False, index=True),
        sa.Column('invoice_id', sa.Integer(), sa.ForeignKey('student_invoices.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('receipt_number', sa.String(length=60), unique=True, index=True, nullable=False),
        sa.Column('receipt_url', sa.String(length=500), nullable=True),
        sa.Column('amount_paid', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='LKR'),
        sa.Column('payment_method', sa.String(length=50), nullable=False),
        sa.Column('issued_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('generated_by', sa.String(length=100), nullable=False, server_default='system'),
    )

    op.create_table(
        'financial_audit_logs',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('transaction_id', sa.Integer(), sa.ForeignKey('payment_transactions.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('invoice_id', sa.Integer(), sa.ForeignKey('student_invoices.id', ondelete='CASCADE'), nullable=True, index=True),
        sa.Column('actor_user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('action', sa.String(length=60), nullable=False),
        sa.Column('old_status', sa.String(length=30), nullable=True),
        sa.Column('new_status', sa.String(length=30), nullable=True),
        sa.Column('amount', sa.Float(), nullable=True),
        sa.Column('ip_address', sa.String(length=60), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def downgrade():
    op.drop_table('financial_audit_logs')
    op.drop_table('payment_receipts')
    op.drop_table('payment_transactions')
