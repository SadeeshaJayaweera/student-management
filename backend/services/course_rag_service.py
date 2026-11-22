"""
NSBM EduSphere — Grounded Course RAG Service
Multi-course document ingestion, semantic chunking, ChromaDB integration,
and citation-grounded retrieval.
"""
import math
import time
import re
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from backend.models import (
    Course,
    CourseModule,
    CourseKnowledgeDocument,
    CourseKnowledgeChunk,
    RAGQueryLog,
)
from backend.config import settings


class CourseRAGService:
    """Service handling course-grounded retrieval-augmented generation"""

    def __init__(self):
        self._chroma_client = None
        self._initialized = False

    def _get_chroma_client(self):
        if not self._initialized:
            try:
                import chromadb
                self._chroma_client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
                self._initialized = True
            except Exception:
                self._chroma_client = None
                self._initialized = True
        return self._chroma_client

    def chunk_content(
        self,
        content: str,
        target_chunk_size: int = 600,
        overlap: int = 80
    ) -> List[Dict[str, Any]]:
        """
        Split document text into structured chunks preserving line & page positions.
        """
        lines = content.splitlines(keepends=True)
        chunks = []
        current_chunk_lines = []
        current_length = 0
        start_line = 1
        current_line = 1
        page_number = 1
        chunk_idx = 0

        for line in lines:
            line_str = line
            # Detect explicit page break
            if "---page" in line_str.lower() or "\x0c" in line_str:
                page_match = re.search(r"page\s*(\d+)", line_str, re.IGNORECASE)
                if page_match:
                    try:
                        page_number = int(page_match.group(1))
                    except ValueError:
                        page_number += 1
                else:
                    page_number += 1

            current_chunk_lines.append(line_str)
            current_length += len(line_str)

            # Heuristic: every 1800 chars without explicit marker is a page increment
            approx_page = max(page_number, (current_line // 35) + 1)

            if current_length >= target_chunk_size:
                chunk_text = "".join(current_chunk_lines).strip()
                if chunk_text:
                    chunks.append({
                        "chunk_index": chunk_idx,
                        "chunk_text": chunk_text,
                        "page_number": approx_page,
                        "line_start": start_line,
                        "line_end": current_line,
                        "metadata": {
                            "char_count": len(chunk_text),
                            "word_count": len(chunk_text.split()),
                        }
                    })
                    chunk_idx += 1

                # Overlap calculation: keep last few lines
                overlap_lines = []
                overlap_len = 0
                for l in reversed(current_chunk_lines):
                    if overlap_len + len(l) <= overlap:
                        overlap_lines.insert(0, l)
                        overlap_len += len(l)
                    else:
                        break

                current_chunk_lines = overlap_lines
                current_length = overlap_len
                start_line = max(1, current_line - len(overlap_lines) + 1)

            current_line += 1

        # Tail chunk
        if current_chunk_lines:
            chunk_text = "".join(current_chunk_lines).strip()
            if chunk_text:
                approx_page = max(page_number, (current_line // 35) + 1)
                chunks.append({
                    "chunk_index": chunk_idx,
                    "chunk_text": chunk_text,
                    "page_number": approx_page,
                    "line_start": start_line,
                    "line_end": current_line - 1,
                    "metadata": {
                        "char_count": len(chunk_text),
                        "word_count": len(chunk_text.split()),
                    }
                })

        return chunks

    async def ingest_document(
        self,
        db: AsyncSession,
        course_id: int,
        title: str,
        content: str,
        module_id: Optional[int] = None,
        document_type: str = "lecture_notes",
        source_citation: Optional[str] = None
    ) -> CourseKnowledgeDocument:
        """
        Ingest and index a course knowledge document into chunks and vector store.
        """
        # Validate course exists
        course_res = await db.execute(select(Course).where(Course.id == course_id))
        if not course_res.scalar_one_or_none():
            raise ValueError(f"Course {course_id} does not exist")

        if module_id:
            mod_res = await db.execute(select(CourseModule).where(CourseModule.id == module_id))
            if not mod_res.scalar_one_or_none():
                raise ValueError(f"CourseModule {module_id} does not exist")

        raw_chunks = self.chunk_content(content)
        token_count = sum(len(c["chunk_text"].split()) for c in raw_chunks) * 1.3

        doc = CourseKnowledgeDocument(
            course_id=course_id,
            module_id=module_id,
            title=title,
            document_type=document_type,
            source_citation=source_citation or f"{title} (Course ID {course_id})",
            content=content,
            token_count=int(token_count),
            chunk_count=len(raw_chunks),
            status="indexed"
        )
        db.add(doc)
        await db.flush()

        # Create chunk records
        chroma_docs = []
        chroma_ids = []
        chroma_metadatas = []

        for c in raw_chunks:
            embedding_id = f"c{course_id}_d{doc.id}_chk{c['chunk_index']}"
            chunk_record = CourseKnowledgeChunk(
                document_id=doc.id,
                course_id=course_id,
                chunk_index=c["chunk_index"],
                chunk_text=c["chunk_text"],
                page_number=c["page_number"],
                line_start=c["line_start"],
                line_end=c["line_end"],
                embedding_id=embedding_id,
                chunk_metadata=c["metadata"]
            )
            db.add(chunk_record)

            chroma_docs.append(c["chunk_text"])
            chroma_ids.append(embedding_id)
            chroma_metadatas.append({
                "course_id": course_id,
                "document_id": doc.id,
                "module_id": module_id or 0,
                "page": c["page_number"],
                "line_start": c["line_start"],
                "line_end": c["line_end"],
                "doc_title": title,
            })

        await db.commit()
        await db.refresh(doc)

        # Sync with ChromaDB if available
        client = self._get_chroma_client()
        if client and chroma_docs:
            try:
                coll = client.get_or_create_collection(name=f"course_{course_id}")
                coll.upsert(
                    ids=chroma_ids,
                    documents=chroma_docs,
                    metadatas=chroma_metadatas
                )
            except Exception:
                pass

        return doc

    def _calculate_lexical_similarity(self, query: str, text: str) -> float:
        """Calculate token-overlap and term frequency relevance score"""
        q_tokens = set(re.findall(r"\w+", query.lower()))
        if not q_tokens:
            return 0.0
        t_tokens = re.findall(r"\w+", text.lower())
        if not t_tokens:
            return 0.0

        matches = sum(1 for t in t_tokens if t in q_tokens)
        density = matches / len(t_tokens)
        query_coverage = sum(1 for q in q_tokens if q in text.lower()) / len(q_tokens)

        # Combined harmonic score
        score = 0.6 * query_coverage + 0.4 * min(1.0, density * 5.0)
        return round(min(1.0, score), 4)

    async def search_course_knowledge(
        self,
        db: AsyncSession,
        course_id: int,
        query: str,
        top_k: int = 4,
        module_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve the most relevant course knowledge chunks with citation metadata.
        """
        # Query chunks from database
        query_stmt = (
            select(CourseKnowledgeChunk, CourseKnowledgeDocument)
            .join(CourseKnowledgeDocument, CourseKnowledgeChunk.document_id == CourseKnowledgeDocument.id)
            .where(CourseKnowledgeChunk.course_id == course_id)
        )
        if module_id is not None:
            query_stmt = query_stmt.where(CourseKnowledgeDocument.module_id == module_id)

        res = await db.execute(query_stmt)
        rows = res.all()

        if not rows:
            return []

        scored_results = []
        for chunk, doc in rows:
            score = self._calculate_lexical_similarity(query, chunk.chunk_text)
            scored_results.append({
                "chunk_id": chunk.id,
                "document_id": doc.id,
                "document_title": doc.title,
                "source_citation": doc.source_citation,
                "page_number": chunk.page_number,
                "line_start": chunk.line_start,
                "line_end": chunk.line_end,
                "content": chunk.chunk_text,
                "relevance_score": score
            })

        # Sort descending by relevance score
        scored_results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return scored_results[:top_k]

    async def generate_grounded_answer(
        self,
        db: AsyncSession,
        course_id: int,
        user_id: int,
        question: str,
        module_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate a grounded answer attributing claims directly to indexed course documents.
        """
        start_time = time.time()
        relevant_chunks = await self.search_course_knowledge(
            db, course_id, question, top_k=3, module_id=module_id
        )

        citations = []
        context_used = bool(relevant_chunks and relevant_chunks[0]["relevance_score"] > 0.05)

        if context_used:
            answer_segments = []
            for i, chunk in enumerate(relevant_chunks, start=1):
                citation_entry = {
                    "citation_index": i,
                    "document_id": chunk["document_id"],
                    "document_title": chunk["document_title"],
                    "source": chunk["source_citation"],
                    "page": chunk["page_number"],
                    "lines": f"{chunk['line_start']}-{chunk['line_end']}",
                    "snippet": (chunk["content"][:240] + "...") if len(chunk["content"]) > 240 else chunk["content"]
                }
                citations.append(citation_entry)
                # Extract first meaningful statement for summary
                snippet = chunk["content"].strip().split("\n")[0]
                answer_segments.append(f"[{i}] {snippet}")

            joined_summary = " ".join(answer_segments)
            answer = (
                f"Based on the official course materials for this syllabus:\n\n"
                f"{joined_summary}\n\n"
                f"Please consult the cited sections above for complete reference details."
            )
        else:
            answer = (
                f"No specific syllabus documents directly matched '{question}'. "
                f"Please verify the module or lecture note indexing for Course {course_id}."
            )

        latency_ms = round((time.time() - start_time) * 1000.0, 2)

        # Log query
        log_entry = RAGQueryLog(
            user_id=user_id,
            course_id=course_id,
            query_text=question,
            response_text=answer,
            retrieved_chunks_json=[
                {"chunk_id": c["chunk_id"], "score": c["relevance_score"]} for c in relevant_chunks
            ],
            citations_json=citations,
            latency_ms=latency_ms
        )
        db.add(log_entry)
        await db.commit()
        await db.refresh(log_entry)

        return {
            "query_id": log_entry.id,
            "question": question,
            "answer": answer,
            "citations": citations,
            "latency_ms": latency_ms,
            "context_used": context_used
        }

    async def log_query_feedback(
        self,
        db: AsyncSession,
        query_id: int,
        rating: int,
        comment: Optional[str] = None
    ) -> RAGQueryLog:
        """Log user feedback rating for a generated RAG answer"""
        res = await db.execute(select(RAGQueryLog).where(RAGQueryLog.id == query_id))
        log_entry = res.scalar_one_or_none()
        if not log_entry:
            raise ValueError(f"RAGQueryLog {query_id} not found")

        log_entry.feedback_rating = rating
        log_entry.feedback_comment = comment
        await db.commit()
        await db.refresh(log_entry)
        return log_entry

    async def get_course_rag_analytics(
        self,
        db: AsyncSession,
        course_id: int
    ) -> Dict[str, Any]:
        """Compute retrieval analytics, query volumes, and average latency"""
        doc_count_res = await db.execute(
            select(func.count(CourseKnowledgeDocument.id)).where(CourseKnowledgeDocument.course_id == course_id)
        )
        doc_count = doc_count_res.scalar() or 0

        chunk_count_res = await db.execute(
            select(func.count(CourseKnowledgeChunk.id)).where(CourseKnowledgeChunk.course_id == course_id)
        )
        chunk_count = chunk_count_res.scalar() or 0

        query_res = await db.execute(
            select(
                func.count(RAGQueryLog.id),
                func.avg(RAGQueryLog.latency_ms),
                func.avg(RAGQueryLog.feedback_rating)
            ).where(RAGQueryLog.course_id == course_id)
        )
        q_count, avg_lat, avg_rating = query_res.one()

        return {
            "course_id": course_id,
            "document_count": doc_count,
            "chunk_count": chunk_count,
            "query_count": q_count or 0,
            "avg_latency_ms": round(float(avg_lat or 0.0), 2),
            "avg_feedback_rating": round(float(avg_rating), 2) if avg_rating is not None else None
        }


course_rag_service = CourseRAGService()
