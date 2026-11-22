"""add hostel and accommodation management

Revision ID: o56a7b8c9d0e
Revises: n45f6a7b8c9d
Create Date: 2026-11-22 11:05:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'o56a7b8c9d0e'
down_revision = 'n45f6a7b8c9d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. hostel_buildings
    op.create_table(
        'hostel_buildings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('gender_type', sa.String(length=20), nullable=False, server_default='mixed'),
        sa.Column('total_floors', sa.Integer(), nullable=False, server_default='4'),
        sa.Column('warden_name', sa.String(length=150), nullable=False),
        sa.Column('warden_contact', sa.String(length=100), nullable=False),
        sa.Column('campus_location', sa.String(length=200), nullable=False),
        sa.Column('amenities', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_hostel_buildings_id'), 'hostel_buildings', ['id'], unique=False)
    op.create_index(op.f('ix_hostel_buildings_name'), 'hostel_buildings', ['name'], unique=True)
    op.create_index(op.f('ix_hostel_buildings_code'), 'hostel_buildings', ['code'], unique=True)

    # 2. hostel_rooms
    op.create_table(
        'hostel_rooms',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('building_id', sa.Integer(), nullable=False),
        sa.Column('room_number', sa.String(length=50), nullable=False),
        sa.Column('floor', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('room_type', sa.String(length=30), nullable=False, server_default='double'),
        sa.Column('capacity', sa.Integer(), nullable=False, server_default='2'),
        sa.Column('occupied_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('monthly_fee', sa.Float(), nullable=False, server_default='15000.0'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='available'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['building_id'], ['hostel_buildings.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_hostel_rooms_id'), 'hostel_rooms', ['id'], unique=False)
    op.create_index(op.f('ix_hostel_rooms_building_id'), 'hostel_rooms', ['building_id'], unique=False)
    op.create_index(op.f('ix_hostel_rooms_room_number'), 'hostel_rooms', ['room_number'], unique=False)

    # 3. hostel_allocations
    op.create_table(
        'hostel_allocations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('room_id', sa.Integer(), nullable=False),
        sa.Column('academic_year', sa.String(length=30), nullable=False),
        sa.Column('semester', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('check_in_date', sa.Date(), nullable=False),
        sa.Column('check_out_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='active'),
        sa.Column('deposit_paid', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('emergency_contact', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['room_id'], ['hostel_rooms.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_hostel_allocations_id'), 'hostel_allocations', ['id'], unique=False)
    op.create_index(op.f('ix_hostel_allocations_student_id'), 'hostel_allocations', ['student_id'], unique=False)
    op.create_index(op.f('ix_hostel_allocations_room_id'), 'hostel_allocations', ['room_id'], unique=False)

    # 4. hostel_maintenance_requests
    op.create_table(
        'hostel_maintenance_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('room_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('issue_type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('priority', sa.String(length=20), nullable=False, server_default='medium'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='reported'),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('reported_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['room_id'], ['hostel_rooms.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_hostel_maintenance_requests_id'), 'hostel_maintenance_requests', ['id'], unique=False)
    op.create_index(op.f('ix_hostel_maintenance_requests_room_id'), 'hostel_maintenance_requests', ['room_id'], unique=False)
    op.create_index(op.f('ix_hostel_maintenance_requests_student_id'), 'hostel_maintenance_requests', ['student_id'], unique=False)


def downgrade() -> None:
    op.drop_table('hostel_maintenance_requests')
    op.drop_table('hostel_allocations')
    op.drop_table('hostel_rooms')
    op.drop_table('hostel_buildings')
