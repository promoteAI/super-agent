"""OpenAI模块的工具函数"""

from typing import Iterable, Literal, Union, overload

from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionContentPartParam,
    ChatCompletionContentPartTextParam,
    ChatCompletionFunctionMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionMessageToolCallParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)


@overload
def create_message(
    content: Union[str, Iterable[ChatCompletionContentPartTextParam]],
    role: Literal["user"],
    name: Union[str, None] = None,
    tool_call_id: None = None,
    refusal: None = None,
    tool_calls: None = None,
) -> ChatCompletionUserMessageParam: ...


@overload
def create_message(
    content: str,
    role: Literal["assistant"],
    name: Union[str, None] = None,
    tool_call_id: None = None,
    refusal: Union[str, None] = None,
    tool_calls: Union[Iterable[ChatCompletionMessageToolCallParam], None] = None,
) -> ChatCompletionAssistantMessageParam: ...


@overload
def create_message(
    content: Union[str, Iterable[ChatCompletionContentPartTextParam]],
    role: Literal["system"],
    name: Union[str, None] = None,
    tool_call_id: None = None,
    refusal: None = None,
    tool_calls: None = None,
) -> ChatCompletionSystemMessageParam: ...


@overload
def create_message(
    content: Union[str, Iterable[ChatCompletionContentPartTextParam]],
    role: Literal["tool"],
    name: str,
    tool_call_id: str,
    refusal: None = None,
    tool_calls: None = None,
) -> ChatCompletionToolMessageParam: ...


@overload
def create_message(
    content: Union[str, Iterable[ChatCompletionContentPartTextParam]],
    role: Literal["tool"],
    name: None,
    tool_call_id: str,
    refusal: None = None,
    tool_calls: None = None,
) -> ChatCompletionToolMessageParam: ...


@overload
def create_message(
    content: str,
    role: Literal["function"],
    name: Union[str, None] = None,
    tool_call_id: None = None,
    refusal: None = None,
    tool_calls: None = None,
) -> ChatCompletionFunctionMessageParam: ...


def create_message(  # pylint: disable=unused-argument
    content: Union[
        str,
        Iterable[ChatCompletionContentPartTextParam],
        Iterable[ChatCompletionContentPartParam],
    ],
    role: Literal["system", "user", "assistant", "tool", "function"],
    name: Union[str, None] = None,
    tool_call_id: Union[str, None] = None,
    refusal: Union[str, None] = None,
    tool_calls: Union[Iterable[ChatCompletionMessageToolCallParam], None] = None,
    **kwargs,
) -> ChatCompletionMessageParam:
    """创建OpenAI API的消息参数

    Args:
        content (Union[str, Iterable[ChatCompletionContentPartTextParam], Iterable[ChatCompletionContentPartParam]]):
            消息内容
        role (Literal["system", "user", "assistant", "tool", "function"]): 消息角色
        name (Union[str, None]): 消息名称
        tool_call_id (Union[str, None]): 工具调用ID
        refusal (Union[str, None]): 拒绝消息
        tool_calls (Union[Iterable[ChatCompletionMessageToolCallParam], None]): 工具调用
        **kwargs: 其他关键字参数

    Returns:
            ChatCompletionMessageParam: 消息参数对象
    """
    args = {
        "content": content,
        "role": role,
        "name": name,
        "tool_call_id": tool_call_id,
        "refusal": refusal,
        "tool_calls": tool_calls,
    }
    # 过滤掉值为None的参数
    args = {k: v for k, v in args.items() if v is not None}

    if role == "agent":
        # 将A2A的agent角色映射为OpenAI的assistant角色
        role = "assistant"
        args["role"] = "assistant"

    match role:
        case "system":
            return ChatCompletionSystemMessageParam(**args)
        case "user":
            return ChatCompletionUserMessageParam(**args)
        case "assistant":
            return ChatCompletionAssistantMessageParam(**args)
        case "tool":
            return ChatCompletionToolMessageParam(**args)
        case "function":
            return ChatCompletionFunctionMessageParam(**args)
        case _:
            raise ValueError("无效的角色")