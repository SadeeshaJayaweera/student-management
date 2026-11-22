"""add transport and shuttle management

Revision ID: p67b8c9d0e1f
Revises: o56a7b8c9d0e
Create Date: 2026-11-22 19:55:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'p67b8c9d0e1f'
down_revision = 'o56a7b8c9d0e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. transport_vehicles
    op.create_table(
        'transport_vehicles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vehicle_number', sa.String(length=50), nullable=False),
        sa.Column('vehicle_type', sa.String(length=30), nullable=False, server_default='bus'),
        sa.Column('capacity', sa.Integer(), nullable=False, server_default='54'),
        sa.Column('driver_name', sa.String(length=150), nullable=False),
        sa.Column('driver_contact', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='active'),
        sa.Column('current_lat', sa.Float(), nullable=True),
        sa.Column('current_lng', sa.Float(), nullable=True),
        sa.Column('last_telemetry_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_transport_vehicles_id'), 'transport_vehicles', ['id'], unique=False)
    op.create_index(op.f('ix_transport_vehicles_vehicle_number'), 'transport_vehicles', ['vehicle_number'], unique=True)

    # 2. shuttle_routes
    op.create_table(
        'shuttle_routes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('route_name', sa.String(length=150), nullable=False),
        sa.Column('route_code', sa.String(length=50), nullable=False),
        sa.Column('origin', sa.String(length=150), nullable=False),
        sa.Column('destination', sa.String(length=150), nullable=False),
        sa.Column('distance_km', sa.Float(), nullable=False, server_default='25.0'),
        sa.Column('estimated_duration_mins', sa.Integer(), nullable=False, server_default='45'),
        sa.Column('fare_amount', sa.Float(), nullable=False, server_default='150.0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_shuttle_routes_id'), 'shuttle_routes', ['id'], unique=False)
    op.create_index(op.f('ix_shuttle_routes_route_name'), 'shuttle_routes', ['route_name'], unique=False)
    op.create_index(op.f('ix_shuttle_routes_route_code'), 'shuttle_routes', ['route_code'], unique=True)

    # 3. shuttle_stops
    op.create_table(
        'shuttle_stops',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('route_id', sa.Integer(), nullable=False),
        sa.Column('stop_name', sa.String(length=150), nullable=False),
        sa.Column('stop_order', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('estimated_time_offset_mins', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['route_id'], ['shuttle_routes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_shuttle_stops_id'), 'shuttle_stops', ['id'], unique=False)
    op.create_index(op.f('ix_shuttle_stops_route_id'), 'shuttle_stops', ['route_id'], unique=False)

    # 4. shuttle_schedules
    op.create_table(
        'shuttle_schedules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('route_id', sa.Integer(), nullable=False),
        sa.Column('vehicle_id', sa.Integer(), nullable=True),
        sa.Column('departure_time', sa.String(length=10), nullable=False),
        sa.Column('arrival_time', sa.String(length=10), nullable=False),
        sa.Column('days_of_week', sa.JSON(), nullable=True),
        sa.Column('shift_type', sa.String(length=30), nullable=False, server_default='morning_inbound'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['route_id'], ['shuttle_routes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['vehicle_id'], ['transport_vehicles.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_shuttle_schedules_id'), 'shuttle_schedules', ['id'], unique=False)
    op.create_index(op.f('ix_shuttle_schedules_route_id'), 'shuttle_schedules', ['route_id'], unique=False)
    op.create_index(op.f('ix_shuttle_schedules_vehicle_id'), 'shuttle_schedules', ['vehicle_id'], unique=False)

    # 5. student_transport_passes
    op.create_table(
        'student_transport_passes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('route_id', sa.Integer(), nullable=False),
        sa.Column('pass_type', sa.String(length=30), nullable=False, server_default='semester'),
        sa.Column('valid_from', sa.Date(), nullable=False),
        sa.Column('valid_until', sa.Date(), nullable=False),
        sa.Column('qr_code_token', sa.String(length=100), nullable=False),
        sa.Column('fare_paid', sa.Float(), nullable=False, server_default='12000.0'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['route_id'], ['shuttle_routes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_student_transport_passes_id'), 'student_transport_passes', ['id'], unique=False)
    op.create_index(op.f('ix_student_transport_passes_student_id'), 'student_transport_passes', ['student_id'], unique=False)
    op.create_index(op.f('ix_student_transport_passes_route_id'), 'student_transport_passes', ['route_id'], unique=False)
    op.create_index(op.f('ix_student_transport_passes_qr_code_token'), 'student_transport_passes', ['qr_code_token'], unique=True)


def downgrade() -> None:
    op.drop_table('student_transport_passes')
    op.drop_table('shuttle_schedules')
    op.drop_table('shuttle_stops')
    op.drop_table('shuttle_routes')
    op.drop_table('transport_vehicles')
