"""add_advanced_student_timetable

Revision ID: a12b3c4d5e6f
Revises: f83a4b5c6d7e
Create Date: 2026-11-21 19:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a12b3c4d5e6f'
down_revision = 'f83a4b5c6d7e'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'timetable_slots',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('course_id', sa.Integer(), sa.ForeignKey('courses.id', ondelete='CASCADE'), nullable=True, index=True),
        sa.Column('lecturer_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('day_of_week', sa.Integer(), nullable=False, index=True),
        sa.Column('start_time', sa.String(length=10), nullable=False),
        sa.Column('end_time', sa.String(length=10), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('slot_type', sa.String(length=50), nullable=False, server_default='lecture'),
        sa.Column('room', sa.String(length=100), nullable=False),
        sa.Column('building', sa.String(length=100), nullable=True),
        sa.Column('recurrence_pattern', sa.String(length=50), nullable=False, server_default='weekly'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('color', sa.String(length=20), nullable=False, server_default='#4F46E5'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
    )


def downgrade():
    op.drop_table('timetable_slots')
