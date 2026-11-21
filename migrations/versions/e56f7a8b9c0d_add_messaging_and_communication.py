"""add_messaging_and_communication

Revision ID: e56f7a8b9c0d
Revises: d45e6f7a8b9c
Create Date: 2026-11-21 20:18:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e56f7a8b9c0d'
down_revision = 'd45e6f7a8b9c'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'conversations',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('subject', sa.String(length=255), nullable=True),
        sa.Column('thread_type', sa.String(length=50), nullable=False, server_default='direct'),
        sa.Column('course_id', sa.Integer(), sa.ForeignKey('courses.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('last_message_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
    )

    op.create_table(
        'conversation_participants',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('conversation_id', sa.Integer(), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('last_read_at', sa.DateTime(), nullable=True),
        sa.Column('is_muted', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('joined_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    )

    with op.batch_alter_table('messages') as batch_op:
        batch_op.add_column(sa.Column('conversation_id', sa.Integer(), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=True))
        batch_op.add_column(sa.Column('subject', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('attachment_url', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('attachment_name', sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column('read_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('is_moderated', sa.Boolean(), nullable=False, server_default=sa.text('0')))
        batch_op.add_column(sa.Column('moderation_flag', sa.String(length=50), nullable=True))
        batch_op.alter_column('receiver_id', existing_type=sa.Integer(), nullable=True)


def downgrade():
    with op.batch_alter_table('messages') as batch_op:
        batch_op.alter_column('receiver_id', existing_type=sa.Integer(), nullable=False)
        batch_op.drop_column('moderation_flag')
        batch_op.drop_column('is_moderated')
        batch_op.drop_column('read_at')
        batch_op.drop_column('attachment_name')
        batch_op.drop_column('attachment_url')
        batch_op.drop_column('subject')
        batch_op.drop_column('conversation_id')

    op.drop_table('conversation_participants')
    op.drop_table('conversations')
