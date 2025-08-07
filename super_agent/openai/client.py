"""基于OpenAI官方库的客户端，支持缓存。"""

from typing import Callable, TypeVar
from openai import OpenAI, OpenAI as OpenAIClient
from cachetools import TTLCache, cached
from super_agent.settings import Model_Config

T = TypeVar("T")


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

    assert isinstance(options, Model_Config), "Options 必须是 Model_Config 实例"

    return client(**options.model_dump())


if __name__ == '__main__':
    from super_agent.settings import settings

    # 打印当前OpenAI模型配置
    print(settings.openai_model_config)

    # 初始化OpenAI客户端
    client = get_client(OpenAIClient, settings.openai_model_config)

    # 构造消息和工具
    messages = [
        {
            "role": "user",
            "content": "鞠婧祎是谁？"
        }
    ]
    tools = [
        {
            "type": "function",
            "function": {
                "name": "search",
                "description": 
                    "通过query进行网页搜索"
                ,
                "parameters": {
                    "properties": {
                        "query": {
                            "title": "用户输入的需要检索的关键字",
                            "type": "string"
                        },
                        "max_results": {
                            "type": "integer",
                            "title": "Max Results"
                        }
                    },
                    "required": ["query"],
                    "title": "search",
                    "type": "object",
                    "additionalProperties": False
                },
                "strict": True
            }
        }
    ]
    # 使用OpenAI官方库进行调用,流式输出
    # response = client.chat.completions.create(
    #     model="llama3.2",
    #     messages=messages,
    #     temperature=0.5,
    #     # tools=tools,
    #     tool_choice="auto",
    #     stream=False,
    # )
    # print(response)
    # 使用OpenAI官方库进行调用,流式输出
    response = client.chat.completions.create(
        model="llama3.2",
        messages=messages,
        temperature=0.5,
        # tools=tools,
        tool_choice="auto",
        stream=True
    )

    for chunk in response:
        print(chunk.choices[0].delta, end="")