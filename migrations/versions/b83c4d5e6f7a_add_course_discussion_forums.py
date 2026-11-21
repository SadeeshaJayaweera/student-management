"""add_course_discussion_forums

Revision ID: b83c4d5e6f7a
Revises: a72b3c4d5e6f
Create Date: 2026-11-21 13:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b83c4d5e6f7a'
down_revision = 'a72b3c4d5e6f'
branch_labels = None
depends_on = None


def upgrade():
    # 1. course_forum_categories
    op.create_table(
        'course_forum_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_locked', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('course_forum_categories', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_course_forum_categories_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_course_forum_categories_course_id'), ['course_id'], unique=False)

    # 2. forum_threads
    op.create_table(
        'forum_threads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_pinned', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('is_locked', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('view_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('reply_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['course_forum_categories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('forum_threads', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_forum_threads_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_forum_threads_course_id'), ['course_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_forum_threads_category_id'), ['category_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_forum_threads_author_id'), ['author_id'], unique=False)

    # 3. forum_posts
    op.create_table(
        'forum_posts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('thread_id', sa.Integer(), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.Column('parent_post_id', sa.Integer(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_endorsed_by_instructor', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('is_solution', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('upvotes', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_post_id'], ['forum_posts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['thread_id'], ['forum_threads.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('forum_posts', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_forum_posts_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_forum_posts_thread_id'), ['thread_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_forum_posts_author_id'), ['author_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_forum_posts_parent_post_id'), ['parent_post_id'], unique=False)

    # 4. forum_post_reactions
    op.create_table(
        'forum_post_reactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('post_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('reaction_type', sa.String(length=50), nullable=False, server_default='like'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['post_id'], ['forum_posts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('post_id', 'user_id', 'reaction_type', name='uq_post_user_reaction')
    )
    with op.batch_alter_table('forum_post_reactions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_forum_post_reactions_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_forum_post_reactions_post_id'), ['post_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_forum_post_reactions_user_id'), ['user_id'], unique=False)


def downgrade():
    op.drop_table('forum_post_reactions')
    op.drop_table('forum_posts')
    op.drop_table('forum_threads')
    op.drop_table('course_forum_categories')
