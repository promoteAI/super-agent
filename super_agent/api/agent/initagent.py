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
        name="weather_query_agent",
        description="用于查询天气信息的Agent",
        version="0.1.0",
        instructions="""你是一个专业的天气查询助手""",
        skills=[
            AgentSkill(
                name="根据经纬度查询天气",
                description="根据经纬度坐标查询当前天气情况，支持自定义温度、风速和降水量单位",
                inputModes=["text"],
                outputModes=["text"],
                id="get_weather",
                tags=["weather", "current", "coordinates"],
            ),
            AgentSkill(
                name="根据城市获取天气",
                description="查询指定城市的天气情况，支持国家代码和自定义单位",
                inputModes=["text"],
                outputModes=["text"],
                id="get_weather_by_city",
                tags=["weather", "city"],
            ),
        ],
        allowed_tools={"get_weather", "get_weather_by_city"},
        model="ollama_chat/gemma3n",
        use_stdio=True,
    )

    # 将天气agent注册到注册表中
    agent_registry.register(
        weather_agent,
    )
    logger.info("%s agent注册成功", weather_agent.name)

    # 可根据需要添加更多agent

    return agent_registry