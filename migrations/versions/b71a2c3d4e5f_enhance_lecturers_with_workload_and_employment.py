"""enhance_lecturers_with_workload_and_employment

Revision ID: b71a2c3d4e5f
Revises: 8912d37c4e51
Create Date: 2026-11-21 11:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b71a2c3d4e5f'
down_revision = '8912d37c4e51'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('lecturers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('institution_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('campus_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('faculty_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('department_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('employment_status', sa.String(length=50), nullable=False, server_default='full_time'))
        batch_op.add_column(sa.Column('designation', sa.String(length=100), nullable=False, server_default='Lecturer'))
        batch_op.add_column(sa.Column('max_teaching_load_hours', sa.Integer(), nullable=False, server_default='15'))
        batch_op.add_column(sa.Column('current_teaching_load_hours', sa.Integer(), nullable=False, server_default='0'))
        batch_op.create_index(batch_op.f('ix_lecturers_institution_id'), ['institution_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_lecturers_campus_id'), ['campus_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_lecturers_faculty_id'), ['faculty_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_lecturers_department_id'), ['department_id'], unique=False)
        batch_op.create_foreign_key('fk_lecturers_institution_id', 'institutions', ['institution_id'], ['id'], ondelete='CASCADE')
        batch_op.create_foreign_key('fk_lecturers_campus_id', 'campuses', ['campus_id'], ['id'], ondelete='SET NULL')
        batch_op.create_foreign_key('fk_lecturers_faculty_id', 'faculties', ['faculty_id'], ['id'], ondelete='SET NULL')
        batch_op.create_foreign_key('fk_lecturers_department_id', 'departments', ['department_id'], ['id'], ondelete='SET NULL')


def downgrade():
    with op.batch_alter_table('lecturers', schema=None) as batch_op:
        batch_op.drop_constraint('fk_lecturers_department_id', type_='foreignkey')
        batch_op.drop_constraint('fk_lecturers_faculty_id', type_='foreignkey')
        batch_op.drop_constraint('fk_lecturers_campus_id', type_='foreignkey')
        batch_op.drop_constraint('fk_lecturers_institution_id', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_lecturers_department_id'))
        batch_op.drop_index(batch_op.f('ix_lecturers_faculty_id'))
        batch_op.drop_index(batch_op.f('ix_lecturers_campus_id'))
        batch_op.drop_index(batch_op.f('ix_lecturers_institution_id'))
        batch_op.drop_column('current_teaching_load_hours')
        batch_op.drop_column('max_teaching_load_hours')
        batch_op.drop_column('designation')
        batch_op.drop_column('employment_status')
        batch_op.drop_column('department_id')
        batch_op.drop_column('faculty_id')
        batch_op.drop_column('campus_id')
        batch_op.drop_column('institution_id')
