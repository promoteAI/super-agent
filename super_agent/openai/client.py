"""Client for OpenAI with caching support."""

from typing import (
    Callable,
    TypeVar,
)

from cachetools import TTLCache, cached
from openai import OpenAI
from super_agent.settings import Model_Config

T = TypeVar("T", bound=OpenAI)


def _hashable_dict(d: dict) -> tuple:
    """Convert a dictionary to a hashable tuple."""
    return tuple((k, v) for k, v in sorted(d.items()))


@cached(cache=TTLCache(maxsize=1, ttl=1800), key=lambda _, options: _hashable_dict(options.model_dump()))
def get_client(
    client: Callable[..., T], options: Model_Config
) -> T:
    """Initialize and returns an instance of the specified client using the provided credentials or options.

    Args:
        client (Callable[..., T]): The client class or factory function to instantiate.
        options (Model_Config): Configuration options for the client.

    Returns:
        T: An instance of the specified client, initialized with the provided options.
    """

    assert isinstance(options, Model_Config), "Options must be a Model_Config instance"

    return client(**options.model_dump())

if __name__ == '__main__':
    from super_agent.settings import settings
    print(settings.openai_model_config)
    client = get_client(
        OpenAI,
        options=settings.openai_model_config,
    )
    messages = [
      {
        "role": "user",
        "content": "What is the weather like in Paris today?"
      }
    ]
    resp=client.chat.completions.create(
        messages=messages,
        model="deepseek-r1-distill-qwen-7b",
        temperature=0.5,
        tools= [
      {
        "type": "function",
        "function": {
          "name": "get_weather",
          "description": "Get current temperature for a given location.",
          "parameters": {
            "type": "object",
            "properties": {
              "location": {
                "type": "string",
                "description": "City and country (e.g., Bogotá, Colombia)"
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