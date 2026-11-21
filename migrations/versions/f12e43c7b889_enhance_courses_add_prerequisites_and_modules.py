"""enhance_courses_add_prerequisites_and_modules

Revision ID: f12e43c7b889
Revises: a91b32d6e442
Create Date: 2026-11-21 05:45:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f12e43c7b889'
down_revision: Union[str, None] = 'a91b32d6e442'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add new columns to courses table
    with op.batch_alter_table('courses', schema=None) as batch_op:
        batch_op.add_column(sa.Column('program_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('faculty_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('department_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('delivery_method', sa.String(length=50), nullable=False, server_default='in_person'))
        batch_op.add_column(sa.Column('learning_outcomes', sa.JSON(), nullable=True))
        batch_op.create_foreign_key(batch_op.f('fk_courses_program_id_programs'), 'programs', ['program_id'], ['id'], ondelete='SET NULL')
        batch_op.create_foreign_key(batch_op.f('fk_courses_faculty_id_faculties'), 'faculties', ['faculty_id'], ['id'], ondelete='SET NULL')
        batch_op.create_foreign_key(batch_op.f('fk_courses_department_id_departments'), 'departments', ['department_id'], ['id'], ondelete='SET NULL')
        batch_op.create_index(batch_op.f('ix_courses_program_id'), ['program_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_courses_faculty_id'), ['faculty_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_courses_department_id'), ['department_id'], unique=False)

    # 2. Create course_prerequisites table
    op.create_table(
        'course_prerequisites',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('prerequisite_course_id', sa.Integer(), nullable=False),
        sa.Column('is_mandatory', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('minimum_grade', sa.String(length=5), nullable=False, server_default='C'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], name=op.f('fk_course_prerequisites_course_id_courses'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['prerequisite_course_id'], ['courses.id'], name=op.f('fk_course_prerequisites_prerequisite_course_id_courses'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_course_prerequisites'))
    )
    with op.batch_alter_table('course_prerequisites', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_course_prerequisites_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_course_prerequisites_course_id'), ['course_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_course_prerequisites_prerequisite_course_id'), ['prerequisite_course_id'], unique=False)

    # 3. Create course_modules table
    op.create_table(
        'course_modules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('learning_objectives', sa.JSON(), nullable=True),
        sa.Column('estimated_hours', sa.Float(), nullable=False, server_default='10.0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], name=op.f('fk_course_modules_course_id_courses'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_course_modules'))
    )
    with op.batch_alter_table('course_modules', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_course_modules_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_course_modules_course_id'), ['course_id'], unique=False)


def downgrade() -> None:
    op.drop_table('course_modules')
    op.drop_table('course_prerequisites')
    with op.batch_alter_table('courses', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_courses_department_id'))
        batch_op.drop_index(batch_op.f('ix_courses_faculty_id'))
        batch_op.drop_index(batch_op.f('ix_courses_program_id'))
        batch_op.drop_constraint(batch_op.f('fk_courses_department_id_departments'), type_='foreignkey')
        batch_op.drop_constraint(batch_op.f('fk_courses_faculty_id_faculties'), type_='foreignkey')
        batch_op.drop_constraint(batch_op.f('fk_courses_program_id_programs'), type_='foreignkey')
        batch_op.drop_column('learning_outcomes')
        batch_op.drop_column('delivery_method')
        batch_op.drop_column('department_id')
        batch_op.drop_column('faculty_id')
        batch_op.drop_column('program_id')
