"""add_student_wellbeing_and_support_workflows

Revision ID: h89c0d1e2f3a
Revises: g78b9c0d1e2f
Create Date: 2026-11-21 21:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'h89c0d1e2f3a'
down_revision = 'g78b9c0d1e2f'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'wellbeing_support_requests',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('institution_id', sa.Integer(), sa.ForeignKey('institutions.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('request_type', sa.String(length=50), nullable=False, server_default='counseling'),
        sa.Column('subject', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('urgency', sa.String(length=30), nullable=False, server_default='normal'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='submitted'),
        sa.Column('assigned_counselor_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('is_confidential', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        'wellbeing_appointments',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('request_id', sa.Integer(), sa.ForeignKey('wellbeing_support_requests.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('counselor_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('appointment_type', sa.String(length=30), nullable=False, server_default='virtual'),
        sa.Column('scheduled_at', sa.DateTime(), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False, server_default=sa.text('45')),
        sa.Column('location_or_link', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='scheduled'),
        sa.Column('meeting_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        'wellbeing_resources',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('institution_id', sa.Integer(), sa.ForeignKey('institutions.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False, server_default='mental_health'),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('content_url', sa.String(length=500), nullable=True),
        sa.Column('emergency_phone', sa.String(length=50), nullable=True),
        sa.Column('is_crisis_resource', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('is_featured', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def downgrade():
    op.drop_table('wellbeing_resources')
    op.drop_table('wellbeing_appointments')
    op.drop_table('wellbeing_support_requests')
