"""add_circulation_and_borrowing_workflows

Revision ID: l23d4e5f6a7b
Revises: k12c3d4e5f6a
Create Date: 2026-11-21 23:56:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'l23d4e5f6a7b'
down_revision = 'k12c3d4e5f6a'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('borrow_records', sa.Column('renewals_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('borrow_records', sa.Column('renewed_at', sa.DateTime(), nullable=True))
    op.add_column('book_reservations', sa.Column('priority_number', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('book_reservations', sa.Column('notified_at', sa.DateTime(), nullable=True))

    op.create_table(
        'library_fine_records',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('borrow_id', sa.Integer(), sa.ForeignKey('borrow_records.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('overdue_days', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='unpaid'),
        sa.Column('waived_by_user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('waiver_reason', sa.Text(), nullable=True),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def downgrade():
    op.drop_table('library_fine_records')
    op.drop_column('book_reservations', 'notified_at')
    op.drop_column('book_reservations', 'priority_number')
    op.drop_column('borrow_records', 'renewed_at')
    op.drop_column('borrow_records', 'renewals_count')
