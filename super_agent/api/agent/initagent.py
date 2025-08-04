"""初始化agent注册表，加载所有可用的agent"""

import logging

from a2a.types import AgentSkill

from super_agent.agents.mcp_agent import create_mcp_agent
from super_agent.agents.registry import agent_registry
from super_agent.mcp.server import main

logger = logging.getLogger(__name__)


async def initialise_agent_registry() -> None:
    """初始化agent注册表，加载所有agent"""
    logger.info("正在初始化agent注册表...")

    # 优化后的系统提示词：仅在需要时调用工具，否则直接回答，并对搜索结果进行分析总结
    instructions = (
        "你是一个专业的网络搜索和内容获取助手。面对用户问题时，优先根据你已有的知识直接回答；"
        "只有在无法直接回答或需要最新、具体信息时，才调用工具进行网络搜索。"
        "你可以调用以下工具：\n"
        "1. search：使用网络搜索并返回格式化结果。\n"
        "   参数：query（搜索关键词，字符串，必填），max_results（最大结果数，整数，必填）。\n"
        "如需调用工具，请合理选择并使用，获取结果后请对搜索内容进行分析和总结，提炼出对用户最有价值的信息，"
        "并用简明、准确的中文语言进行回答。"
    )

    # 创建搜索agent实例
    search_agent = await create_mcp_agent(
        name="search_query_agent",
        description="用于执行网络搜索和内容获取的Agent",
        version="0.1.0",
        instructions=instructions,
        command="uv",
        server_args=[
            "run",
            "/home/tarena/code/workspace/super-agent/super_agent/mcp/server.py"
        ],
        skills=[
            AgentSkill(
                name="search",
                description="执行网络搜索并返回格式化结果",
                inputModes=["text"],
                outputModes=["text"],
                id="search",
                tags=["search", "internet", "query"],
            )
        ],
        allowed_tools={"search"},
        model="ollama_chat/llama3.2",
        use_stdio=True,
    )

    # 将搜索agent注册到注册表中
    agent_registry.register(
        search_agent,
    )
    logger.info("%s agent注册成功", search_agent.name)

    # 可根据需要添加更多agent

    return agent_registry