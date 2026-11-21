"""
NSBM EduSphere — Document & Media Management Router
Manages secure uploads, MIME validation, anti-traversal storage, download streaming,
integrity verification, and access controls for course learning media.
"""
import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.models import (
    Course, CourseModule, CourseLesson, CourseDocument, Enrollment, User, UserRole, Lecturer
)
from backend.schemas import CourseDocumentOut, CourseDocumentUpdate
from backend.core.dependencies import get_current_user
from backend.core.storage import storage_service

router = APIRouter(tags=["Document & Media Management"])


def check_course_admin_or_faculty_access(current_user: User, course: Optional[Course] = None):
    """Allows Admins or assigned Lecturers to manage course media"""
    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if role_val in {UserRole.ADMIN.value, UserRole.DEAN.value}:
        return
    if course and role_val == UserRole.LECTURER.value:
        lec = getattr(current_user, "lecturer", None) or getattr(current_user, "lecturer_profile", None)
        if lec and course.lecturer_id == lec.id:
            return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Administrative or assigned faculty permissions required."
    )


async def check_course_read_access(current_user: User, course_id: int, db: AsyncSession) -> Course:
    """Verifies that user is either course instructor, admin, or actively enrolled student"""
    res = await db.execute(
        select(Course)
        .where(Course.id == course_id)
        .options(
            selectinload(Course.lecturer),
            selectinload(Course.enrollments)
        )
    )
    course = res.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    is_admin = role_val in {UserRole.ADMIN.value, UserRole.DEAN.value}
    is_instructor = bool(
        course.lecturer_id and hasattr(current_user, "lecturer_profile") and
        current_user.lecturer_profile and current_user.lecturer_profile.id == course.lecturer_id
    )

    if is_admin or is_instructor:
        return course

    # Check student enrollment
    if role_val == UserRole.STUDENT.value:
        for enr in course.enrollments:
            if enr.student and enr.student.user_id == current_user.id and enr.status in {"active", "completed"}:
                return course

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied: You must be actively enrolled in or instructor of this course."
    )


# ─── Document Endpoints ───────────────────────────────────────────────────────

@router.post("/api/courses/{course_id}/documents/upload", response_model=CourseDocumentOut, status_code=201)
async def upload_course_document(
    course_id: int,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    module_id: Optional[int] = Form(None),
    lesson_id: Optional[int] = Form(None),
    is_published: bool = Form(True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Securely uploads a document or media asset, validates MIME type,
    calculates cryptographic SHA-256 hash, and binds to course/module/lesson.
    """
    course = await db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    check_course_admin_or_faculty_access(current_user, course)

    if module_id:
        mod = await db.get(CourseModule, module_id)
        if not mod or mod.course_id != course_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid module ID for this course")

    if lesson_id:
        les = await db.get(CourseLesson, lesson_id)
        if not les:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid lesson ID")

    storage_path, original_filename, size_bytes, sha256_hash = await storage_service.save_file(file)

    doc = CourseDocument(
        institution_id=course.institution_id,
        course_id=course_id,
        module_id=module_id,
        lesson_id=lesson_id,
        title=(title or original_filename).strip(),
        original_filename=original_filename,
        storage_path=storage_path,
        mime_type=file.content_type or "application/octet-stream",
        file_size_bytes=size_bytes,
        sha256_hash=sha256_hash,
        uploader_id=current_user.id,
        is_published=is_published,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc


@router.get("/api/courses/{course_id}/documents", response_model=List[CourseDocumentOut])
async def list_course_documents(
    course_id: int,
    module_id: Optional[int] = Query(None, description="Filter by module"),
    lesson_id: Optional[int] = Query(None, description="Filter by lesson"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists accessible documents and media files for a course"""
    course = await check_course_read_access(current_user, course_id, db)

    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    is_admin = role_val in {UserRole.ADMIN.value, UserRole.DEAN.value}
    is_instructor = bool(
        course.lecturer_id and hasattr(current_user, "lecturer_profile") and
        current_user.lecturer_profile and current_user.lecturer_profile.id == course.lecturer_id
    )

    q = select(CourseDocument).where(CourseDocument.course_id == course_id)
    if not (is_admin or is_instructor):
        q = q.where(CourseDocument.is_published == True)

    if module_id is not None:
        q = q.where(CourseDocument.module_id == module_id)
    if lesson_id is not None:
        q = q.where(CourseDocument.lesson_id == lesson_id)

    q = q.order_by(CourseDocument.created_at.desc())
    res = await db.execute(q)
    return list(res.scalars().all())


@router.get("/api/documents/{document_id}", response_model=CourseDocumentOut)
async def get_document_details(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves document metadata"""
    res = await db.execute(select(CourseDocument).where(CourseDocument.id == document_id))
    doc = res.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    await check_course_read_access(current_user, doc.course_id, db)
    return doc


@router.get("/api/documents/{document_id}/download")
async def download_course_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Securely streams document file to authorized users and increments download count"""
    res = await db.execute(select(CourseDocument).where(CourseDocument.id == document_id))
    doc = res.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    await check_course_read_access(current_user, doc.course_id, db)

    if not os.path.exists(doc.storage_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File asset missing on storage host")

    doc.download_count += 1
    await db.commit()

    return FileResponse(
        path=doc.storage_path,
        filename=doc.original_filename,
        media_type=doc.mime_type,
        headers={"X-Content-Type-Options": "nosniff"}
    )


@router.put("/api/documents/{document_id}", response_model=CourseDocumentOut)
async def update_document_metadata(
    document_id: int,
    payload: CourseDocumentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Updates document metadata or publication status"""
    res = await db.execute(select(CourseDocument).where(CourseDocument.id == document_id))
    doc = res.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    course = await db.get(Course, doc.course_id)
    check_course_admin_or_faculty_access(current_user, course)

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(doc, field, val)

    await db.commit()
    await db.refresh(doc)
    return doc


@router.delete("/api/documents/{document_id}", status_code=204)
async def delete_course_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Permanently deletes document record and removes physical asset from storage"""
    res = await db.execute(select(CourseDocument).where(CourseDocument.id == document_id))
    doc = res.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    course = await db.get(Course, doc.course_id)
    check_course_admin_or_faculty_access(current_user, course)

    storage_service.delete_file(doc.storage_path)
    await db.delete(doc)
    await db.commit()
    return None
