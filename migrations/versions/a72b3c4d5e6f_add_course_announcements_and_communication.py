"""add_course_announcements_and_communication

Revision ID: a72b3c4d5e6f
Revises: f61e2a3b4c5d
Create Date: 2026-11-21 12:54:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a72b3c4d5e6f'
down_revision = 'f61e2a3b4c5d'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'course_announcements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=True),
        sa.Column('cohort_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('priority', sa.String(length=20), nullable=False, server_default='normal'),
        sa.Column('is_pinned', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('requires_acknowledgement', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('published_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['cohort_id'], ['cohorts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('course_announcements', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_course_announcements_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_course_announcements_course_id'), ['course_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_course_announcements_author_id'), ['author_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_course_announcements_cohort_id'), ['cohort_id'], unique=False)

    op.create_table(
        'announcement_acknowledgements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('announcement_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['announcement_id'], ['course_announcements.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('announcement_acknowledgements', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_announcement_acknowledgements_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_announcement_acknowledgements_announcement_id'), ['announcement_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_announcement_acknowledgements_student_id'), ['student_id'], unique=False)


def downgrade():
    with op.batch_alter_table('announcement_acknowledgements', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_announcement_acknowledgements_student_id'))
        batch_op.drop_index(batch_op.f('ix_announcement_acknowledgements_announcement_id'))
        batch_op.drop_index(batch_op.f('ix_announcement_acknowledgements_id'))
    op.drop_table('announcement_acknowledgements')

    with op.batch_alter_table('course_announcements', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_course_announcements_cohort_id'))
        batch_op.drop_index(batch_op.f('ix_course_announcements_author_id'))
        batch_op.drop_index(batch_op.f('ix_course_announcements_course_id'))
        batch_op.drop_index(batch_op.f('ix_course_announcements_id'))
    op.drop_table('course_announcements')
