"""add_academic_advising_and_support

Revision ID: e04d5f6a7b8c
Revises: d93c4e5f6a7b
Create Date: 2026-11-21 11:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e04d5f6a7b8c'
down_revision = 'd93c4e5f6a7b'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'academic_advisor_assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('institution_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('lecturer_id', sa.Integer(), nullable=False),
        sa.Column('assigned_date', sa.Date(), nullable=False, server_default=sa.func.current_date()),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('advising_type', sa.String(length=50), nullable=False, server_default='academic'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['lecturer_id'], ['lecturers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('academic_advisor_assignments', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_academic_advisor_assignments_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_academic_advisor_assignments_institution_id'), ['institution_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_academic_advisor_assignments_student_id'), ['student_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_academic_advisor_assignments_lecturer_id'), ['lecturer_id'], unique=False)

    op.create_table(
        'advising_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('institution_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('lecturer_id', sa.Integer(), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('session_type', sa.String(length=50), nullable=False, server_default='one_on_one'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='scheduled'),
        sa.Column('topic', sa.String(length=200), nullable=False),
        sa.Column('student_notes', sa.Text(), nullable=True),
        sa.Column('confidential_notes', sa.Text(), nullable=True),
        sa.Column('action_items', sa.JSON(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['lecturer_id'], ['lecturers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('advising_sessions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_advising_sessions_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_advising_sessions_institution_id'), ['institution_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_advising_sessions_student_id'), ['student_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_advising_sessions_lecturer_id'), ['lecturer_id'], unique=False)

    op.create_table(
        'student_support_cases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('institution_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('assigned_staff_id', sa.Integer(), nullable=True),
        sa.Column('case_number', sa.String(length=50), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False, server_default='academic_probation'),
        sa.Column('priority', sa.String(length=20), nullable=False, server_default='medium'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='open'),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('resolution_summary', sa.Text(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['assigned_staff_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('student_support_cases', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_student_support_cases_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_student_support_cases_case_number'), ['case_number'], unique=True)
        batch_op.create_index(batch_op.f('ix_student_support_cases_institution_id'), ['institution_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_student_support_cases_student_id'), ['student_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_student_support_cases_assigned_staff_id'), ['assigned_staff_id'], unique=False)

    op.create_table(
        'support_case_notes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('case_id', sa.Integer(), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=True),
        sa.Column('is_confidential', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['case_id'], ['student_support_cases.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('support_case_notes', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_support_case_notes_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_case_notes_case_id'), ['case_id'], unique=False)


def downgrade():
    op.drop_table('support_case_notes')
    op.drop_table('student_support_cases')
    op.drop_table('advising_sessions')
    op.drop_table('academic_advisor_assignments')
