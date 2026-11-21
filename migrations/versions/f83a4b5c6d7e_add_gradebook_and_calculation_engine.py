"""add_gradebook_and_calculation_engine

Revision ID: f83a4b5c6d7e
Revises: e72f3a4b5c6d
Create Date: 2026-11-21 16:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f83a4b5c6d7e'
down_revision = 'e72f3a4b5c6d'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'gradebook_categories',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('course_id', sa.Integer(), sa.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('weight_percentage', sa.Float(), nullable=False, server_default='25.0'),
        sa.Column('drop_lowest_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
    )

    op.create_table(
        'grade_scales',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('course_id', sa.Integer(), sa.ForeignKey('courses.id', ondelete='CASCADE'), nullable=True, index=True),
        sa.Column('name', sa.String(length=100), nullable=False, server_default='Standard Letter Scale'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('scale_brackets', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
    )

    op.create_table(
        'gradebook_overrides',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('course_id', sa.Integer(), sa.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('overridden_percentage', sa.Float(), nullable=True),
        sa.Column('overridden_letter_grade', sa.String(length=10), nullable=True),
        sa.Column('overridden_gpa_points', sa.Float(), nullable=True),
        sa.Column('override_reason', sa.Text(), nullable=False),
        sa.Column('overridden_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
    )

    with op.batch_alter_table('assignments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('category_id', sa.Integer(), sa.ForeignKey('gradebook_categories.id', ondelete='SET NULL'), nullable=True))

    with op.batch_alter_table('quizzes', schema=None) as batch_op:
        batch_op.add_column(sa.Column('category_id', sa.Integer(), sa.ForeignKey('gradebook_categories.id', ondelete='SET NULL'), nullable=True))


def downgrade():
    with op.batch_alter_table('quizzes', schema=None) as batch_op:
        batch_op.drop_column('category_id')

    with op.batch_alter_table('assignments', schema=None) as batch_op:
        batch_op.drop_column('category_id')

    op.drop_table('gradebook_overrides')
    op.drop_table('grade_scales')
    op.drop_table('gradebook_categories')
