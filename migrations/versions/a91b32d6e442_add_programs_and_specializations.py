"""add_programs_and_specializations

Revision ID: a91b32d6e442
Revises: e84f21b5c331
Create Date: 2026-11-21 05:40:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a91b32d6e442'
down_revision: Union[str, None] = 'e84f21b5c331'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create programs table
    op.create_table(
        'programs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('institution_id', sa.Integer(), nullable=False),
        sa.Column('faculty_id', sa.Integer(), nullable=True),
        sa.Column('department_id', sa.Integer(), nullable=True),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('qualification', sa.String(length=50), nullable=False, server_default='BSc'),
        sa.Column('duration_years', sa.Float(), nullable=False, server_default='4.0'),
        sa.Column('total_credits', sa.Integer(), nullable=False, server_default='120'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], name=op.f('fk_programs_institution_id_institutions'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['faculty_id'], ['faculties.id'], name=op.f('fk_programs_faculty_id_faculties'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], name=op.f('fk_programs_department_id_departments'), ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_programs'))
    )
    with op.batch_alter_table('programs', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_programs_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_programs_institution_id'), ['institution_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_programs_faculty_id'), ['faculty_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_programs_department_id'), ['department_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_programs_code'), ['code'], unique=False)

    # 2. Create specializations table
    op.create_table(
        'specializations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('institution_id', sa.Integer(), nullable=False),
        sa.Column('program_id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('required_credits', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], name=op.f('fk_specializations_institution_id_institutions'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['program_id'], ['programs.id'], name=op.f('fk_specializations_program_id_programs'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_specializations'))
    )
    with op.batch_alter_table('specializations', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_specializations_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_specializations_institution_id'), ['institution_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_specializations_program_id'), ['program_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_specializations_code'), ['code'], unique=False)


def downgrade() -> None:
    op.drop_table('specializations')
    op.drop_table('programs')
