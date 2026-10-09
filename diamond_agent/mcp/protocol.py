"""
Model Context Protocol (MCP) standard implementation for DiamondAgent.
Follows Anthropic's MCP specification (JSON-RPC 2.0).
"""

from typing import Any, Callable, Dict, List, Optional
import json
import logging

logger = logging.getLogger("diamond_agent.mcp")


class MCPToolDefinition:
    """Definition of an MCP tool exposed to Claude."""

    def __init__(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable[..., Any],
    ):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.handler = handler

    def to_claude_tool_schema(self) -> Dict[str, Any]:
        """Convert to Anthropic Tool Calling schema."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters,
        }


class MCPServer:
    """In-memory MCP Server hosting tool registries."""

    def __init__(self, server_name: str = "diamond-mcp-server"):
        self.server_name = server_name
        self.tools: Dict[str, MCPToolDefinition] = {}

    def register_tool(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable[..., Any],
    ):
        tool = MCPToolDefinition(name, description, parameters, handler)
        self.tools[name] = tool
        logger.info(f"Registered MCP tool: {name}")

    def list_tools(self) -> List[Dict[str, Any]]:
        return [tool.to_claude_tool_schema() for tool in self.tools.values()]

    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        if name not in self.tools:
            raise ValueError(f"Tool '{name}' not found on MCP server '{self.server_name}'")
        tool = self.tools[name]
        try:
            import inspect
            if inspect.iscoroutinefunction(tool.handler):
                return await tool.handler(**arguments)
            else:
                return tool.handler(**arguments)
        except Exception as e:
            logger.error(f"Error executing MCP tool {name}: {e}")
            return {"error": str(e)}
