"""使用Weather MCP Server的天气代理"""

from a2a.types import AgentCapabilities, AgentSkill
from mcp.client.stdio import StdioServerParameters

from super_agent.agents.base import BaseAgent
from super_agent.mcp.base import BaseHttpMcpSession
from super_agent.settings import ConfiguredBaseSettings
from super_agent.tools.registry import ToolRegistry


class WeatherMcpSettings(ConfiguredBaseSettings):
    """天气MCP代理的配置设置"""

    use_stdio: bool = True  # 是否使用标准输入输出进行通信


settings = WeatherMcpSettings()

# 标准输入输出参数配置
stdio_params = StdioServerParameters(
    command="python",  # 使用的命令
    args=["-m", "mcp_weather_free"]  # 命令参数
)


async def create_weather_agent(
    name: str,
    description: str,
    version: str,
    instructions: str,
    skills: list[AgentSkill] = None,
    allowed_tools: set[str] = None,
    model: str = "gemma2",
    use_stdio: bool = settings.use_stdio,
) -> BaseAgent:
    """创建并配置一个天气代理

    Args:
        name (str): 代理名称
        description (str): 代理功能描述
        version (str): 代理版本号
        instructions (str): 代理操作指南
        skills (list[AgentSkill], optional): 代理技能列表，默认为None
        allowed_tools (set[str], optional): 代理允许使用的工具集合，默认为None
        model (str, optional): 使用的模型标识，默认为"gpt-4o-mini_2024-07-18"
        use_stdio (bool, optional): 是否使用标准输入输出进行通信，默认为True

    Returns:
        BaseAgent: 配置好的天气代理实例

    Raises:
        工具注册或代理创建过程中抛出的任何异常
    """
    # 生成代理ID，将名称转换为小写并用-替换空格
    agent_id = name.lower().replace(" ", "-")

    # 初始化工具注册表
    tool_registry = ToolRegistry()

    # 创建MCP会话
    weather_mcp = BaseHttpMcpSession(
        session_id=f"{agent_id}-weather-mcp-session",  # 会话ID
        stdio_parameters=stdio_params,  # 标准输入输出参数
        use_stdio=use_stdio,  # 是否使用标准输入输出
    )

    # 注册MCP服务器
    await tool_registry.register_mcp_server(weather_mcp, allowed_tools)

    # 返回配置好的代理实例
    return BaseAgent(
        capabilities=AgentCapabilities(
            pushNotifications=False,  # 是否支持推送通知
            stateTransitionHistory=False,  # 是否记录状态转换历史
            streaming=False  # 是否支持流式传输
        ),
        defaultInputModes=["text"],  # 默认输入模式
        defaultOutputModes=["text"],  # 默认输出模式
        description=description,  # 代理描述
        url="https://localhost:41241",  # 代理URL
        version=version,  # 代理版本
        id=agent_id,  # 代理ID
        name=name,  # 代理名称
        model=model,  # 使用模型
        instructions=instructions,  # 操作指南
        skills=skills or [],  # 技能列表
        tool_registry=tool_registry,  # 工具注册表
    )