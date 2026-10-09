"""
FastAPI Server exposing DiamondAgent orchestration and MCP endpoints.
"""

from typing import Any, Dict
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from diamond_agent import __version__
from diamond_agent.api.schemas import GoalRequest, GoalResponse, HealthResponse, ToolExecutionRequest
from diamond_agent.core.orchestrator import DiamondOrchestrator
from diamond_agent.core.llm_client import ClaudeClient
from diamond_agent.mcp.protocol import MCPServer
from diamond_agent.mcp.tools.fs_tools import FilesystemTools
from diamond_agent.mcp.tools.code_runner import PythonRunnerTool
from diamond_agent.mcp.tools.search_tools import KnowledgeSearchTool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("diamond_agent.api")

app = FastAPI(
    title="DiamondAgent API",
    description="Enterprise Multi-Agent Orchestrator powered by Claude 3.5 & Model Context Protocol (MCP)",
    version=__version__,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize MCP Server & Tools
mcp_server = MCPServer("diamond-core-mcp")
fs = FilesystemTools()
runner = PythonRunnerTool()
searcher = KnowledgeSearchTool()

mcp_server.register_tool(
    name="read_file",
    description="Read file from workspace sandbox",
    parameters={
        "type": "object",
        "properties": {"path": {"type": "string", "description": "Relative file path"}},
        "required": ["path"],
    },
    handler=fs.read_file,
)

mcp_server.register_tool(
    name="execute_python",
    description="Execute Python code snippet in safe environment",
    parameters={
        "type": "object",
        "properties": {"code": {"type": "string", "description": "Valid Python code snippet"}},
        "required": ["code"],
    },
    handler=runner.run_python_code,
)

orchestrator = DiamondOrchestrator()


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="operational",
        version=__version__,
        models_supported=[
            ClaudeClient.DEFAULT_MODEL,
            ClaudeClient.FAST_MODEL,
            ClaudeClient.OPUS_MODEL,
        ],
        mcp_tools_active=len(mcp_server.tools),
    )


@app.post("/api/v1/orchestrate", response_model=GoalResponse)
async def orchestrate_goal(req: GoalRequest):
    """Decompose and execute goal with multi-agent pipeline."""
    try:
        result = await orchestrator.run_pipeline(req.goal)
        return GoalResponse(
            goal=result["goal"],
            status=result["status"],
            tasks_count=result["tasks_count"],
            summary=result["summary"],
            review=result["review"],
        )
    except Exception as e:
        logger.error(f"Orchestration failure: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/mcp/tools")
async def list_mcp_tools():
    """List all registered MCP tools conforming to Claude tool format."""
    return {"tools": mcp_server.list_tools()}


@app.post("/api/v1/mcp/execute")
async def execute_mcp_tool(req: ToolExecutionRequest):
    """Directly trigger an MCP tool."""
    try:
        res = await mcp_server.execute_tool(req.tool_name, req.arguments)
        return {"tool": req.tool_name, "result": res}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
