"""add_student_calendar_and_task_management

Revision ID: c34d5e6f7a8b
Revises: b23c4d5e6f7a
Create Date: 2026-11-21 20:05:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c34d5e6f7a8b'
down_revision = 'b23c4d5e6f7a'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'student_tasks',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('course_id', sa.Integer(), sa.ForeignKey('courses.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('due_date', sa.DateTime(), nullable=True, index=True),
        sa.Column('priority', sa.String(length=20), nullable=False, server_default='medium'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='todo'),
        sa.Column('category', sa.String(length=50), nullable=False, server_default='study'),
        sa.Column('estimated_minutes', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('reminder_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
    )

    op.create_table(
        'calendar_events',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=True, index=True),
        sa.Column('course_id', sa.Integer(), sa.ForeignKey('courses.id', ondelete='CASCADE'), nullable=True, index=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('event_type', sa.String(length=50), nullable=False, server_default='personal'),
        sa.Column('start_time', sa.DateTime(), nullable=False, index=True),
        sa.Column('end_time', sa.DateTime(), nullable=False, index=True),
        sa.Column('all_day', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('location', sa.String(length=200), nullable=True),
        sa.Column('color', sa.String(length=20), nullable=False, server_default='#4F46E5'),
        sa.Column('is_system_generated', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
    )


def downgrade():
    op.drop_table('calendar_events')
    op.drop_table('student_tasks')
