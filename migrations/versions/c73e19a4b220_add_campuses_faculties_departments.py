"""add_campuses_faculties_departments

Revision ID: c73e19a4b220
Revises: 55d145cb785e
Create Date: 2026-11-21 05:25:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c73e19a4b220'
down_revision: Union[str, None] = '55d145cb785e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create campuses table
    op.create_table(
        'campuses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('institution_id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('address', sa.String(length=255), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=100), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=False, server_default='Sri Lanka'),
        sa.Column('contact_email', sa.String(length=255), nullable=True),
        sa.Column('contact_phone', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], name=op.f('fk_campuses_institution_id_institutions'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_campuses'))
    )
    with op.batch_alter_table('campuses', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_campuses_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_campuses_institution_id'), ['institution_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_campuses_code'), ['code'], unique=False)

    # 2. Create faculties table
    op.create_table(
        'faculties',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('institution_id', sa.Integer(), nullable=False),
        sa.Column('campus_id', sa.Integer(), nullable=True),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('dean_name', sa.String(length=255), nullable=True),
        sa.Column('contact_email', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], name=op.f('fk_faculties_institution_id_institutions'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['campus_id'], ['campuses.id'], name=op.f('fk_faculties_campus_id_campuses'), ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_faculties'))
    )
    with op.batch_alter_table('faculties', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_faculties_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_faculties_institution_id'), ['institution_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_faculties_campus_id'), ['campus_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_faculties_code'), ['code'], unique=False)

    # 3. Create departments table
    op.create_table(
        'departments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('institution_id', sa.Integer(), nullable=False),
        sa.Column('faculty_id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('head_of_department', sa.String(length=255), nullable=True),
        sa.Column('contact_email', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], name=op.f('fk_departments_institution_id_institutions'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['faculty_id'], ['faculties.id'], name=op.f('fk_departments_faculty_id_faculties'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_departments'))
    )
    with op.batch_alter_table('departments', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_departments_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_departments_institution_id'), ['institution_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_departments_faculty_id'), ['faculty_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_departments_code'), ['code'], unique=False)


def downgrade() -> None:
    op.drop_table('departments')
    op.drop_table('faculties')
    op.drop_table('campuses')
