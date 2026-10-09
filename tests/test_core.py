"""
Unit tests for DiamondAgent Core and MCP engine.
"""

import asyncio
from diamond_agent.core.llm_client import ClaudeClient
from diamond_agent.core.orchestrator import DiamondOrchestrator
from diamond_agent.core.context_manager import ContextCompactor
from diamond_agent.mcp.protocol import MCPServer
from diamond_agent.mcp.tools.code_runner import PythonRunnerTool
from diamond_agent.mcp.tools.fs_tools import FilesystemTools


def test_claude_client_simulation():
    async def _run():
        client = ClaudeClient(api_key=None)
        res = await client.generate_response(messages=[{"role": "user", "content": "Hello Diamond"}])
        assert res is not None
        assert "content" in res
        assert res["role"] == "assistant"
    asyncio.run(_run())


def test_orchestrator_planning():
    async def _run():
        orchestrator = DiamondOrchestrator()
        tasks = await orchestrator.plan_goal("Build an AI document summarization engine")
        assert len(tasks) >= 2
        for t in tasks:
            assert t.task_id.startswith("T")
            assert len(t.title) > 0
    asyncio.run(_run())


def test_orchestrator_pipeline():
    async def _run():
        orchestrator = DiamondOrchestrator()
        res = await orchestrator.run_pipeline("Optimize database indexing")
        assert res["status"] in ["success", "needs_revision"]
        assert res["tasks_count"] >= 2
    asyncio.run(_run())


def test_context_compactor():
    compactor = ContextCompactor(max_token_budget=1000, summary_threshold=100)
    for i in range(10):
        compactor.add_memory("user", f"Turn {i}: Detailed instruction text repeating " * 10)
    compacted = compactor.compact_history()
    assert len(compacted) < 10
    assert any("[Compacted Summary" in m["content"] for m in compacted)


def test_mcp_server_and_tools(tmp_path):
    async def _run():
        server = MCPServer("test-server")
        runner = PythonRunnerTool()
        fs = FilesystemTools(base_dir=str(tmp_path))

        server.register_tool(
            name="run_code",
            description="Run python",
            parameters={"type": "object", "properties": {"code": {"type": "string"}}},
            handler=runner.run_python_code,
        )

        tools = server.list_tools()
        assert len(tools) == 1
        assert tools[0]["name"] == "run_code"

        result = await server.execute_tool("run_code", {"code": "print(2 + 3)"})
        assert result["status"] == "success"
        assert result["stdout"].strip() == "5"

        # Test file write and read
        res_w = fs.write_file("test.txt", "Hello MCP")
        assert res_w["status"] == "success"
        res_r = fs.read_file("test.txt")
        assert res_r["content"] == "Hello MCP"
    asyncio.run(_run())
