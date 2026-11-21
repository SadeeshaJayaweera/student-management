"""add_timed_examinations_and_proctoring_controls

Revision ID: c50d1e2f3a4b
Revises: b49c0d1e2f3a
Create Date: 2026-11-21 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c50d1e2f3a4b'
down_revision = 'b49c0d1e2f3a'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'exam_proctoring_sessions',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('quiz_id', sa.Integer(), sa.ForeignKey('quizzes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False),
        sa.Column('attempt_id', sa.Integer(), sa.ForeignKey('quiz_attempts.id', ondelete='CASCADE'), nullable=True),
        sa.Column('session_token', sa.String(length=100), nullable=False),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('user_agent', sa.String(length=255), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('last_heartbeat_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='active'),
        sa.Column('tab_switch_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('fullscreen_exit_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('copy_paste_attempt_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_flagged', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('flag_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index(op.f('ix_exam_proctoring_sessions_quiz_id'), 'exam_proctoring_sessions', ['quiz_id'], unique=False)
    op.create_index(op.f('ix_exam_proctoring_sessions_student_id'), 'exam_proctoring_sessions', ['student_id'], unique=False)
    op.create_index(op.f('ix_exam_proctoring_sessions_attempt_id'), 'exam_proctoring_sessions', ['attempt_id'], unique=False)
    op.create_index(op.f('ix_exam_proctoring_sessions_session_token'), 'exam_proctoring_sessions', ['session_token'], unique=True)

    op.create_table(
        'exam_proctoring_events',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('session_id', sa.Integer(), sa.ForeignKey('exam_proctoring_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False, server_default='low'),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index(op.f('ix_exam_proctoring_events_session_id'), 'exam_proctoring_events', ['session_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_exam_proctoring_events_session_id'), table_name='exam_proctoring_events')
    op.drop_table('exam_proctoring_events')

    op.drop_index(op.f('ix_exam_proctoring_sessions_session_token'), table_name='exam_proctoring_sessions')
    op.drop_index(op.f('ix_exam_proctoring_sessions_attempt_id'), table_name='exam_proctoring_sessions')
    op.drop_index(op.f('ix_exam_proctoring_sessions_student_id'), table_name='exam_proctoring_sessions')
    op.drop_index(op.f('ix_exam_proctoring_sessions_quiz_id'), table_name='exam_proctoring_sessions')
    op.drop_table('exam_proctoring_sessions')
