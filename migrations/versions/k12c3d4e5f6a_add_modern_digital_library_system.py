"""add_modern_digital_library_system

Revision ID: k12c3d4e5f6a
Revises: j01b2c3d4e5f
Create Date: 2026-11-21 23:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'k12c3d4e5f6a'
down_revision = 'j01b2c3d4e5f'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'library_subject_collections',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('slug', sa.String(length=200), unique=True, index=True, nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(length=50), nullable=False, server_default='📚'),
        sa.Column('is_featured', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        'digital_library_resources',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('book_id', sa.Integer(), sa.ForeignKey('books.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('title', sa.String(length=350), nullable=False, index=True),
        sa.Column('author', sa.String(length=300), nullable=False, index=True),
        sa.Column('resource_type', sa.String(length=50), nullable=False, server_default='ebook'),
        sa.Column('doi_or_issn', sa.String(length=100), nullable=True, index=True),
        sa.Column('subject_category', sa.String(length=100), nullable=False, server_default='General', index=True),
        sa.Column('file_format', sa.String(length=20), nullable=False, server_default='pdf'),
        sa.Column('file_url', sa.String(length=500), nullable=False),
        sa.Column('cover_url', sa.String(length=500), nullable=True),
        sa.Column('file_size_bytes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('download_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('view_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('abstract', sa.Text(), nullable=True),
        sa.Column('keywords', sa.String(length=300), nullable=True),
        sa.Column('is_open_access', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('published_year', sa.Integer(), nullable=True),
        sa.Column('publisher', sa.String(length=200), nullable=True),
        sa.Column('collection_id', sa.Integer(), sa.ForeignKey('library_subject_collections.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        'library_resource_bookmarks',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('resource_id', sa.Integer(), sa.ForeignKey('digital_library_resources.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def downgrade():
    op.drop_table('library_resource_bookmarks')
    op.drop_table('digital_library_resources')
    op.drop_table('library_subject_collections')
