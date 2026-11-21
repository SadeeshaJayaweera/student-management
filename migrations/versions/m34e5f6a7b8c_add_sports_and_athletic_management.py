"""add_sports_and_athletic_management

Revision ID: m34e5f6a7b8c
Revises: l23d4e5f6a7b
Create Date: 2026-11-22 00:03:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'm34e5f6a7b8c'
down_revision = 'l23d4e5f6a7b'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'athletic_teams',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('name', sa.String(length=200), nullable=False, index=True),
        sa.Column('sport_type', sa.String(length=60), nullable=False, index=True),
        sa.Column('coach_name', sa.String(length=200), nullable=True),
        sa.Column('captain_name', sa.String(length=200), nullable=True),
        sa.Column('division', sa.String(length=60), nullable=False, server_default='Division 1'),
        sa.Column('home_venue', sa.String(length=200), nullable=True),
        sa.Column('logo_url', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        'athlete_profiles',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('team_id', sa.Integer(), sa.ForeignKey('athletic_teams.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('jersey_number', sa.Integer(), nullable=True),
        sa.Column('position_or_role', sa.String(length=100), nullable=False),
        sa.Column('fitness_status', sa.String(length=30), nullable=False, server_default='fit'),
        sa.Column('matches_played', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('points_or_goals', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('mvp_awards', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('joined_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        'sports_fixtures',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('team_id', sa.Integer(), sa.ForeignKey('athletic_teams.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('tournament_name', sa.String(length=255), nullable=False, index=True),
        sa.Column('opponent_name', sa.String(length=255), nullable=False),
        sa.Column('scheduled_time', sa.DateTime(), nullable=False, index=True),
        sa.Column('venue', sa.String(length=200), nullable=False),
        sa.Column('fixture_type', sa.String(length=50), nullable=False, server_default='tournament'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='upcoming'),
        sa.Column('our_score', sa.String(length=50), nullable=True),
        sa.Column('opponent_score', sa.String(length=50), nullable=True),
        sa.Column('match_result', sa.String(length=30), nullable=True),
        sa.Column('highlights', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        'sports_facility_bookings',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('facility_name', sa.String(length=150), nullable=False, index=True),
        sa.Column('booked_by_user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('team_id', sa.Integer(), sa.ForeignKey('athletic_teams.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('start_time', sa.DateTime(), nullable=False, index=True),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('purpose', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='confirmed'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def downgrade():
    op.drop_table('sports_facility_bookings')
    op.drop_table('sports_fixtures')
    op.drop_table('athlete_profiles')
    op.drop_table('athletic_teams')
