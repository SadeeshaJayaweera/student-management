"""add_rich_learning_content_authoring

Revision ID: c38b9d0e1f2a
Revises: b27a8c9d0e1f
Create Date: 2026-11-21 12:28:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c38b9d0e1f2a'
down_revision = 'b27a8c9d0e1f'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'lesson_content_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lesson_id', sa.Integer(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('content_format', sa.String(length=50), nullable=False, server_default='markdown'),
        sa.Column('raw_content', sa.Text(), nullable=False),
        sa.Column('rendered_content', sa.Text(), nullable=False),
        sa.Column('widget_configs', sa.JSON(), nullable=True),
        sa.Column('author_id', sa.Integer(), nullable=True),
        sa.Column('change_summary', sa.String(length=255), nullable=True),
        sa.Column('is_current', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['lesson_id'], ['course_lessons.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('lesson_content_versions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_lesson_content_versions_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_lesson_content_versions_lesson_id'), ['lesson_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_lesson_content_versions_version_number'), ['version_number'], unique=False)
        batch_op.create_index(batch_op.f('ix_lesson_content_versions_author_id'), ['author_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_lesson_content_versions_is_current'), ['is_current'], unique=False)


def downgrade():
    with op.batch_alter_table('lesson_content_versions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_lesson_content_versions_is_current'))
        batch_op.drop_index(batch_op.f('ix_lesson_content_versions_author_id'))
        batch_op.drop_index(batch_op.f('ix_lesson_content_versions_version_number'))
        batch_op.drop_index(batch_op.f('ix_lesson_content_versions_lesson_id'))
        batch_op.drop_index(batch_op.f('ix_lesson_content_versions_id'))
    op.drop_table('lesson_content_versions')
