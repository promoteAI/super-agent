"""初始化agent注册表，加载所有可用的agent"""

import logging

from a2a.types import AgentSkill
import os
from super_agent.agents.mcp_agent import create_mcp_agent
from super_agent.agents.registry import agent_registry
from super_agent.mcp.server import main

logger = logging.getLogger(__name__)


async def initialise_agent_registry() -> None:
    """初始化agent注册表，加载所有agent"""
    logger.info("正在初始化agent注册表...")

    # 优化后的系统提示词：智能判断是否需要调用工具，优先直接回答，调用工具后需总结分析
    instructions = """
你是一个**专业且高效的网络搜索与信息获取助手**。

## 回答原则
- 优先基于你自身的知识和理解直接作答，确保内容**准确、简明**。
- 仅当你无法凭自身知识给出**完整、最新或具体答案**时，才调用工具进行网络搜索。

## 可用工具

### 1. `search`
- **功能**：执行网络搜索，返回结构化结果。
- **参数**：
    - `query`（必填）：用户问题
    - `max_results`（可选）：返回结果数（整数）

如需调用工具，请合理选择并准确填写参数。

## 工具结果处理
- 获取工具返回内容后，请对搜索结果进行**归纳、分析和总结**，提炼出最有价值的信息。
- 用**简洁、权威的中文**回答用户，**避免直接照搬原始搜索内容**。
    """

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
        model=os.getenv("MODEL_NAME", "llama3.2"),
        use_stdio=True,
    )

    # 将搜索agent注册到注册表中
    agent_registry.register(
        search_agent,
    )
    logger.info("%s agent注册成功", search_agent.name)

    # 可根据需要添加更多agent

    return agent_registry