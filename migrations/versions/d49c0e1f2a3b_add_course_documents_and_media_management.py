"""add_course_documents_and_media_management

Revision ID: d49c0e1f2a3b
Revises: c38b9d0e1f2a
Create Date: 2026-11-21 12:34:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd49c0e1f2a3b'
down_revision = 'c38b9d0e1f2a'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'course_documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('institution_id', sa.Integer(), nullable=True),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('module_id', sa.Integer(), nullable=True),
        sa.Column('lesson_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('storage_path', sa.String(length=512), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), nullable=False),
        sa.Column('sha256_hash', sa.String(length=64), nullable=False),
        sa.Column('uploader_id', sa.Integer(), nullable=True),
        sa.Column('is_published', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('download_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['lesson_id'], ['course_lessons.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['module_id'], ['course_modules.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['uploader_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('course_documents', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_course_documents_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_course_documents_course_id'), ['course_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_course_documents_institution_id'), ['institution_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_course_documents_module_id'), ['module_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_course_documents_lesson_id'), ['lesson_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_course_documents_uploader_id'), ['uploader_id'], unique=False)


def downgrade():
    with op.batch_alter_table('course_documents', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_course_documents_uploader_id'))
        batch_op.drop_index(batch_op.f('ix_course_documents_lesson_id'))
        batch_op.drop_index(batch_op.f('ix_course_documents_module_id'))
        batch_op.drop_index(batch_op.f('ix_course_documents_institution_id'))
        batch_op.drop_index(batch_op.f('ix_course_documents_course_id'))
        batch_op.drop_index(batch_op.f('ix_course_documents_id'))
    op.drop_table('course_documents')
