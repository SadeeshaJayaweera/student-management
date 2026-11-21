"""add_assignment_submission_and_versioning

Revision ID: f27a8b9c0d1e
Revises: e16f7a8b9c0d
Create Date: 2026-11-21 14:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f27a8b9c0d1e'
down_revision = 'e16f7a8b9c0d'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('assignment_submissions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('attempt_number', sa.Integer(), nullable=False, server_default='1'))
        batch_op.add_column(sa.Column('submission_receipt', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('attachments', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('is_late', sa.Boolean(), nullable=False, server_default=sa.text('0')))
        batch_op.add_column(sa.Column('days_late', sa.Float(), nullable=False, server_default='0.0'))
        batch_op.add_column(sa.Column('late_penalty_applied', sa.Float(), nullable=False, server_default='0.0'))
        batch_op.add_column(sa.Column('originality_score', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('originality_report_url', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('graded_by_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('graded_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(), nullable=True))
        batch_op.create_foreign_key('fk_assignment_submissions_graded_by_id', 'users', ['graded_by_id'], ['id'], ondelete='SET NULL')
        batch_op.create_index(batch_op.f('ix_assignment_submissions_submission_receipt'), ['submission_receipt'], unique=False)
        batch_op.create_index(batch_op.f('ix_assignment_submissions_assignment_id'), ['assignment_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_assignment_submissions_student_id'), ['student_id'], unique=False)

    op.create_table(
        'assignment_submission_versions',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('submission_id', sa.Integer(), sa.ForeignKey('assignment_submissions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('file_url', sa.String(length=500), nullable=True),
        sa.Column('text_content', sa.Text(), nullable=True),
        sa.Column('attachments', sa.JSON(), nullable=True),
        sa.Column('submission_receipt', sa.String(length=100), nullable=False),
        sa.Column('is_late', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('days_late', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('submitted_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index(op.f('ix_assignment_submission_versions_submission_id'), 'assignment_submission_versions', ['submission_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_assignment_submission_versions_submission_id'), table_name='assignment_submission_versions')
    op.drop_table('assignment_submission_versions')

    with op.batch_alter_table('assignment_submissions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_assignment_submissions_student_id'))
        batch_op.drop_index(batch_op.f('ix_assignment_submissions_assignment_id'))
        batch_op.drop_index(batch_op.f('ix_assignment_submissions_submission_receipt'))
        batch_op.drop_constraint('fk_assignment_submissions_graded_by_id', type_='foreignkey')
        batch_op.drop_column('updated_at')
        batch_op.drop_column('graded_at')
        batch_op.drop_column('graded_by_id')
        batch_op.drop_column('originality_report_url')
        batch_op.drop_column('originality_score')
        batch_op.drop_column('late_penalty_applied')
        batch_op.drop_column('days_late')
        batch_op.drop_column('is_late')
        batch_op.drop_column('attachments')
        batch_op.drop_column('submission_receipt')
        batch_op.drop_column('attempt_number')
