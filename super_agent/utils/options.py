"""Options module for the example."""

import inspect
from functools import wraps
from typing import Callable, ParamSpec, Type, TypeVar

from pydantic import BaseModel, ConfigDict

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

            # If 'options' is present and is a dict, validate it.
            if "options" in bound_args.arguments:
                value = bound_args.arguments["options"]
                if isinstance(value, dict):
                    bound_args.arguments["options"] = expected.model_validate(value)
            return func(*bound_args.args, **bound_args.kwargs)

        return wrapper

    return decorator


class BaseOptions(BaseModel):
    """Base options for the example."""

    model_config = ConfigDict(extra="allow")