"""通用的MCP服务器代理创建工具"""

from typing import Optional, Any

from a2a.types import AgentCapabilities, AgentSkill
from mcp.client.stdio import StdioServerParameters

from super_agent.agents.base import BaseAgent
from super_agent.mcp.base import BaseHttpMcpSession
from super_agent.settings import ConfiguredBaseSettings
from super_agent.tools.registry import ToolRegistry


class McpAgentSettings(ConfiguredBaseSettings):
    """MCP代理的通用配置设置"""

    use_stdio: bool = True  # 是否使用标准输入输出进行通信


settings = McpAgentSettings()


async def create_mcp_agent(
    name: str,
    description: str,
    version: str,
    instructions: str,
    command: str = "uvx",
    server_args: list[str] = None,
    skills: Optional[list[AgentSkill]] = None,
    allowed_tools: Optional[set[str]] = None,
    model: str = "ollama_chat/gemma3n",
    use_stdio: bool = settings.use_stdio,
    url: str = "https://localhost:41241",
    **kwargs: Any
) -> BaseAgent:
    """创建并配置一个通用的MCP代理

    Args:
        name (str): 代理名称
        description (str): 代理功能描述
        version (str): 代理版本号
        instructions (str): 代理操作指南
        command (str, optional): MCP服务器启动命令，默认为"uvx"
        server_args (list[str], optional): MCP服务器命令参数，默认为None
        skills (Optional[list[AgentSkill]], optional): 代理技能列表，默认为None
        allowed_tools (Optional[set[str]], optional): 代理允许使用的工具集合，默认为None
        model (str, optional): 使用的模型标识，默认为"ollama_chat/gemma3n"
        use_stdio (bool, optional): 是否使用标准输入输出进行通信，默认为True
        url (str, optional): 代理URL，默认为本地地址
        **kwargs: 其他可能的配置参数

    Returns:
        BaseAgent: 配置好的MCP代理实例
    """
    # 生成代理ID，将名称转换为小写并用-替换空格
    agent_id = name.lower().replace(" ", "-")

    # 标准输入输出参数配置
    stdio_params = StdioServerParameters(
        command=command,
        args=server_args or []
    )

    # 初始化工具注册表
    tool_registry = ToolRegistry()

    # 创建MCP会话
    mcp_session = BaseHttpMcpSession(
        session_id=f"{agent_id}-mcp-session",
        stdio_parameters=stdio_params,
        use_stdio=use_stdio,
    )

    # 注册MCP服务器
    await tool_registry.register_mcp_server(mcp_session, allowed_tools)

    # 返回配置好的代理实例
    return BaseAgent(
        capabilities=AgentCapabilities(
            pushNotifications=False,
            stateTransitionHistory=False,
            streaming=True,
        ),
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        description=description,
        url=url,
        version=version,
        id=agent_id,
        name=name,
        model=model,
        instructions=instructions,
        skills=skills or [],
        tool_registry=tool_registry,
        **kwargs
    )