"""add_grading_workflows_and_feedback_delivery

Revision ID: e72f3a4b5c6d
Revises: d61e2f3a4b5c
Create Date: 2026-11-21 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e72f3a4b5c6d'
down_revision = 'd61e2f3a4b5c'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('assignments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('grades_released', sa.Boolean(), nullable=False, server_default=sa.text('1')))
        batch_op.add_column(sa.Column('grades_released_at', sa.DateTime(), nullable=True))

    op.create_table(
        'submission_annotations',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('submission_id', sa.Integer(), sa.ForeignKey('assignment_submissions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('coordinates', sa.JSON(), nullable=True),
        sa.Column('comment_text', sa.Text(), nullable=False),
        sa.Column('author_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index(op.f('ix_submission_annotations_submission_id'), 'submission_annotations', ['submission_id'], unique=False)
    op.create_index(op.f('ix_submission_annotations_author_id'), 'submission_annotations', ['author_id'], unique=False)

    op.create_table(
        'grade_appeals',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('assignment_id', sa.Integer(), sa.ForeignKey('assignments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('submission_id', sa.Integer(), sa.ForeignKey('assignment_submissions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('requested_marks', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='pending'),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('resolved_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index(op.f('ix_grade_appeals_assignment_id'), 'grade_appeals', ['assignment_id'], unique=False)
    op.create_index(op.f('ix_grade_appeals_submission_id'), 'grade_appeals', ['submission_id'], unique=False)
    op.create_index(op.f('ix_grade_appeals_student_id'), 'grade_appeals', ['student_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_grade_appeals_student_id'), table_name='grade_appeals')
    op.drop_index(op.f('ix_grade_appeals_submission_id'), table_name='grade_appeals')
    op.drop_index(op.f('ix_grade_appeals_assignment_id'), table_name='grade_appeals')
    op.drop_table('grade_appeals')

    op.drop_index(op.f('ix_submission_annotations_author_id'), table_name='submission_annotations')
    op.drop_index(op.f('ix_submission_annotations_submission_id'), table_name='submission_annotations')
    op.drop_table('submission_annotations')

    with op.batch_alter_table('assignments', schema=None) as batch_op:
        batch_op.drop_column('grades_released_at')
        batch_op.drop_column('grades_released')
