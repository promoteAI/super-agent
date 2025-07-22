"""初始化agent注册表，加载所有可用的agent"""

import logging

from a2a.types import AgentSkill

from super_agent.agents.weather_agent import create_weather_agent
from super_agent.agents.registry import agent_registry

logger = logging.getLogger(__name__)


async def initialise_agent_registry() -> None:
    """初始化agent注册表，加载所有agent"""
    logger.info("正在初始化agent注册表...")

    # 创建天气agent实例
    weather_agent = await create_weather_agent(
        name="天气查询Agent",
        description="用于查询天气信息的Agent",
        version="0.1.0",
        instructions="该Agent负责处理天气查询请求",
        skills=[
            AgentSkill(
                name="查询当前天气",
                description="查询指定位置的当前天气情况",
                inputModes=["text"],
                outputModes=["text"],
                id="get_current_weather",
                tags=["weather", "current"],
            ),
            AgentSkill(
                name="查询天气预报",
                description="查询指定位置的未来天气预报",
                inputModes=["text"],
                outputModes=["text"],
                id="get_weather_forecast",
                tags=["weather", "forecast"],
            ),
        ],
        allowed_tools={"get_current_weather", "get_weather_forecast"},
        model="gemma2",
        use_stdio=True,
    )

    # 将天气agent注册到注册表中
    agent_registry.register(
        weather_agent,
    )
    logger.info("%s agent注册成功", weather_agent.name)

    # 可根据需要添加更多agent

    return agent_registry