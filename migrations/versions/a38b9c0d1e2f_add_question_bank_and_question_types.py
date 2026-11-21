"""add_question_bank_and_question_types

Revision ID: a38b9c0d1e2f
Revises: f27a8b9c0d1e
Create Date: 2026-11-21 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a38b9c0d1e2f'
down_revision = 'f27a8b9c0d1e'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'question_categories',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('course_id', sa.Integer(), sa.ForeignKey('courses.id', ondelete='CASCADE'), nullable=True),
        sa.Column('parent_id', sa.Integer(), sa.ForeignKey('question_categories.id', ondelete='CASCADE'), nullable=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index(op.f('ix_question_categories_course_id'), 'question_categories', ['course_id'], unique=False)
    op.create_index(op.f('ix_question_categories_parent_id'), 'question_categories', ['parent_id'], unique=False)

    op.create_table(
        'question_bank_items',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('course_id', sa.Integer(), sa.ForeignKey('courses.id', ondelete='CASCADE'), nullable=True),
        sa.Column('category_id', sa.Integer(), sa.ForeignKey('question_categories.id', ondelete='SET NULL'), nullable=True),
        sa.Column('creator_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('rubric_id', sa.Integer(), sa.ForeignKey('rubrics.id', ondelete='SET NULL'), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('question_type', sa.String(length=50), nullable=False),
        sa.Column('difficulty_level', sa.String(length=20), nullable=False, server_default='intermediate'),
        sa.Column('default_points', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('options', sa.JSON(), nullable=True),
        sa.Column('answer_key', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index(op.f('ix_question_bank_items_course_id'), 'question_bank_items', ['course_id'], unique=False)
    op.create_index(op.f('ix_question_bank_items_category_id'), 'question_bank_items', ['category_id'], unique=False)
    op.create_index(op.f('ix_question_bank_items_creator_id'), 'question_bank_items', ['creator_id'], unique=False)
    op.create_index(op.f('ix_question_bank_items_rubric_id'), 'question_bank_items', ['rubric_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_question_bank_items_rubric_id'), table_name='question_bank_items')
    op.drop_index(op.f('ix_question_bank_items_creator_id'), table_name='question_bank_items')
    op.drop_index(op.f('ix_question_bank_items_category_id'), table_name='question_bank_items')
    op.drop_index(op.f('ix_question_bank_items_course_id'), table_name='question_bank_items')
    op.drop_table('question_bank_items')

    op.drop_index(op.f('ix_question_categories_parent_id'), table_name='question_categories')
    op.drop_index(op.f('ix_question_categories_course_id'), table_name='question_categories')
    op.drop_table('question_categories')
