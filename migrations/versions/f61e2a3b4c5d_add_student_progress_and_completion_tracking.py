"""add_student_progress_and_completion_tracking

Revision ID: f61e2a3b4c5d
Revises: e50d1f2a3b4c
Create Date: 2026-11-21 12:48:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f61e2a3b4c5d'
down_revision = 'e50d1f2a3b4c'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'student_lesson_progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('lesson_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='in_progress'),
        sa.Column('time_spent_seconds', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['lesson_id'], ['course_lessons.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('student_lesson_progress', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_student_lesson_progress_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_student_lesson_progress_lesson_id'), ['lesson_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_student_lesson_progress_student_id'), ['student_id'], unique=False)

    op.create_table(
        'student_module_progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('module_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='in_progress'),
        sa.Column('completed_items_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_items_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('progress_percentage', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['module_id'], ['course_modules.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('student_module_progress', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_student_module_progress_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_student_module_progress_module_id'), ['module_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_student_module_progress_student_id'), ['student_id'], unique=False)


def downgrade():
    with op.batch_alter_table('student_module_progress', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_student_module_progress_student_id'))
        batch_op.drop_index(batch_op.f('ix_student_module_progress_module_id'))
        batch_op.drop_index(batch_op.f('ix_student_module_progress_id'))
    op.drop_table('student_module_progress')

    with op.batch_alter_table('student_lesson_progress', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_student_lesson_progress_student_id'))
        batch_op.drop_index(batch_op.f('ix_student_lesson_progress_lesson_id'))
        batch_op.drop_index(batch_op.f('ix_student_lesson_progress_id'))
    op.drop_table('student_lesson_progress')
