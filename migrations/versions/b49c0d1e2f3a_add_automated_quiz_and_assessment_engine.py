"""add_automated_quiz_and_assessment_engine

Revision ID: b49c0d1e2f3a
Revises: a38b9c0d1e2f
Create Date: 2026-11-21 14:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b49c0d1e2f3a'
down_revision = 'a38b9c0d1e2f'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'quizzes',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('course_id', sa.Integer(), sa.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('module_id', sa.Integer(), sa.ForeignKey('course_modules.id', ondelete='SET NULL'), nullable=True),
        sa.Column('creator_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('instructions', sa.Text(), nullable=True),
        sa.Column('time_limit_minutes', sa.Integer(), nullable=True),
        sa.Column('passing_score_percentage', sa.Float(), nullable=False, server_default='50.0'),
        sa.Column('max_attempts', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('shuffle_questions', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('shuffle_options', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('show_correct_answers', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('allow_backtracking', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('total_points', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='published'),
        sa.Column('available_from', sa.DateTime(), nullable=True),
        sa.Column('due_date', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index(op.f('ix_quizzes_course_id'), 'quizzes', ['course_id'], unique=False)
    op.create_index(op.f('ix_quizzes_module_id'), 'quizzes', ['module_id'], unique=False)
    op.create_index(op.f('ix_quizzes_creator_id'), 'quizzes', ['creator_id'], unique=False)

    op.create_table(
        'quiz_questions',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('quiz_id', sa.Integer(), sa.ForeignKey('quizzes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_item_id', sa.Integer(), sa.ForeignKey('question_bank_items.id', ondelete='CASCADE'), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('points', sa.Float(), nullable=False, server_default='1.0'),
    )
    op.create_index(op.f('ix_quiz_questions_quiz_id'), 'quiz_questions', ['quiz_id'], unique=False)
    op.create_index(op.f('ix_quiz_questions_question_item_id'), 'quiz_questions', ['question_item_id'], unique=False)

    op.create_table(
        'quiz_attempts',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('quiz_id', sa.Integer(), sa.ForeignKey('quizzes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False),
        sa.Column('attempt_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('total_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('max_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('percentage', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('is_passed', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='in_progress'),
        sa.Column('answers', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index(op.f('ix_quiz_attempts_quiz_id'), 'quiz_attempts', ['quiz_id'], unique=False)
    op.create_index(op.f('ix_quiz_attempts_student_id'), 'quiz_attempts', ['student_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_quiz_attempts_student_id'), table_name='quiz_attempts')
    op.drop_index(op.f('ix_quiz_attempts_quiz_id'), table_name='quiz_attempts')
    op.drop_table('quiz_attempts')

    op.drop_index(op.f('ix_quiz_questions_question_item_id'), table_name='quiz_questions')
    op.drop_index(op.f('ix_quiz_questions_quiz_id'), table_name='quiz_questions')
    op.drop_table('quiz_questions')

    op.drop_index(op.f('ix_quizzes_creator_id'), table_name='quizzes')
    op.drop_index(op.f('ix_quizzes_module_id'), table_name='quizzes')
    op.drop_index(op.f('ix_quizzes_course_id'), table_name='quizzes')
    op.drop_table('quizzes')
