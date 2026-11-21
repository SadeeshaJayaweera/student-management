"""add_academic_records_and_transcripts

Revision ID: f15e6a7b8c9d
Revises: e04d5f6a7b8c
Create Date: 2026-11-21 11:57:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f15e6a7b8c9d'
down_revision = 'e04d5f6a7b8c'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('grades', schema=None) as batch_op:
        batch_op.add_column(sa.Column('semester_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('credits_earned', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('is_final', sa.Boolean(), nullable=False, server_default='0'))
        batch_op.create_index(batch_op.f('ix_grades_semester_id'), ['semester_id'], unique=False)
        batch_op.create_foreign_key('fk_grades_semester_id', 'semesters', ['semester_id'], ['id'], ondelete='SET NULL')

    op.create_table(
        'academic_term_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('institution_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('semester_id', sa.Integer(), nullable=False),
        sa.Column('term_gpa', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('cgpa', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('credits_attempted', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('credits_earned', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('cumulative_credits_attempted', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('cumulative_credits_earned', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('academic_standing', sa.String(length=50), nullable=False, server_default='good_standing'),
        sa.Column('is_finalized', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('finalized_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['semester_id'], ['semesters.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('academic_term_records', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_academic_term_records_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_academic_term_records_institution_id'), ['institution_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_academic_term_records_student_id'), ['student_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_academic_term_records_semester_id'), ['semester_id'], unique=False)

    op.create_table(
        'official_transcripts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('institution_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('verification_code', sa.String(length=64), nullable=False),
        sa.Column('digital_signature_hash', sa.String(length=128), nullable=False),
        sa.Column('issue_type', sa.String(length=30), nullable=False, server_default='official'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='valid'),
        sa.Column('issued_by_id', sa.Integer(), nullable=True),
        sa.Column('issued_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('recipient_name', sa.String(length=200), nullable=True),
        sa.Column('recipient_email', sa.String(length=255), nullable=True),
        sa.Column('data_snapshot', sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['issued_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('official_transcripts', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_official_transcripts_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_official_transcripts_verification_code'), ['verification_code'], unique=True)
        batch_op.create_index(batch_op.f('ix_official_transcripts_institution_id'), ['institution_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_official_transcripts_student_id'), ['student_id'], unique=False)


def downgrade():
    op.drop_table('official_transcripts')
    op.drop_table('academic_term_records')
    with op.batch_alter_table('grades', schema=None) as batch_op:
        batch_op.drop_constraint('fk_grades_semester_id', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_grades_semester_id'))
        batch_op.drop_column('is_final')
        batch_op.drop_column('credits_earned')
        batch_op.drop_column('semester_id')
