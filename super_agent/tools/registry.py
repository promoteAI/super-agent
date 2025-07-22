"""Tool Registry Module."""

from typing import List, Optional

from openai.types.chat.chat_completion_tool_param import ChatCompletionToolParam

from super_agent.mcp.base import BaseHttpMcpSession, MCPTool
from super_agent.pydantic import model_from_schema
from super_agent.tools.base import BaseTool


class ToolRegistry:
    """A registry for managing tools.

    This class allows for the registration and retrieval of tools by their names.
    """

    def __init__(self):
        self._tools = {}

    def __getitem__(self, name: str) -> BaseTool:
        """Get a tool by its name.

        Args:
            name (str): The name of the tool to retrieve.

        Returns:
            BaseTool: The tool instance associated with the given name.

        Raises:
            KeyError: If no tool with the specified name is registered.

        """
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' is not registered.")
        return self._tools[name]

    def __contains__(self, name: str) -> bool:
        """Check if a tool is registered by its name.

        Args:
            name (str): The name of the tool to check.

        Returns:
            bool: True if the tool is registered, False otherwise.

        """
        return name in self._tools

    def register_tool(self, tool: BaseTool):
        """Register a tool in the registry.

        Args:
            tool (BaseTool): The tool instance to register. The tool must have a unique 'name'
                attribute.

        Raises:
            KeyError: If a tool with the same name is already registered.

        """
        self._tools[tool.name] = tool

    async def register_mcp_server(
        self,
        mcp_server: BaseHttpMcpSession,
        allowed_tools: Optional[set[str]] = None,
    ):
        """Register tools from a given MCP server session.

        Retrieves the list of tools available from the provided `mcp_server` session,
        and registers each tool whose name is included in the `allowed_tools` set (if specified).
        For each eligible tool, constructs an `MCPTool` instance with the appropriate
        name, description, input schema, and session, then registers it.

        Args:
            mcp_server (BaseHttpMcpSession): The MCP server session to retrieve tools from.
            allowed_tools (Optional[set[str]], optional): A set of tool names to allow for
                registration. If None, all tools from the server will be registered. Defaults to
                None.

        """
        tools = await mcp_server.list_tools()
        for tool in tools.tools:
            if allowed_tools is None or tool.name in allowed_tools:
                mcp_tool = MCPTool(
                    name=tool.name,
                    description=tool.description,
                    tool_call_schema=model_from_schema(tool.name, tool.inputSchema),
                    session=mcp_server,
                )
                self.register_tool(mcp_tool)

    @property
    def tools(self) -> List[ChatCompletionToolParam]:
        """Return a list of all registered tools."""
        return [i.card for i in self._tools.values() if isinstance(i, BaseTool)]