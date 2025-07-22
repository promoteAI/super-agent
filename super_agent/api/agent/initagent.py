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
        instructions="""你是一个专业的天气查询助手。当用户需要查询天气时，请按照以下步骤操作：
1. 如果用户提供城市名称，调用get_weather_by_city工具查询该城市天气。需要以下参数：
   - city: 城市名称（必填）
   - country_code: 国家代码（可选，如"US"）
   - temperature_unit: 温度单位（默认celsius）
   - wind_speed_unit: 风速单位（默认kmh）
   - precipitation_unit: 降水量单位（默认mm）

2. 如果用户提供经纬度坐标，调用get_weather工具查询该位置天气。需要以下参数：
   - latitude: 纬度（必填）
   - longitude: 经度（必填）
   - location_name: 位置名称（可选）
   - temperature_unit: 温度单位（默认celsius）
   - wind_speed_unit: 风速单位（默认kmh）
   - precipitation_unit: 降水量单位（默认mm）

3. 将查询结果以清晰、专业的方式返回给用户，包括：
   - 当前天气状况
   - 温度（使用用户指定的单位）
   - 风速（使用用户指定的单位）
   - 降水量（使用用户指定的单位）
   - 天气预报信息

4. 如果用户提供的信息不足以查询天气，请礼貌地要求用户提供更多必要信息，并说明需要哪些具体参数""",
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