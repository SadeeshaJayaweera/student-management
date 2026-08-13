"""NSBM EduSphere — AI Assistant Router (RAG + MCP)"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import User
from backend.schemas import AIQuery
from backend.services.rag_service import rag_service
from backend.services.mcp_service import mcp_server
from backend.utils.security import get_current_user

import json

router = APIRouter(prefix="/api/ai", tags=["AI Assistant"])


@router.post("/chat")
async def ai_chat(
    query: AIQuery,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Non-streaming AI query with RAG"""
    result = await rag_service.query(query.question, query.context or "")
    return {
        "answer": result["answer"],
        "sources": result.get("sources", []),
        "user": current_user.full_name
    }


@router.post("/chat/stream")
async def ai_chat_stream(
    query: AIQuery,
    current_user: User = Depends(get_current_user)
):
    """Streaming AI response using Server-Sent Events"""
    async def generate():
        yield "data: " + json.dumps({"type": "start", "user": current_user.full_name}) + "\n\n"
        async for chunk in rag_service.stream_query(query.question):
            yield "data: " + json.dumps({"type": "chunk", "content": chunk}) + "\n\n"
        yield "data: " + json.dumps({"type": "end"}) + "\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/mcp/tools")
async def list_mcp_tools(current_user: User = Depends(get_current_user)):
    """List available MCP tools"""
    return {"tools": mcp_server.get_tool_definitions()}


@router.post("/mcp/execute")
async def execute_mcp_tool(
    tool_name: str,
    arguments: dict,
    current_user: User = Depends(get_current_user)
):
    """Execute an MCP tool"""
    result = await mcp_server.execute_tool(tool_name, arguments)
    return {"tool": tool_name, "result": result}


@router.post("/mcp/agent")
async def ai_agent_query(
    query: AIQuery,
    current_user: User = Depends(get_current_user)
):
    """
    AI Agent that uses both RAG and MCP tools to answer questions.
    Automatically selects the right tools based on the query.
    """
    question = query.question.lower()
    mcp_results = {}

    # Tool selection logic
    if any(kw in question for kw in ["grade", "gpa", "mark", "score", "result"]):
        if current_user.role == "student":
            from backend.database import AsyncSessionLocal
            from backend.models import Student
            from sqlalchemy import select
            async with AsyncSessionLocal() as db:
                stu_q = await db.execute(select(Student).where(Student.user_id == current_user.id))
                student = stu_q.scalar_one_or_none()
                if student:
                    mcp_results["grades"] = await mcp_server.execute_tool("get_student_grades", {"student_id": student.student_id})

    if any(kw in question for kw in ["book", "library", "borrow", "isbn", "author"]):
        search_term = next((word for word in query.question.split() if len(word) > 3), query.question)
        mcp_results["library"] = await mcp_server.execute_tool("search_library", {"query": search_term})

    if any(kw in question for kw in ["event", "club", "sports", "activity", "happening"]):
        mcp_results["events"] = await mcp_server.execute_tool("get_club_events", {})

    if any(kw in question for kw in ["news", "announcement", "latest", "recent"]):
        mcp_results["news"] = await mcp_server.execute_tool("get_news", {"limit": 3})

    if any(kw in question for kw in ["exam", "test", "schedule", "timetable"]):
        mcp_results["exam"] = await mcp_server.execute_tool("get_exam_schedule", {})

    # Build augmented question with MCP data
    augmented_question = query.question
    if mcp_results:
        data_summary = "\n".join([f"{k}: {str(v)[:500]}" for k, v in mcp_results.items()])
        augmented_question = f"{query.question}\n\nRelevant data from university systems:\n{data_summary}"

    # Run RAG query
    rag_result = await rag_service.query(augmented_question)

    return {
        "answer": rag_result["answer"],
        "sources": rag_result.get("sources", []),
        "tools_used": list(mcp_results.keys()),
        "user": current_user.full_name
    }


@router.on_event("startup")
async def initialize_rag():
    """Initialize RAG service on startup"""
    await rag_service.initialize()
