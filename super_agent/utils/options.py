"""Options module for the example."""

import inspect
from functools import wraps
from typing import Callable, ParamSpec, Type, TypeVar, Union

from pydantic import BaseModel, ConfigDict, ValidationError

# Define a generic type variable bound to BaseOptions.
T = TypeVar("T", bound="BaseModel")
P = ParamSpec("P")
R = TypeVar("R")


def validate_options(expected: Type[T]) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Convert options to expected type.

    This decorator inspects the 'options' argument:
      - If it is a dict, it converts it using `expected.model_validate`.
      - Otherwise, it passes the value along as-is.

    Note:
      For best type checking, consider annotating your function's `options` parameter
      as Union[T, dict] so that both types are accepted by static checkers.

    """
    if not issubclass(expected, BaseModel):
        raise ValueError("The expected type must be a subclass of BaseModel.")

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            # Bind the arguments to the function's signature.
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # If 'options' is present, validate it
            if "options" in bound_args.arguments:
                value = bound_args.arguments["options"]
                try:
                    if isinstance(value, dict):
                        # Convert nested dict values to their expected types
                        if "tool_call" in value and isinstance(value["tool_call"], dict):
                            from openai.types.chat.chat_completion_message_tool_call import ChatCompletionMessageToolCall
                            value["tool_call"] = ChatCompletionMessageToolCall(**value["tool_call"])
                        bound_args.arguments["options"] = expected.model_validate(value)
                    elif not isinstance(value, expected):
                        raise ValueError(f"Options must be of type {expected} or dict")
                except ValidationError as e:
                    raise ValueError(f"Invalid options: {e.errors()}") from e
                    
            return func(*bound_args.args, **bound_args.kwargs)

        return wrapper

    return decorator


class BaseOptions(BaseModel):
    """Base options for the example."""

    model_config = ConfigDict(extra="allow")