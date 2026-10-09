"""
Pydantic Schemas for DiamondAgent REST & Streaming API.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class GoalRequest(BaseModel):
    goal: str = Field(..., description="High-level business or engineering goal to orchestrate")
    model: Optional[str] = Field("claude-3-5-sonnet-20241022", description="Underlying Claude model")
    enable_caching: bool = Field(True, description="Enable Anthropic prompt caching")
    max_budget_tokens: Optional[int] = Field(150000, description="Token budget cap")


class AgentTaskResponse(BaseModel):
    task_id: str
    title: str
    agent_role: str
    status: str
    result: Optional[str] = None


class GoalResponse(BaseModel):
    goal: str
    status: str
    tasks_count: int
    summary: str
    review: Dict[str, Any]


class ToolExecutionRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]


class HealthResponse(BaseModel):
    status: str
    version: str
    models_supported: List[str]
    mcp_tools_active: int
