"""add_video_learning_delivery

Revision ID: e50d1f2a3b4c
Revises: d49c0e1f2a3b
Create Date: 2026-11-21 12:42:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e50d1f2a3b4c'
down_revision = 'd49c0e1f2a3b'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'course_videos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('module_id', sa.Integer(), nullable=True),
        sa.Column('lesson_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('provider', sa.String(length=50), nullable=False, server_default='self_hosted'),
        sa.Column('video_url', sa.String(length=1024), nullable=False),
        sa.Column('duration_seconds', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('thumbnail_url', sa.String(length=1024), nullable=True),
        sa.Column('captions_track', sa.JSON(), nullable=True),
        sa.Column('chapters', sa.JSON(), nullable=True),
        sa.Column('is_published', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['lesson_id'], ['course_lessons.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['module_id'], ['course_modules.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('course_videos', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_course_videos_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_course_videos_course_id'), ['course_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_course_videos_module_id'), ['module_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_course_videos_lesson_id'), ['lesson_id'], unique=False)

    op.create_table(
        'video_playback_progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('video_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('last_position_seconds', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_watched_seconds', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('watch_percentage', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('is_completed', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('bookmarks', sa.JSON(), nullable=True),
        sa.Column('notes', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['video_id'], ['course_videos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('video_playback_progress', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_video_playback_progress_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_video_playback_progress_video_id'), ['video_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_video_playback_progress_student_id'), ['student_id'], unique=False)


def downgrade():
    with op.batch_alter_table('video_playback_progress', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_video_playback_progress_student_id'))
        batch_op.drop_index(batch_op.f('ix_video_playback_progress_video_id'))
        batch_op.drop_index(batch_op.f('ix_video_playback_progress_id'))
    op.drop_table('video_playback_progress')

    with op.batch_alter_table('course_videos', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_course_videos_lesson_id'))
        batch_op.drop_index(batch_op.f('ix_course_videos_module_id'))
        batch_op.drop_index(batch_op.f('ix_course_videos_course_id'))
        batch_op.drop_index(batch_op.f('ix_course_videos_id'))
    op.drop_table('course_videos')
