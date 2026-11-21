"""enhance_student_profile_and_academic_status

Revision ID: 8912d37c4e51
Revises: f12e43c7b889
Create Date: 2026-11-21 05:50:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8912d37c4e51'
down_revision: Union[str, None] = 'f12e43c7b889'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('students', schema=None) as batch_op:
        batch_op.add_column(sa.Column('campus_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('program_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('faculty_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('department_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('academic_standing', sa.String(length=50), nullable=False, server_default='good_standing'))
        batch_op.add_column(sa.Column('enrollment_status', sa.String(length=50), nullable=False, server_default='enrolled'))
        batch_op.add_column(sa.Column('national_id', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('date_of_birth', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('gender', sa.String(length=20), nullable=True))
        batch_op.create_foreign_key(batch_op.f('fk_students_campus_id_campuses'), 'campuses', ['campus_id'], ['id'], ondelete='SET NULL')
        batch_op.create_foreign_key(batch_op.f('fk_students_program_id_programs'), 'programs', ['program_id'], ['id'], ondelete='SET NULL')
        batch_op.create_foreign_key(batch_op.f('fk_students_faculty_id_faculties'), 'faculties', ['faculty_id'], ['id'], ondelete='SET NULL')
        batch_op.create_foreign_key(batch_op.f('fk_students_department_id_departments'), 'departments', ['department_id'], ['id'], ondelete='SET NULL')
        batch_op.create_index(batch_op.f('ix_students_campus_id'), ['campus_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_students_program_id'), ['program_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_students_faculty_id'), ['faculty_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_students_department_id'), ['department_id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('students', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_students_department_id'))
        batch_op.drop_index(batch_op.f('ix_students_faculty_id'))
        batch_op.drop_index(batch_op.f('ix_students_program_id'))
        batch_op.drop_index(batch_op.f('ix_students_campus_id'))
        batch_op.drop_constraint(batch_op.f('fk_students_department_id_departments'), type_='foreignkey')
        batch_op.drop_constraint(batch_op.f('fk_students_faculty_id_faculties'), type_='foreignkey')
        batch_op.drop_constraint(batch_op.f('fk_students_program_id_programs'), type_='foreignkey')
        batch_op.drop_constraint(batch_op.f('fk_students_campus_id_campuses'), type_='foreignkey')
        batch_op.drop_column('gender')
        batch_op.drop_column('date_of_birth')
        batch_op.drop_column('national_id')
        batch_op.drop_column('enrollment_status')
        batch_op.drop_column('academic_standing')
        batch_op.drop_column('department_id')
        batch_op.drop_column('faculty_id')
        batch_op.drop_column('program_id')
        batch_op.drop_column('campus_id')
