"""Client for OpenAI with caching support."""

from typing import (
    Callable,
    TypeVar,
)

from cachetools import TTLCache, cached
from litellm import completion
from super_agent.settings import Model_Config

T = TypeVar("T", bound=completion)


def _hashable_dict(d: dict) -> tuple:
    """将字典转换为可哈希的元组"""
    return tuple((k, v) for k, v in sorted(d.items()))


@cached(cache=TTLCache(maxsize=1, ttl=1800), key=lambda _, options: _hashable_dict(options.model_dump()))
def get_client(
    client: Callable[..., T], options: Model_Config
) -> T:
    """使用提供的凭据或选项初始化并返回指定客户端的实例

    Args:
        client (Callable[..., T]): 要实例化的客户端类或工厂函数
        options (Model_Config): 客户端的配置选项

    Returns:
        T: 使用提供的选项初始化的指定客户端的实例
    """

    assert isinstance(options, Model_Config), "Options must be a Model_Config instance"

    return client(**options.model_dump())

if __name__ == '__main__':
    from super_agent.settings import settings
    print(settings.openai_model_config)
    client = get_client(
        completion,
        options=settings.openai_model_config,
    )
    messages = [
      {
        "role": "user",
        "content": "北京今天天气如何？"
      }
    ]
    resp = client(
        messages=messages,
        model="ollama_chat/llama3.2",
        temperature=0.5,
        tools= [
      {
        "type": "function",
        "function": {
          "name": "get_weather",
          "description": "获取指定城市的当前天气",
          "parameters": {
            "type": "object",
            "properties": {
              "location": {
                "type": "string",
                "description": "城市名称"
              }
            },
            "required": ["location"],
            "additionalProperties": False
          },
          "strict": True
        }
      }
    ],
    tool_choice="auto"
    )
    print(resp)