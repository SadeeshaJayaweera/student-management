"""add_advanced_notification_center

Revision ID: f67a8b9c0d1e
Revises: e56f7a8b9c0d
Create Date: 2026-11-21 20:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f67a8b9c0d1e'
down_revision = 'e56f7a8b9c0d'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Add columns to notifications table if table exists
    with op.batch_alter_table('notifications', schema=None) as batch_op:
        batch_op.add_column(sa.Column('category', sa.String(length=50), nullable=False, server_default='general'))
        batch_op.add_column(sa.Column('priority', sa.String(length=20), nullable=False, server_default='normal'))
        batch_op.add_column(sa.Column('read_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('expires_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('extra_data', sa.JSON(), nullable=True))
        batch_op.create_index(batch_op.f('ix_notifications_category'), ['category'], unique=False)
        batch_op.create_index(batch_op.f('ix_notifications_is_read'), ['is_read'], unique=False)

    # 2. Create notification_preferences table
    op.create_table(
        'notification_preferences',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True, index=True),
        sa.Column('email_enabled', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('in_app_enabled', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('push_enabled', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('sms_enabled', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('notify_academic', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('notify_deadlines', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('notify_announcements', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('notify_messages', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('notify_grades', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('quiet_hours_enabled', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('quiet_hours_start', sa.String(length=10), nullable=True),
        sa.Column('quiet_hours_end', sa.String(length=10), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def downgrade():
    op.drop_table('notification_preferences')
    with op.batch_alter_table('notifications', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_notifications_is_read'))
        batch_op.drop_index(batch_op.f('ix_notifications_category'))
        batch_op.drop_column('extra_data')
        batch_op.drop_column('expires_at')
        batch_op.drop_column('read_at')
        batch_op.drop_column('priority')
        batch_op.drop_column('category')
