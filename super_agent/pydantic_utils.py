"""用于处理Pydantic模型的工具函数"""

import inspect
from typing import Any, Dict, List, Optional, Sequence, Type, TypeGuard, TypeVar, Union

from pydantic import BaseModel, ConfigDict, create_model, Field


class ConfiguredBaseModel(BaseModel):
    """带有自定义配置的Pydantic基础模型"""

    model_config = ConfigDict(
        extra="forbid",  # 禁止额外字段
        validate_assignment=True,  # 赋值时验证
        arbitrary_types_allowed=True,  # 允许任意类型
    )


T = TypeVar("T", bound=BaseModel)


def is_basemodel_type(cls: Any) -> TypeGuard[type[BaseModel]]:
    """检查给定类型是否为Pydantic BaseModel

    Args:
        cls (Any): 要检查的类型

    Returns:
        TypeGuard[type[pydantic.BaseModel]]: 如果是Pydantic BaseModel返回True，否则返回False
    """
    if not inspect.isclass(cls):
        return False

    return issubclass(cls, BaseModel)


def create_simple_model(
    model_name: str, fields: Sequence[str]
) -> type[T]:  # pyright: ignore[reportInvalidTypeVarUse]
    """动态创建具有指定字段的Pydantic模型

    **假设所有字段类型都是字符串，都是必需的且没有默认值**

    如果需要更多控制字段定义，请直接使用`pydantic`的`create_model`

    Args:
        model_name (str): 要创建的模型名称
        fields (Sequence[str]): 要包含在模型中的字段名称序列

    Returns:
        T: 具有指定字段的动态创建的Pydantic模型类
    """
    field_definitions = {field: (str, ...) for field in fields}

    return create_model(model_name, **field_definitions)  # type: ignore


def model_from_schema(
    name: str,
    schema: Dict[str, Any],
    definitions: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Type[BaseModel]:
    """
    根据JSON Schema动态创建Pydantic模型，保留所有字段（如title、description、default等元信息）。

    支持：
      - $ref 解析（仅内部 #/definitions 或 #/$defs）
      - 嵌套对象和数组
      - 默认值、必需字段
      - 字段元信息（如title、description、default等）全部保留

    参数:
        name: 生成的Pydantic模型名称
        schema: JSON schema字典
        definitions: （可选）共享定义子schema的字典

    返回:
        动态生成的Pydantic BaseModel子类
    """

    definitions = definitions or {}
    for defs_key in ("definitions", "$defs"):
        if defs_key in schema and isinstance(schema[defs_key], dict):
            definitions.update(schema[defs_key])

    def _resolve_ref(ref: str) -> Dict[str, Any]:
        # 只支持内部引用 '#/definitions/...'
        if not ref.startswith("#/"):
            raise ValueError(f"Unsupported reference: {ref}")
        parts = ref.lstrip("#/").split("/")
        target: Any = schema
        for part in parts:
            target = target.get(part)
            if target is None:
                raise KeyError(f"Reference path not found: {ref}")
        return target

    def _build(subschema: Dict[str, Any], model_name: str) -> Any:
        # 处理$ref
        if "$ref" in subschema:
            ref_schema = _resolve_ref(subschema["$ref"])
            return _build(ref_schema, model_name)

        schema_type = subschema.get("type")

        if schema_type == "array":
            items = subschema.get("items", {})
            item_type = _build(items, f"{model_name}Item")
            return List[item_type]  # type: ignore

        if schema_type == "object":
            properties = subschema.get("properties", {})
            required_fields = set(subschema.get("required", []))
            fields: Dict[str, Any] = {}

            for field_name, field_schema in properties.items():
                field_type = _build(field_schema, f"{model_name}{field_name.capitalize()}")
                field_kwargs = {
                    k: field_schema[k]
                    for k in ("title", "description", "example", "examples", "enum")
                    if k in field_schema
                }

                default_value = field_schema.get("default")
                is_required = field_name in required_fields

                if not is_required and default_value is None:
                    field_type = Optional[field_type]  # type: ignore

                if default_value is not None:
                    fields[field_name] = (field_type, Field(default=default_value, **field_kwargs))
                else:
                    fields[field_name] = (field_type, Field(..., **field_kwargs)) if is_required else (field_type, Field(**field_kwargs))

            return create_model(model_name, __base__=BaseModel, **fields)  # type: ignore

        mapping = {"string": str, "integer": int, "number": float, "boolean": bool, "object": dict, "array": list}
        return mapping.get(schema_type, Any)

    top_level_model = _build(schema, name)

    if isinstance(top_level_model, type) and issubclass(top_level_model, BaseModel):
        top_level_model.__name__ = name
        return top_level_model  # type: ignore

    # model = create_model(name, __base__=BaseModel, value=(top_level_model, ...))
    # return model
    return top_level_model


def convert_mcp_to_openai_tools(mcp_tools: list) -> list:
    """
    将MCP Server返回的工具列表转换为OpenAI函数调用格式

    参数：
        mcp_tools: MCP工具列表，每个元素需包含name, description, inputSchema字段

    返回：
        符合OpenAI函数调用规范的JSON对象列表
    """

    openai_tools = []  # 用来存放转换后的工具列表

    for tool in mcp_tools.tools:  # 遍历每一个MCP工具
        # 第一步：创建OpenAI工具的基本框架
        tool_schema = {
            "type": "function",  # 告诉OpenAI这是一个函数工具
            "function": {
                "name": tool.name,           # 工具名称，比如"search_weather"
                "description": tool.description,  # 工具描述，让AI知道这个工具是干什么的
                "parameters": {}             # 参数部分，稍后会填充
            }
        }

        # 第二步：获取MCP工具的参数定义
        input_schema = tool.inputSchema  # 这里包含了工具需要什么参数

        # 第三步：转换参数格式
        parameters = {
            "type": input_schema['type'],  # 参数类型，通常是"object"（对象）
            "properties": input_schema['properties'],  # 具体的参数定义
            "required": input_schema['required'],      # 哪些参数是必须的
            "additionalProperties": False  # 不允许额外参数，这是安全考虑
        }

        # 第四步：特殊处理枚举类型参数
        # 如果参数有固定的可选值，我们要让AI更清楚地知道
        for prop in parameters["properties"].values():
            if "enum" in prop:  # 如果这个参数有枚举值（比如颜色只能是红、绿、蓝）
                # 把可选值写进描述里，让AI更容易理解
                prop["description"] = f"可选值: {', '.join(prop['enum'])}"

        # 第五步：把处理好的参数放回工具定义中
        tool_schema["function"]["parameters"] = parameters
        openai_tools.append(tool_schema)  # 添加到结果列表

    print("\nconverte to openai tools success:", [openai_tools])
    return openai_tools  # 返回转换完成的工具列表


if __name__ == '__main__':
    schema={'properties': {'query': {'title': '用户输入', 'type': 'string'}, 'max_results': {'default': 5, 'title': '返回的最大搜索结果数', 'type': 'integer'}}, 'required': ['query'], 'title': 'searchArguments', 'type': 'object'}
    print("调用前：",schema)
    res=model_from_schema(name="search",schema=schema)
    print("调用后：",res.model_json_schema())