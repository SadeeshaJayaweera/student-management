"""add_class_cohorts_and_groups

Revision ID: d93c4e5f6a7b
Revises: c82b3d4e5f6a
Create Date: 2026-11-21 11:42:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd93c4e5f6a7b'
down_revision = 'c82b3d4e5f6a'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'cohorts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('institution_id', sa.Integer(), nullable=False),
        sa.Column('program_id', sa.Integer(), nullable=True),
        sa.Column('academic_year_id', sa.Integer(), nullable=True),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('year_of_study', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('semester_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('max_capacity', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['academic_year_id'], ['academic_years.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['program_id'], ['programs.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('cohorts', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_cohorts_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_cohorts_code'), ['code'], unique=False)
        batch_op.create_index(batch_op.f('ix_cohorts_institution_id'), ['institution_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_cohorts_program_id'), ['program_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_cohorts_academic_year_id'), ['academic_year_id'], unique=False)

    op.create_table(
        'cohort_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cohort_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=30), nullable=False, server_default='student'),
        sa.Column('joined_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.ForeignKeyConstraint(['cohort_id'], ['cohorts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('cohort_members', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_cohort_members_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_cohort_members_cohort_id'), ['cohort_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_cohort_members_student_id'), ['student_id'], unique=False)

    op.create_table(
        'student_groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('institution_id', sa.Integer(), nullable=False),
        sa.Column('cohort_id', sa.Integer(), nullable=True),
        sa.Column('course_id', sa.Integer(), nullable=True),
        sa.Column('group_type', sa.String(length=50), nullable=False, server_default='tutorial'),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('max_capacity', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('mentor_lecturer_id', sa.Integer(), nullable=True),
        sa.Column('schedule_info', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['cohort_id'], ['cohorts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['mentor_lecturer_id'], ['lecturers.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('student_groups', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_student_groups_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_student_groups_institution_id'), ['institution_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_student_groups_cohort_id'), ['cohort_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_student_groups_course_id'), ['course_id'], unique=False)

    op.create_table(
        'student_group_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('group_role', sa.String(length=30), nullable=False, server_default='member'),
        sa.Column('joined_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['group_id'], ['student_groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('student_group_members', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_student_group_members_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_student_group_members_group_id'), ['group_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_student_group_members_student_id'), ['student_id'], unique=False)


def downgrade():
    op.drop_table('student_group_members')
    op.drop_table('student_groups')
    op.drop_table('cohort_members')
    op.drop_table('cohorts')
