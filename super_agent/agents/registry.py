"""Agent Registry Module."""

from typing import Any, Dict, List, Union, overload
from uuid import uuid4

from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.types import Message, MessageSendParams, Part, Role, TextPart
from pydantic import BeforeValidator, Field
from typing_extensions import Annotated

from super_agent.agents.base import BaseAgent
from super_agent.openai_cli.tools import ChatCompletionToolParam, create_tool
from super_agent.pydantic_utils import ConfiguredBaseModel
from super_agent.utils.options import validate_options


class AgentParameters(ConfiguredBaseModel):
    """Agent的基础参数类"""

    text: Annotated[str, Field(description="Agent要处理的文本内容")]


class A2AOptions(AgentParameters):
    """A2A Agent的配置选项"""

    message_id: Annotated[
        str,
        Field(
            description="要处理的消息ID",
            default_factory=lambda: uuid4().hex,
        ),
    ]
    role: Annotated[
        Role,
        Field(description="Agent在对话中的角色", default=Role.agent),
        BeforeValidator(lambda v: Role(v) if isinstance(v, str) else v),
    ]
    thread_id: Annotated[
        str,
        Field(
            description="Agent上下文的线程ID",
            default_factory=lambda: uuid4().hex,
        ),
    ]


class AgentRegistry:
    """管理Agent的单例注册表"""

    _instance: "AgentRegistry" = None

    def __new__(cls) -> "AgentRegistry":
        """确保AgentRegistry是单例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化AgentRegistry，创建空的agents字典"""
        if not hasattr(self, "_agents"):
            self._agents: Dict[str, BaseAgent] = {}

    def __iter__(self):
        """返回已注册agents的迭代器"""
        return iter(self._agents.values())

    def __contains__(self, agent_id: str) -> bool:
        """检查指定id的agent是否已注册

        Args:
            agent_id (str): 要检查的agent id

        Returns:
            bool: 如果agent已注册返回True，否则返回False
        """
        return agent_id in self._agents

    def register(self, agent: BaseAgent):
        """注册一个新的agent

        Args:
            agent (BaseAgent): 要注册的agent实例，必须具有唯一的'id'属性

        Raises:
            KeyError: 如果同名的agent已经注册

        Side Effects:
            修改类级别的_agents字典，添加新的agent
        """
        self._agents[agent.id] = agent

    def list_agents(self) -> Dict[str, BaseAgent]:
        """返回agent名称到对应agent类的映射字典

        Returns:
            Dict[str, BaseAgent]: 字典的key是agent id（字符串），value是注册的agent类
        """
        return self._agents

    def get_agent(self, id: str) -> BaseAgent:
        """通过名称获取已注册的agent类

        Args:
            id (str): 要获取的agent id

        Returns:
            BaseAgent: 与给定名称关联的agent类

        Raises:
            KeyError: 如果没有找到指定名称的agent
        """
        return self._agents[id]

    @overload
    def execute_agent(self, options: A2AOptions): ...

    @overload
    def execute_agent(self, options: dict[str, Any]): ...

    @validate_options(A2AOptions)
    async def execute_agent(
        self,
        id: str,
        queue: EventQueue,
        options: Union[A2AOptions, dict[str, Any]],
    ) -> None:
        """使用提供的事件队列和选项执行指定的agent

        Args:
            id (str): 要执行的agent id
            queue (EventQueue): 供agent使用的事件队列
            options (Union[A2AOptions, dict[str, Any]]): agent执行的选项，必须是A2AOptions的实例

        Raises:
            AssertionError: 如果options不是A2AOptions的实例

        该方法从提供的选项构造Message和RequestContext，
        通过名称获取agent类，并使用构造的上下文和事件队列调用其execute方法
        """
        assert isinstance(
            options, A2AOptions
        ), "Options必须是A2AOptions的实例"

        message = Message(
            messageId=options.message_id,
            role=options.role,
            contextId=options.thread_id,
            parts=[
                Part(
                    root=TextPart(
                        kind="text",
                        text=options.text,
                    )
                )
            ],
        )

        context = RequestContext(
            request=MessageSendParams(message=message), context_id=options.thread_id
        )

        agent_cls = self.get_agent(id)
        await agent_cls.execute(
            context=context,
            event_queue=queue,
        )
        await queue.close()

    @property
    def agents_as_tools(self) -> List[ChatCompletionToolParam]:
        """返回可以作为工具使用的agents字典

        Returns:
            Dict[str, BaseAgent]: 字典的key是agent id，value是可以作为工具使用的agent类
        """
        return [
            create_tool(
                name=agent.id,
                description=agent.description,
                parameters=AgentParameters,
                strict=True,
            )
            for agent in self._agents.values()
        ]


agent_registry = AgentRegistry()