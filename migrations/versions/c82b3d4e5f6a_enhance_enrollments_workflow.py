"""enhance_enrollments_workflow

Revision ID: c82b3d4e5f6a
Revises: b71a2c3d4e5f
Create Date: 2026-11-21 11:36:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c82b3d4e5f6a'
down_revision = 'b71a2c3d4e5f'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('enrollments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('institution_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('semester_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('waitlist_position', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('registration_type', sa.String(length=30), nullable=False, server_default='regular'))
        batch_op.add_column(sa.Column('approved_by_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('approved_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('dropped_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('rejection_reason', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('remarks', sa.Text(), nullable=True))
        batch_op.create_index(batch_op.f('ix_enrollments_institution_id'), ['institution_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_enrollments_semester_id'), ['semester_id'], unique=False)
        batch_op.create_foreign_key('fk_enrollments_institution_id', 'institutions', ['institution_id'], ['id'], ondelete='CASCADE')
        batch_op.create_foreign_key('fk_enrollments_semester_id', 'semesters', ['semester_id'], ['id'], ondelete='SET NULL')
        batch_op.create_foreign_key('fk_enrollments_approved_by_id', 'users', ['approved_by_id'], ['id'], ondelete='SET NULL')


def downgrade():
    with op.batch_alter_table('enrollments', schema=None) as batch_op:
        batch_op.drop_constraint('fk_enrollments_approved_by_id', type_='foreignkey')
        batch_op.drop_constraint('fk_enrollments_semester_id', type_='foreignkey')
        batch_op.drop_constraint('fk_enrollments_institution_id', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_enrollments_semester_id'))
        batch_op.drop_index(batch_op.f('ix_enrollments_institution_id'))
        batch_op.drop_column('remarks')
        batch_op.drop_column('rejection_reason')
        batch_op.drop_column('dropped_at')
        batch_op.drop_column('approved_at')
        batch_op.drop_column('approved_by_id')
        batch_op.drop_column('registration_type')
        batch_op.drop_column('waitlist_position')
        batch_op.drop_column('semester_id')
        batch_op.drop_column('institution_id')
