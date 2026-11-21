"""add_assignment_lifecycle_architecture

Revision ID: d05e6f7a8b9c
Revises: c94d5e6f7a8b
Create Date: 2026-11-21 13:38:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd05e6f7a8b9c'
down_revision = 'c94d5e6f7a8b'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('assignments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('creator_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('module_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('available_from', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('cutoff_date', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('weightage_percentage', sa.Float(), nullable=False, server_default='10.0'))
        batch_op.add_column(sa.Column('grading_type', sa.String(length=30), nullable=False, server_default='points'))
        batch_op.add_column(sa.Column('status', sa.String(length=30), nullable=False, server_default='published'))
        batch_op.add_column(sa.Column('allow_late_submissions', sa.Boolean(), nullable=False, server_default=sa.text('1')))
        batch_op.add_column(sa.Column('late_penalty_percentage_per_day', sa.Float(), nullable=False, server_default='0.0'))
        batch_op.add_column(sa.Column('submission_types', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('allowed_file_extensions', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('max_file_size_mb', sa.Integer(), nullable=False, server_default='50'))
        batch_op.add_column(sa.Column('max_attempts', sa.Integer(), nullable=False, server_default='1'))
        batch_op.add_column(sa.Column('anonymous_grading', sa.Boolean(), nullable=False, server_default=sa.text('0')))
        batch_op.add_column(sa.Column('peer_review_enabled', sa.Boolean(), nullable=False, server_default=sa.text('0')))
        batch_op.add_column(sa.Column('group_assignment', sa.Boolean(), nullable=False, server_default=sa.text('0')))
        batch_op.add_column(sa.Column('published_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(), nullable=True))
        batch_op.create_foreign_key('fk_assignments_creator_id', 'users', ['creator_id'], ['id'], ondelete='SET NULL')
        batch_op.create_foreign_key('fk_assignments_module_id', 'course_modules', ['module_id'], ['id'], ondelete='SET NULL')
        batch_op.create_index(batch_op.f('ix_assignments_creator_id'), ['creator_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_assignments_module_id'), ['module_id'], unique=False)


def downgrade():
    with op.batch_alter_table('assignments', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_assignments_module_id'))
        batch_op.drop_index(batch_op.f('ix_assignments_creator_id'))
        batch_op.drop_constraint('fk_assignments_module_id', type_='foreignkey')
        batch_op.drop_constraint('fk_assignments_creator_id', type_='foreignkey')
        batch_op.drop_column('updated_at')
        batch_op.drop_column('published_at')
        batch_op.drop_column('group_assignment')
        batch_op.drop_column('peer_review_enabled')
        batch_op.drop_column('anonymous_grading')
        batch_op.drop_column('max_attempts')
        batch_op.drop_column('max_file_size_mb')
        batch_op.drop_column('allowed_file_extensions')
        batch_op.drop_column('submission_types')
        batch_op.drop_column('late_penalty_percentage_per_day')
        batch_op.drop_column('allow_late_submissions')
        batch_op.drop_column('status')
        batch_op.drop_column('grading_type')
        batch_op.drop_column('weightage_percentage')
        batch_op.drop_column('cutoff_date')
        batch_op.drop_column('available_from')
        batch_op.drop_column('module_id')
        batch_op.drop_column('creator_id')
