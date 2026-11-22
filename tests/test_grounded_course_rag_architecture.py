from datetime import datetime
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import User, UserRole, Course, CourseModule
from backend.utils.security import hash_password, create_access_token


@pytest.mark.asyncio
async def test_grounded_course_rag_architecture(
    client: AsyncClient,
    test_session: AsyncSession
):
    # 1. Setup Admin, Lecturer, and Student users
    lecturer_user = User(
        email="ai_prof@nsbm.ac.lk",
        username="ai_prof",
        hashed_password=hash_password("LecPass123!"),
        full_name="Prof. John McCarthy",
        role=UserRole.LECTURER,
        is_active=True,
    )
    student_user = User(
        email="ai_student@nsbm.ac.lk",
        username="ai_student",
        hashed_password=hash_password("StuPass123!"),
        full_name="Ada Lovelace",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_session.add_all([lecturer_user, student_user])
    await test_session.commit()

    # 2. Setup Course and Module
    course = Course(
        course_code="CS304",
        title="Artificial Intelligence & Machine Learning",
        description="Core concepts in search algorithms, heuristics, knowledge representation, and neural networks.",
        faculty="Computing",
        department="Computer Science",
        credits=4,
        semester=1,
        year=3,
        is_active=True,
    )
    test_session.add(course)
    await test_session.commit()

    module = CourseModule(
        course_id=course.id,
        title="Knowledge Representation and Graph Search",
        order_index=1,
        status="published",
        is_active=True,
    )
    test_session.add(module)
    await test_session.commit()

    lec_token = create_access_token({"sub": str(lecturer_user.id), "role": "lecturer"})
    lec_headers = {"Authorization": f"Bearer {lec_token}"}
    stu_token = create_access_token({"sub": str(student_user.id), "role": "student"})
    stu_headers = {"Authorization": f"Bearer {stu_token}"}

    # 3. RBAC Check: Student cannot ingest documents
    sample_content = (
        "---Page 1---\n"
        "A* Search algorithm uses both the actual path cost g(n) and the heuristic estimate h(n).\n"
        "The evaluation function is f(n) = g(n) + h(n).\n"
        "An admissible heuristic never overestimates the true cost to reach the goal state.\n"
        "Consistency or monotonicity guarantees that the first time a state is expanded, the path is optimal.\n"
        "---Page 2---\n"
        "Heuristic evaluation functions are widely used in game playing trees such as Minimax and Alpha-Beta Pruning.\n"
        "Branching factor reduction is crucial for maintaining computational tractability."
    )
    res_forbidden = await client.post(
        f"/api/ai/rag/courses/{course.id}/documents",
        json={
            "title": "A* Search & Heuristics Lecture Notes",
            "content": sample_content,
            "module_id": module.id,
            "document_type": "lecture_notes",
            "source_citation": "Module 1 Lecture 2 Slides"
        },
        headers=stu_headers
    )
    assert res_forbidden.status_code == 403

    # 4. Ingest Document as Lecturer
    res_ingest = await client.post(
        f"/api/ai/rag/courses/{course.id}/documents",
        json={
            "title": "A* Search & Heuristics Lecture Notes",
            "content": sample_content,
            "module_id": module.id,
            "document_type": "lecture_notes",
            "source_citation": "Module 1 Lecture 2 Slides"
        },
        headers=lec_headers
    )
    assert res_ingest.status_code == 201
    doc_data = res_ingest.json()
    assert doc_data["title"] == "A* Search & Heuristics Lecture Notes"
    assert doc_data["chunk_count"] >= 1
    assert doc_data["token_count"] > 0
    doc_id = doc_data["id"]

    # 5. List and Get Document Details with Chunks
    res_list = await client.get(f"/api/ai/rag/courses/{course.id}/documents", headers=stu_headers)
    assert res_list.status_code == 200
    docs = res_list.json()
    assert len(docs) == 1
    assert docs[0]["id"] == doc_id

    res_doc = await client.get(f"/api/ai/rag/courses/{course.id}/documents/{doc_id}", headers=stu_headers)
    assert res_doc.status_code == 200
    doc_detail = res_doc.json()
    assert len(doc_detail["chunks"]) >= 1
    chunk = doc_detail["chunks"][0]
    assert "chunk_text" in chunk
    assert chunk["page_number"] >= 1
    assert chunk["line_start"] >= 1

    # 6. Semantic Search with Citation and Attribution
    res_search = await client.post(
        f"/api/ai/rag/courses/{course.id}/search",
        json={"query": "admissible heuristic path cost", "top_k": 3},
        headers=stu_headers
    )
    assert res_search.status_code == 200
    search_hits = res_search.json()
    assert len(search_hits) >= 1
    assert search_hits[0]["relevance_score"] > 0
    assert search_hits[0]["document_title"] == "A* Search & Heuristics Lecture Notes"
    assert search_hits[0]["line_start"] >= 1

    # 7. Grounded Query Generation
    res_query = await client.post(
        f"/api/ai/rag/courses/{course.id}/grounded-query",
        json={"question": "What is an admissible heuristic in A* search?"},
        headers=stu_headers
    )
    assert res_query.status_code == 200
    ans_data = res_query.json()
    assert ans_data["context_used"] is True
    assert len(ans_data["citations"]) >= 1
    citation = ans_data["citations"][0]
    assert citation["citation_index"] == 1
    assert citation["document_title"] == "A* Search & Heuristics Lecture Notes"
    assert "lines" in citation
    assert "[1]" in ans_data["answer"]
    query_id = ans_data["query_id"]

    # 8. User Feedback Logging
    res_feedback = await client.post(
        f"/api/ai/rag/queries/{query_id}/feedback",
        json={"rating": 5, "comment": "Precise citation and accurate answer!"},
        headers=stu_headers
    )
    assert res_feedback.status_code == 200
    assert res_feedback.json()["rating"] == 5

    # 9. Course RAG Analytics
    res_analytics = await client.get(f"/api/ai/rag/courses/{course.id}/analytics", headers=lec_headers)
    assert res_analytics.status_code == 200
    analytics = res_analytics.json()
    assert analytics["document_count"] == 1
    assert analytics["chunk_count"] >= 1
    assert analytics["query_count"] == 1
    assert analytics["avg_feedback_rating"] == 5.0
    assert analytics["avg_latency_ms"] >= 0
