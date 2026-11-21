"""add_attendance_and_participation_management

Revision ID: b23c4d5e6f7a
Revises: a12b3c4d5e6f
Create Date: 2026-11-21 19:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b23c4d5e6f7a'
down_revision = 'a12b3c4d5e6f'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'attendance_sessions',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('course_id', sa.Integer(), sa.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('timetable_slot_id', sa.Integer(), sa.ForeignKey('timetable_slots.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('session_title', sa.String(length=200), nullable=False),
        sa.Column('session_date', sa.Date(), nullable=False),
        sa.Column('start_time', sa.String(length=10), nullable=False),
        sa.Column('end_time', sa.String(length=10), nullable=False),
        sa.Column('checkin_code', sa.String(length=10), nullable=True),
        sa.Column('code_expires_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='open'),
        sa.Column('allow_self_checkin', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
    )

    op.create_table(
        'attendance_correction_requests',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('course_id', sa.Integer(), sa.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('session_id', sa.Integer(), sa.ForeignKey('attendance_sessions.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('attendance_date', sa.Date(), nullable=False),
        sa.Column('requested_status', sa.String(length=30), nullable=False, server_default='excused'),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('supporting_document_url', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='pending'),
        sa.Column('reviewed_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('review_comment', sa.Text(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
    )

    with op.batch_alter_table('attendance') as batch_op:
        batch_op.add_column(sa.Column('session_id', sa.Integer(), sa.ForeignKey('attendance_sessions.id', ondelete='SET NULL'), nullable=True))
        batch_op.add_column(sa.Column('checkin_method', sa.String(length=50), nullable=False, server_default='manual'))
        batch_op.add_column(sa.Column('checked_in_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('participation_score', sa.Float(), nullable=False, server_default='0.0'))
        batch_op.add_column(sa.Column('remarks', sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table('attendance') as batch_op:
        batch_op.drop_column('remarks')
        batch_op.drop_column('participation_score')
        batch_op.drop_column('checked_in_at')
        batch_op.drop_column('checkin_method')
        batch_op.drop_column('session_id')

    op.drop_table('attendance_correction_requests')
    op.drop_table('attendance_sessions')
