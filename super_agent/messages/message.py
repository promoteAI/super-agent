"""聊天补全的消息数据类"""

from typing import Annotated, Literal, Optional

from pydantic import BaseModel, Field

from super_agent.messages.create import ChatCompletionMessageParam, create_message


class Audio(BaseModel):
    """模型之前的音频响应数据"""

    id: str
    """模型之前音频响应的唯一标识符"""


class Function(BaseModel):
    """要调用的函数"""

    arguments: str
    """
    调用函数时使用的参数，由模型生成的JSON格式。
    注意：模型生成的JSON不一定有效，可能会生成函数模式中未定义的参数。
    在调用函数之前，请在你的代码中验证这些参数。
    """

    name: str
    """要调用的函数名称"""


class ToolCall(BaseModel):
    """应用于搜索的工具调用"""

    id: str
    """工具调用的ID"""

    function: Function
    """模型调用的函数"""

    type: Literal["function"]
    """工具的类型。目前仅支持`function`"""


class ChatMessage(BaseModel):
    """聊天补全消息"""

    content: Optional[str] = None
    """系统消息的内容"""

    role: Literal["system", "user", "assistant", "tool", "function"]
    """消息作者的角色"""

    name: Optional[str] = None
    """参与者的可选名称。

    为模型提供信息以区分相同角色的参与者。
    """

    audio: Optional[Audio] = None
    """模型之前音频响应的数据。

    [了解更多](https://platform.openai.com/docs/guides/audio)
    """

    refusal: Optional[str] = None
    """助手的拒绝消息"""

    toolCalls: Annotated[Optional[list[ToolCall]], Field(alias="tool_calls")] = None
    """模型生成的工具调用，例如函数调用"""

    toolCallId: Annotated[Optional[str], Field(alias="tool_call_id")] = None
    """此消息正在响应的工具调用"""

    @property
    def as_type(self) -> ChatCompletionMessageParam:
        """将消息内容转换为ChatCompletionMessageParam类型"""
        return create_message(**self.model_dump(by_alias=True))