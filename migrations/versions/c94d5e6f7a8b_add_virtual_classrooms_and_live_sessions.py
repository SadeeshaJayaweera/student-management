"""add_virtual_classrooms_and_live_sessions

Revision ID: c94d5e6f7a8b
Revises: b83c4d5e6f7a
Create Date: 2026-11-21 13:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c94d5e6f7a8b'
down_revision = 'b83c4d5e6f7a'
branch_labels = None
depends_on = None


def upgrade():
    # 1. virtual_classroom_sessions
    op.create_table(
        'virtual_classroom_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('host_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('provider', sa.String(length=50), nullable=False, server_default='zoom'),
        sa.Column('meeting_id', sa.String(length=255), nullable=True),
        sa.Column('join_url', sa.String(length=1024), nullable=False),
        sa.Column('host_url', sa.String(length=1024), nullable=True),
        sa.Column('passcode', sa.String(length=100), nullable=True),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='scheduled'),
        sa.Column('recording_url', sa.String(length=1024), nullable=True),
        sa.Column('recording_duration_minutes', sa.Integer(), nullable=True),
        sa.Column('is_recorded', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('max_participants', sa.Integer(), nullable=True, server_default='100'),
        sa.Column('session_settings', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['host_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('virtual_classroom_sessions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_virtual_classroom_sessions_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_virtual_classroom_sessions_course_id'), ['course_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_virtual_classroom_sessions_host_id'), ['host_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_virtual_classroom_sessions_start_time'), ['start_time'], unique=False)

    # 2. virtual_classroom_attendance
    op.create_table(
        'virtual_classroom_attendance',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=True),
        sa.Column('joined_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('left_at', sa.DateTime(), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('device_type', sa.String(length=100), nullable=True, server_default='browser'),
        sa.Column('attendance_status', sa.String(length=30), nullable=False, server_default='present'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['virtual_classroom_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id', 'user_id', name='uq_session_user_attendance')
    )
    with op.batch_alter_table('virtual_classroom_attendance', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_virtual_classroom_attendance_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_virtual_classroom_attendance_session_id'), ['session_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_virtual_classroom_attendance_user_id'), ['user_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_virtual_classroom_attendance_student_id'), ['student_id'], unique=False)


def downgrade():
    op.drop_table('virtual_classroom_attendance')
    op.drop_table('virtual_classroom_sessions')
