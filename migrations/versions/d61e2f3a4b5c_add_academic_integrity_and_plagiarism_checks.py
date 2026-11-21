"""add_academic_integrity_and_plagiarism_checks

Revision ID: d61e2f3a4b5c
Revises: c50d1e2f3a4b
Create Date: 2026-11-21 15:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd61e2f3a4b5c'
down_revision = 'c50d1e2f3a4b'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'plagiarism_scan_reports',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('submission_id', sa.Integer(), sa.ForeignKey('assignment_submissions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('assignment_id', sa.Integer(), sa.ForeignKey('assignments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False),
        sa.Column('similarity_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='completed'),
        sa.Column('integrity_flag', sa.String(length=30), nullable=False, server_default='clean'),
        sa.Column('matched_sources', sa.JSON(), nullable=True),
        sa.Column('scanned_content_hash', sa.String(length=64), nullable=True),
        sa.Column('instructor_notes', sa.Text(), nullable=True),
        sa.Column('reviewed_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index(op.f('ix_plagiarism_scan_reports_submission_id'), 'plagiarism_scan_reports', ['submission_id'], unique=True)
    op.create_index(op.f('ix_plagiarism_scan_reports_assignment_id'), 'plagiarism_scan_reports', ['assignment_id'], unique=False)
    op.create_index(op.f('ix_plagiarism_scan_reports_student_id'), 'plagiarism_scan_reports', ['student_id'], unique=False)
    op.create_index(op.f('ix_plagiarism_scan_reports_reviewed_by_id'), 'plagiarism_scan_reports', ['reviewed_by_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_plagiarism_scan_reports_reviewed_by_id'), table_name='plagiarism_scan_reports')
    op.drop_index(op.f('ix_plagiarism_scan_reports_student_id'), table_name='plagiarism_scan_reports')
    op.drop_index(op.f('ix_plagiarism_scan_reports_assignment_id'), table_name='plagiarism_scan_reports')
    op.drop_index(op.f('ix_plagiarism_scan_reports_submission_id'), table_name='plagiarism_scan_reports')
    op.drop_table('plagiarism_scan_reports')
