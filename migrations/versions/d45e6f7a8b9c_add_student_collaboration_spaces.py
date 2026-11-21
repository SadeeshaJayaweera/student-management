"""add_student_collaboration_spaces

Revision ID: d45e6f7a8b9c
Revises: c34d5e6f7a8b
Create Date: 2026-11-21 20:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd45e6f7a8b9c'
down_revision = 'c34d5e6f7a8b'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'collaboration_workspaces',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('course_id', sa.Integer(), sa.ForeignKey('courses.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('topic', sa.String(length=150), nullable=True),
        sa.Column('visibility', sa.String(length=30), nullable=False, server_default='course_public'),
        sa.Column('owner_student_id', sa.Integer(), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('join_code', sa.String(length=12), nullable=False, unique=True, index=True),
        sa.Column('shared_whiteboard_data', sa.JSON(), nullable=True),
        sa.Column('meeting_link', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
    )

    op.create_table(
        'collaboration_workspace_members',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('collaboration_workspaces.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('role', sa.String(length=30), nullable=False, server_default='collaborator'),
        sa.Column('joined_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    )

    op.create_table(
        'collaboration_workspace_assets',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('collaboration_workspaces.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('created_by_student_id', sa.Integer(), sa.ForeignKey('students.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('asset_type', sa.String(length=50), nullable=False, server_default='note'),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
    )

    op.create_table(
        'collaboration_workspace_messages',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('collaboration_workspaces.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('sender_student_id', sa.Integer(), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('pinned', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    )


def downgrade():
    op.drop_table('collaboration_workspace_messages')
    op.drop_table('collaboration_workspace_assets')
    op.drop_table('collaboration_workspace_members')
    op.drop_table('collaboration_workspaces')
