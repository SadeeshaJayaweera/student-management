"""add_structured_course_module_delivery

Revision ID: b27a8c9d0e1f
Revises: a16f7b8c9d0e
Create Date: 2026-11-21 12:12:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b27a8c9d0e1f'
down_revision = 'a16f7b8c9d0e'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('course_modules', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status', sa.String(length=50), nullable=False, server_default='published'))
        batch_op.add_column(sa.Column('unlock_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('prerequisite_module_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_course_modules_prereq',
            'course_modules',
            ['prerequisite_module_id'],
            ['id'],
            ondelete='SET NULL'
        )

    op.create_table(
        'course_lessons',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('module_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('lesson_type', sa.String(length=50), nullable=False, server_default='reading'),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('resource_url', sa.String(length=1024), nullable=True),
        sa.Column('estimated_minutes', sa.Integer(), nullable=False, server_default='15'),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_required', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('is_published', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('unlock_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['module_id'], ['course_modules.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('course_lessons', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_course_lessons_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_course_lessons_module_id'), ['module_id'], unique=False)


def downgrade():
    with op.batch_alter_table('course_lessons', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_course_lessons_module_id'))
        batch_op.drop_index(batch_op.f('ix_course_lessons_id'))
    op.drop_table('course_lessons')

    with op.batch_alter_table('course_modules', schema=None) as batch_op:
        batch_op.drop_constraint('fk_course_modules_prereq', type_='foreignkey')
        batch_op.drop_column('prerequisite_module_id')
        batch_op.drop_column('unlock_at')
        batch_op.drop_column('status')
