"""add_academic_years_and_semesters

Revision ID: e84f21b5c331
Revises: c73e19a4b220
Create Date: 2026-11-21 05:35:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e84f21b5c331'
down_revision: Union[str, None] = 'c73e19a4b220'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create academic_years table
    op.create_table(
        'academic_years',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('institution_id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('is_current', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], name=op.f('fk_academic_years_institution_id_institutions'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_academic_years'))
    )
    with op.batch_alter_table('academic_years', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_academic_years_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_academic_years_institution_id'), ['institution_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_academic_years_code'), ['code'], unique=False)

    # 2. Create semesters table
    op.create_table(
        'semesters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('institution_id', sa.Integer(), nullable=False),
        sa.Column('academic_year_id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('term_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('census_date', sa.Date(), nullable=True),
        sa.Column('registration_start_date', sa.Date(), nullable=True),
        sa.Column('registration_end_date', sa.Date(), nullable=True),
        sa.Column('add_drop_deadline', sa.Date(), nullable=True),
        sa.Column('exam_start_date', sa.Date(), nullable=True),
        sa.Column('exam_end_date', sa.Date(), nullable=True),
        sa.Column('is_current', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], name=op.f('fk_semesters_institution_id_institutions'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['academic_year_id'], ['academic_years.id'], name=op.f('fk_semesters_academic_year_id_academic_years'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_semesters'))
    )
    with op.batch_alter_table('semesters', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_semesters_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_semesters_institution_id'), ['institution_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_semesters_academic_year_id'), ['academic_year_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_semesters_code'), ['code'], unique=False)


def downgrade() -> None:
    op.drop_table('semesters')
    op.drop_table('academic_years')
