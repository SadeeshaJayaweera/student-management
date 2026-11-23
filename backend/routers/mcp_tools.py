"""
NSBM EduSphere — Model Context Protocol (MCP) Router
Endpoints for tool registry discovery, authorized tool execution,
parameter schema introspection, and invocation audit logging.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database import get_db
from backend.models import User, MCPToolExecutionLog
from backend.schemas import (
    MCPToolDefinitionOut,
    MCPToolExecuteRequest,
    MCPToolExecuteResponse,
    MCPToolInvocationLogOut,
)
from backend.services.mcp_service import mcp_server
from backend.utils.security import get_current_user

router = APIRouter(prefix="/api/mcp", tags=["Model Context Protocol (MCP)"])


@router.get("/tools", response_model=List[MCPToolDefinitionOut])
async def list_registered_mcp_tools(
    current_user: User = Depends(get_current_user)
):
    """Retrieve full catalog of MCP-compliant tool definitions and parameter schemas"""
    return mcp_server.get_tool_definitions()


@router.post("/tools/{tool_name}/execute", response_model=MCPToolExecuteResponse)
async def execute_mcp_tool(
    tool_name: str,
    payload: MCPToolExecuteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Execute an MCP tool with role boundary verification, parameter validation, and audit logging"""
    response = await mcp_server.execute_tool(
        db=db,
        tool_name=tool_name,
        arguments=payload.arguments,
        caller=current_user
    )

    if response.get("status") == "unauthorized":
        raise HTTPException(
            status_code=403,
            detail=response.get("result", {}).get("error", "Execution forbidden by role/privacy boundary")
        )

    return response


@router.get("/invocations", response_model=List[MCPToolInvocationLogOut])
async def list_tool_invocations(
    tool_name: Optional[str] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Audit log of MCP tool invocations (Administrators & Lecturers only)"""
    user_role_str = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if user_role_str not in ["admin", "lecturer"]:
        raise HTTPException(status_code=403, detail="Audit logs access restricted to administrators and faculty")

    stmt = select(MCPToolExecutionLog)
    if tool_name:
        stmt = stmt.where(MCPToolExecutionLog.tool_name == tool_name)
    if status_filter:
        stmt = stmt.where(MCPToolExecutionLog.result_status == status_filter)

    stmt = stmt.order_by(MCPToolExecutionLog.created_at.desc()).limit(limit)
    res = await db.execute(stmt)
    return res.scalars().all()
