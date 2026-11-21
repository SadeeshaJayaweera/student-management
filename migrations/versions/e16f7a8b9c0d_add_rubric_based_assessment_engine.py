"""add_rubric_based_assessment_engine

Revision ID: e16f7a8b9c0d
Revises: d05e6f7a8b9c
Create Date: 2026-11-21 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e16f7a8b9c0d'
down_revision = 'd05e6f7a8b9c'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'rubrics',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('course_id', sa.Integer(), sa.ForeignKey('courses.id', ondelete='CASCADE'), nullable=True),
        sa.Column('creator_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('scoring_strategy', sa.String(length=50), nullable=False, server_default='analytic'),
        sa.Column('is_template', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('total_points', sa.Float(), nullable=False, server_default='100.0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index(op.f('ix_rubrics_course_id'), 'rubrics', ['course_id'], unique=False)
    op.create_index(op.f('ix_rubrics_creator_id'), 'rubrics', ['creator_id'], unique=False)

    op.create_table(
        'rubric_criteria',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('rubric_id', sa.Integer(), sa.ForeignKey('rubrics.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('max_points', sa.Float(), nullable=False, server_default='10.0'),
        sa.Column('weight', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
    )
    op.create_index(op.f('ix_rubric_criteria_rubric_id'), 'rubric_criteria', ['rubric_id'], unique=False)

    op.create_table(
        'rubric_levels',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('criterion_id', sa.Integer(), sa.ForeignKey('rubric_criteria.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('point_value', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
    )
    op.create_index(op.f('ix_rubric_levels_criterion_id'), 'rubric_levels', ['criterion_id'], unique=False)

    op.create_table(
        'rubric_evaluations',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('rubric_id', sa.Integer(), sa.ForeignKey('rubrics.id', ondelete='CASCADE'), nullable=False),
        sa.Column('assignment_id', sa.Integer(), sa.ForeignKey('assignments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('submission_id', sa.Integer(), sa.ForeignKey('assignment_submissions.id', ondelete='CASCADE'), nullable=True),
        sa.Column('grader_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('total_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('max_possible_score', sa.Float(), nullable=False, server_default='100.0'),
        sa.Column('percentage', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('criteria_scores', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index(op.f('ix_rubric_evaluations_rubric_id'), 'rubric_evaluations', ['rubric_id'], unique=False)
    op.create_index(op.f('ix_rubric_evaluations_assignment_id'), 'rubric_evaluations', ['assignment_id'], unique=False)
    op.create_index(op.f('ix_rubric_evaluations_submission_id'), 'rubric_evaluations', ['submission_id'], unique=False)
    op.create_index(op.f('ix_rubric_evaluations_grader_id'), 'rubric_evaluations', ['grader_id'], unique=False)

    with op.batch_alter_table('assignments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('rubric_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_assignments_rubric_id', 'rubrics', ['rubric_id'], ['id'], ondelete='SET NULL')
        batch_op.create_index(batch_op.f('ix_assignments_rubric_id'), ['rubric_id'], unique=False)


def downgrade():
    with op.batch_alter_table('assignments', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_assignments_rubric_id'))
        batch_op.drop_constraint('fk_assignments_rubric_id', type_='foreignkey')
        batch_op.drop_column('rubric_id')

    op.drop_index(op.f('ix_rubric_evaluations_grader_id'), table_name='rubric_evaluations')
    op.drop_index(op.f('ix_rubric_evaluations_submission_id'), table_name='rubric_evaluations')
    op.drop_index(op.f('ix_rubric_evaluations_assignment_id'), table_name='rubric_evaluations')
    op.drop_index(op.f('ix_rubric_evaluations_rubric_id'), table_name='rubric_evaluations')
    op.drop_table('rubric_evaluations')

    op.drop_index(op.f('ix_rubric_levels_criterion_id'), table_name='rubric_levels')
    op.drop_table('rubric_levels')

    op.drop_index(op.f('ix_rubric_criteria_rubric_id'), table_name='rubric_criteria')
    op.drop_table('rubric_criteria')

    op.drop_index(op.f('ix_rubrics_creator_id'), table_name='rubrics')
    op.drop_index(op.f('ix_rubrics_course_id'), table_name='rubrics')
    op.drop_table('rubrics')
