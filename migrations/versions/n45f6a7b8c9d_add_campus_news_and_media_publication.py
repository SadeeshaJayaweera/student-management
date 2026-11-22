"""add_campus_news_and_media_publication

Revision ID: n45f6a7b8c9d
Revises: m34e5f6a7b8c
Create Date: 2026-11-22 00:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'n45f6a7b8c9d'
down_revision = 'm34e5f6a7b8c'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('news', sa.Column('status', sa.String(length=30), nullable=False, server_default='published'))
    op.add_column('news', sa.Column('editorial_notes', sa.Text(), nullable=True))
    op.add_column('news', sa.Column('likes_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('news', sa.Column('target_audience', sa.String(length=30), nullable=False, server_default='all'))
    op.add_column('news', sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False))

    op.create_table(
        'media_gallery_items',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('news_id', sa.Integer(), sa.ForeignKey('news.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('media_type', sa.String(length=30), nullable=False, server_default='image'),
        sa.Column('media_url', sa.String(length=500), nullable=False),
        sa.Column('caption', sa.String(length=300), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        'news_reactions',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('news_id', sa.Integer(), sa.ForeignKey('news.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('reaction_type', sa.String(length=30), nullable=False, server_default='like'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def downgrade():
    op.drop_table('news_reactions')
    op.drop_table('media_gallery_items')
    op.drop_column('news', 'updated_at')
    op.drop_column('news', 'target_audience')
    op.drop_column('news', 'likes_count')
    op.drop_column('news', 'editorial_notes')
    op.drop_column('news', 'status')
