"""add_student_feedback_and_course_evaluation

Revision ID: g78b9c0d1e2f
Revises: f67a8b9c0d1e
Create Date: 2026-11-21 20:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'g78b9c0d1e2f'
down_revision = 'f67a8b9c0d1e'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'course_evaluation_surveys',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('institution_id', sa.Integer(), sa.ForeignKey('institutions.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('course_id', sa.Integer(), sa.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('is_published', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('is_anonymous', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        'survey_questions',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('survey_id', sa.Integer(), sa.ForeignKey('course_evaluation_surveys.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('question_type', sa.String(length=50), nullable=False, server_default='rating_scale_5'),
        sa.Column('category', sa.String(length=50), nullable=False, server_default='instructor_effectiveness'),
        sa.Column('is_required', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('options_json', sa.JSON(), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default=sa.text('0')),
    )

    op.create_table(
        'survey_responses',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('survey_id', sa.Integer(), sa.ForeignKey('course_evaluation_surveys.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('students.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('student_hash', sa.String(length=64), nullable=True, index=True),
        sa.Column('submitted_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        'survey_answers',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('response_id', sa.Integer(), sa.ForeignKey('survey_responses.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('question_id', sa.Integer(), sa.ForeignKey('survey_questions.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('numeric_rating', sa.Float(), nullable=True),
        sa.Column('text_response', sa.Text(), nullable=True),
        sa.Column('selected_options_json', sa.JSON(), nullable=True),
    )


def downgrade():
    op.drop_table('survey_answers')
    op.drop_table('survey_responses')
    op.drop_table('survey_questions')
    op.drop_table('course_evaluation_surveys')
