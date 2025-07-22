"""用于创建工具选择和函数的工具函数"""

from typing import Any, List, Optional

from openai.types.chat.chat_completion_named_tool_choice_param import (
    ChatCompletionNamedToolChoiceParam,
    Function,
)
from openai.types.chat.chat_completion_tool_param import ChatCompletionToolParam
from openai.types.shared_params import FunctionDefinition
from pydantic import BaseModel


def create_tool(
    name: str,
    description: str,
    parameters: dict[str, Any] | type[BaseModel],
    strict: bool = False,
    exclude: Optional[List[str]] = None,
    defaults: Optional[dict[str, Any]] = None,
) -> ChatCompletionToolParam:
    """创建用于OpenAI API的工具定义

    Args:
        name (str): 要调用的函数名称
        description (str): 函数功能的描述
        parameters (dict[str, Any] | BaseModel): 函数的参数
        strict (bool, optional): 是否严格调用函数。默认为False
        exclude (Optional[List[str]], optional): 要从参数中排除的属性。默认为None
        defaults (Optional[dict[str, Any]], optional): 参数的默认值，这些参数将从模式中排除，并应在LLM响应后默认设置。默认为None

    Returns:
        ChatCompletionToolParam: 函数定义
    """
    schema: dict[str, Any] = {}
    schema = (
        parameters if isinstance(parameters, dict) else parameters.model_json_schema()
    )

    # 移除排除的属性和默认属性
    _exclude = []
    if exclude:
        _exclude.extend(exclude)
    if defaults:
        _exclude.extend(defaults.keys())

    for key in _exclude or []:
        schema["properties"].pop(key, None)

    if not schema:
        raise ValueError("参数必须是Pydantic模型或字典")

    if strict:
        # 确保additionalProperties设置为False
        schema["additionalProperties"] = False

        if "$defs" in schema:
            for _, value in schema["$defs"].items():
                value["additionalProperties"] = False

                # 检查required字段
                if "required" not in value:
                    value["required"] = []
                for key in value.get("properties", []):
                    if key not in value["required"]:
                        value["required"].append(key)

    # 递归移除`default`或`format`等属性
    def remove_default(obj):
        if isinstance(obj, dict):
            obj.pop("default", None)
            obj.pop("format", None)
            obj.pop("examples", None)
            obj.pop("maximum", None)
            obj.pop("minimum", None)
            for _, value in obj.items():
                remove_default(value)
        elif isinstance(obj, list):
            for item in obj:
                remove_default(item)

    remove_default(schema)

    # 确保每个属性都在required列表中
    if "required" not in schema:
        schema["required"] = []

    for key in schema["properties"]:
        if key not in schema["required"]:
            schema["required"].append(key)

    return ChatCompletionToolParam(
        type="function",
        function=FunctionDefinition(
            name=name,
            description=description,
            parameters=schema,
            strict=strict,
        ),
    )


def tool_choice(name: str) -> ChatCompletionNamedToolChoiceParam:
    """创建用于OpenAI API的命名工具选择

    Args:
        name (str): 工具选择的名称

    Returns:
        ChatCompletionNamedToolChoiceParam: 命名工具选择
    """
    return ChatCompletionNamedToolChoiceParam(
        type="function", function=Function(name=name)
    )