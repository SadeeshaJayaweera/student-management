"""add campus facility and resource booking

Revision ID: q78c9d0e1f2a
Revises: p67b8c9d0e1f
Create Date: 2026-11-22 20:14:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'q78c9d0e1f2a'
down_revision = 'p67b8c9d0e1f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. campus_facilities
    op.create_table(
        'campus_facilities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('facility_code', sa.String(length=50), nullable=False),
        sa.Column('facility_type', sa.String(length=50), nullable=False, server_default='lecture_hall'),
        sa.Column('building_name', sa.String(length=150), nullable=False),
        sa.Column('floor', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('capacity', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('hourly_rate', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('amenities', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_campus_facilities_id'), 'campus_facilities', ['id'], unique=False)
    op.create_index(op.f('ix_campus_facilities_name'), 'campus_facilities', ['name'], unique=False)
    op.create_index(op.f('ix_campus_facilities_facility_code'), 'campus_facilities', ['facility_code'], unique=True)

    # 2. facility_equipment
    op.create_table(
        'facility_equipment',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('facility_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('asset_tag', sa.String(length=50), nullable=False),
        sa.Column('equipment_type', sa.String(length=50), nullable=False, server_default='av_projector'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='available'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['facility_id'], ['campus_facilities.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_facility_equipment_id'), 'facility_equipment', ['id'], unique=False)
    op.create_index(op.f('ix_facility_equipment_facility_id'), 'facility_equipment', ['facility_id'], unique=False)
    op.create_index(op.f('ix_facility_equipment_asset_tag'), 'facility_equipment', ['asset_tag'], unique=True)

    # 3. facility_reservations
    op.create_table(
        'facility_reservations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('facility_id', sa.Integer(), nullable=False),
        sa.Column('reserved_by_user_id', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('purpose', sa.String(length=255), nullable=False),
        sa.Column('attendee_count', sa.Integer(), nullable=False, server_default='20'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='confirmed'),
        sa.Column('approval_notes', sa.Text(), nullable=True),
        sa.Column('equipment_requested', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['facility_id'], ['campus_facilities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reserved_by_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_facility_reservations_id'), 'facility_reservations', ['id'], unique=False)
    op.create_index(op.f('ix_facility_reservations_facility_id'), 'facility_reservations', ['facility_id'], unique=False)
    op.create_index(op.f('ix_facility_reservations_reserved_by_user_id'), 'facility_reservations', ['reserved_by_user_id'], unique=False)
    op.create_index(op.f('ix_facility_reservations_start_time'), 'facility_reservations', ['start_time'], unique=False)
    op.create_index(op.f('ix_facility_reservations_end_time'), 'facility_reservations', ['end_time'], unique=False)


def downgrade() -> None:
    op.drop_table('facility_reservations')
    op.drop_table('facility_equipment')
    op.drop_table('campus_facilities')
