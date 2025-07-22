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
        {"role": "system", "content": "你是一个有帮助的助手"},
        {"role": "user", "content": "你好，请帮我写一封感谢信"}
    ]
    resp=client.chat.completions.create(
        messages=messages,
        model="gemma2",
        temperature=0.5
    )
    print(resp)