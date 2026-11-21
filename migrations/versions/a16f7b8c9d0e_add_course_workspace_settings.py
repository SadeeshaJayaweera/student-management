"""add_course_workspace_settings

Revision ID: a16f7b8c9d0e
Revises: f15e6a7b8c9d
Create Date: 2026-11-21 12:05:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a16f7b8c9d0e'
down_revision = 'f15e6a7b8c9d'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('courses', schema=None) as batch_op:
        batch_op.add_column(sa.Column('syllabus_data', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('workspace_settings', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('banner_url', sa.String(length=500), nullable=True))


def downgrade():
    with op.batch_alter_table('courses', schema=None) as batch_op:
        batch_op.drop_column('banner_url')
        batch_op.drop_column('workspace_settings')
        batch_op.drop_column('syllabus_data')
