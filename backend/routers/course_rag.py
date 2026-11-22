"""
NSBM EduSphere — Grounded Course RAG Router
Endpoints for course material ingestion, semantic search with source citations,
grounded query generation, user feedback, and retrieval analytics.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.models import User, CourseKnowledgeDocument, CourseKnowledgeChunk
from backend.schemas import (
    CourseKnowledgeDocumentCreate,
    CourseKnowledgeDocumentOut,
    CourseKnowledgeChunkOut,
    CourseRAGSearchQuery,
    CourseRAGSearchResult,
    CourseRAGGroundedQuery,
    CourseRAGGroundedAnswer,
    RAGFeedbackCreate,
    CourseRAGAnalyticsOut,
)
from backend.services.course_rag_service import course_rag_service
from backend.utils.security import get_current_user

router = APIRouter(prefix="/api/ai/rag", tags=["Course Grounded RAG"])


@router.post("/courses/{course_id}/documents", response_model=CourseKnowledgeDocumentOut, status_code=status.HTTP_201_CREATED)
async def ingest_course_document(
    course_id: int,
    payload: CourseKnowledgeDocumentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ingest, chunk, and index course document into vector knowledge base (Lecturers/Admins only)"""
    if current_user.role not in ["lecturer", "admin"]:
        raise HTTPException(status_code=403, detail="Only lecturers and administrators can ingest course knowledge documents")

    try:
        doc = await course_rag_service.ingest_document(
            db=db,
            course_id=course_id,
            title=payload.title,
            content=payload.content,
            module_id=payload.module_id,
            document_type=payload.document_type,
            source_citation=payload.source_citation
        )
        return doc
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/courses/{course_id}/documents", response_model=List[CourseKnowledgeDocumentOut])
async def list_course_documents(
    course_id: int,
    module_id: Optional[int] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all indexed documents for a course"""
    stmt = select(CourseKnowledgeDocument).where(CourseKnowledgeDocument.course_id == course_id)
    if module_id is not None:
        stmt = stmt.where(CourseKnowledgeDocument.module_id == module_id)
    stmt = stmt.order_by(CourseKnowledgeDocument.created_at.desc())
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get("/courses/{course_id}/documents/{document_id}")
async def get_document_details(
    course_id: int,
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get document details along with its individual chunk items"""
    stmt = (
        select(CourseKnowledgeDocument)
        .where(
            CourseKnowledgeDocument.id == document_id,
            CourseKnowledgeDocument.course_id == course_id
        )
        .options(selectinload(CourseKnowledgeDocument.chunks))
    )
    res = await db.execute(stmt)
    doc = res.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "id": doc.id,
        "course_id": doc.course_id,
        "module_id": doc.module_id,
        "title": doc.title,
        "document_type": doc.document_type,
        "source_citation": doc.source_citation,
        "token_count": doc.token_count,
        "chunk_count": doc.chunk_count,
        "status": doc.status,
        "created_at": doc.created_at,
        "chunks": [
            {
                "id": c.id,
                "chunk_index": c.chunk_index,
                "chunk_text": c.chunk_text,
                "page_number": c.page_number,
                "line_start": c.line_start,
                "line_end": c.line_end,
                "metadata": c.chunk_metadata
            }
            for c in doc.chunks
        ]
    }


@router.post("/courses/{course_id}/search", response_model=List[CourseRAGSearchResult])
async def search_course_chunks(
    course_id: int,
    payload: CourseRAGSearchQuery,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve semantic chunks matching query with citation metadata and relevance scores"""
    results = await course_rag_service.search_course_knowledge(
        db=db,
        course_id=course_id,
        query=payload.query,
        top_k=payload.top_k,
        module_id=payload.module_id
    )
    return results


@router.post("/courses/{course_id}/grounded-query", response_model=CourseRAGGroundedAnswer)
async def grounded_query(
    course_id: int,
    payload: CourseRAGGroundedQuery,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate grounded answer synthesized with explicit source document and line/page citations"""
    answer_data = await course_rag_service.generate_grounded_answer(
        db=db,
        course_id=course_id,
        user_id=current_user.id,
        question=payload.question,
        module_id=payload.module_id
    )
    return answer_data


@router.post("/queries/{query_id}/feedback")
async def submit_query_feedback(
    query_id: int,
    payload: RAGFeedbackCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Log user satisfaction rating and commentary for a grounded answer"""
    try:
        log_entry = await course_rag_service.log_query_feedback(
            db=db,
            query_id=query_id,
            rating=payload.rating,
            comment=payload.comment
        )
        return {
            "query_id": log_entry.id,
            "rating": log_entry.feedback_rating,
            "comment": log_entry.feedback_comment,
            "status": "recorded"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/courses/{course_id}/analytics", response_model=CourseRAGAnalyticsOut)
async def get_course_analytics(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get RAG performance metrics, indexed documents count, and latency stats"""
    analytics = await course_rag_service.get_course_rag_analytics(db, course_id)
    return analytics
