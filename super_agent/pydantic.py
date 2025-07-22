"""用于处理Pydantic模型的工具函数"""

import inspect
from typing import Any, Dict, List, Optional, Sequence, Type, TypeGuard, TypeVar

import pydantic
from pydantic import BaseModel, ConfigDict, create_model


class ConfiguredBaseModel(BaseModel):
    """带有自定义配置的Pydantic基础模型"""

    model_config = ConfigDict(
        extra="forbid",  # 禁止额外字段
        validate_assignment=True,  # 赋值时验证
        arbitrary_types_allowed=True,  # 允许任意类型
    )


T = TypeVar("T", bound=pydantic.BaseModel)


def is_basemodel_type(cls: Any) -> TypeGuard[type[pydantic.BaseModel]]:
    """检查给定类型是否为Pydantic BaseModel

    Args:
        cls (Any): 要检查的类型

    Returns:
        TypeGuard[type[pydantic.BaseModel]]: 如果是Pydantic BaseModel返回True，否则返回False
    """
    if not inspect.isclass(cls):
        return False

    return issubclass(cls, pydantic.BaseModel)


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
    """从JSON schema动态创建Pydantic模型

    支持：
      - $ref解析（通过#/definitions或#/$defs的内部引用）
      - 嵌套对象和数组
      - 默认值和必填字段

    Args:
        name: 生成的Pydantic模型名称
        schema: JSON schema字典
        definitions: （内部）共享定义子schema的字典

    Returns:
        动态生成的Pydantic BaseModel子类
    """
    # 从根schema收集定义
    definitions = definitions or {}
    for defs_key in ("definitions", "$defs"):
        if defs_key in schema and isinstance(schema[defs_key], dict):
            definitions.update(schema[defs_key])

    def _resolve_ref(ref: str) -> Dict[str, Any]:
        # 仅支持'#/definitions/...'形式的内部引用
        if not ref.startswith("#/"):
            raise ValueError(f"不支持的引用: {ref}")
        parts = ref.lstrip("#/").split("/")
        target: Any = schema
        for part in parts:
            target = target.get(part)
            if target is None:
                raise KeyError(f"未找到引用路径: {ref}")
        return target

    def _build(subschema: Dict[str, Any], model_name: str) -> Any:
        # 处理$ref
        if "$ref" in subschema:
            ref_schema = _resolve_ref(subschema["$ref"])
            return _build(ref_schema, model_name)

        schema_type = subschema.get("type")
        # 数组：递归构建项目类型
        if schema_type == "array":
            items = subschema.get("items", {})
            item_type = _build(items, model_name + "Item")
            return List[item_type]  # type: ignore

        # 对象：构建嵌套的BaseModel
        if schema_type == "object":
            props = subschema.get("properties", {})
            required = set(subschema.get("required", []))
            fields: Dict[str, Any] = {}
            for prop_name, prop_schema in props.items():
                field_type = _build(prop_schema, model_name + prop_name.capitalize())
                # 确定默认值
                if prop_name in required:
                    default = prop_schema.get("default", ...)
                else:
                    default = prop_schema.get("default", None)
                    field_type = Optional[field_type]  # type: ignore
                fields[prop_name] = (field_type, default)

            # 创建并返回新的Pydantic模型
            return create_model(model_name, __base__=BaseModel, **fields)  # type: ignore

        # 基本类型映射
        mapping = {
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
            # 如果没有详细的props/items，则作为对象/数组的回退
            "object": dict,
            "array": list,
        }
        if schema_type in mapping:
            return mapping[schema_type]

        # 如果没有类型，允许任何类型
        return Any

    # 构建并返回顶层模型
    top_model = _build(schema, name)
    if isinstance(top_model, type) and issubclass(top_model, BaseModel):
        top_model.__name__ = name
        return top_model  # type: ignore
    # 如果顶层schema不是对象，则包装成具有单个字段'value'的模型
    return create_model(name, __base__=BaseModel, value=(top_model, ...))  # type: ignore