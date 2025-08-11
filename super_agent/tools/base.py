"""Base class for tools."""

import json
from typing import Any, Generic, Type, TypeVar, Union, overload

from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
)
from openai.types.chat.chat_completion_tool_param import ChatCompletionToolParam
from pydantic import BaseModel, PrivateAttr, ValidationError

from super_agent.messages.create import ChatCompletionToolMessageParam, create_message
from super_agent.openai_cli.tools import create_tool
from super_agent.utils.options import BaseOptions, validate_options

T = TypeVar("T", bound=BaseModel)


# region base tool
class BaseToolOptions(BaseOptions):
    """Options for the BaseTool agent."""

    tool_call: ChatCompletionMessageToolCall


class BaseTool(Generic[T]):
    """Base class for tools."""

    name: str
    description: str
    tool_call_schema: Type[T]

    strict: bool = True
    """Whether to enforce strict validation of tool arguments."""

    _tool_call_id: str | None = PrivateAttr(default=None)
    _tool_args: T | None = PrivateAttr(default=None)

    @overload
    async def run(self, options: BaseToolOptions) -> ChatCompletionToolMessageParam: ...

    @overload
    async def run(self, options: dict[str, Any]) -> ChatCompletionToolMessageParam: ...

    @validate_options(BaseToolOptions)
    async def run(
        self, options: Union[BaseToolOptions, dict[str, Any]]
    ) -> ChatCompletionToolMessageParam:
        """Invoke the tool asynchronously."""
        raise NotImplementedError("Method not implemented.")

    def initialise_tool_call(
        self, options: BaseToolOptions
    ) -> ChatCompletionToolMessageParam | None:
        """Initialise the tool with the provided options.

        Parses and validates the tool call arguments using the tool's schema. If validation fails,
        returns a tool message containing the validation error. If arguments are missing, returns
        a tool message indicating that tool arguments must be set. Otherwise, returns None.

        Args:
            options (BaseToolOptions): The options containing the tool call and its arguments.

        Returns:
            ChatCompletionToolMessageParam | None: A tool message with error details if validation
            fails, or None if initialization is successful.

        """
        self._tool_call_id = options.tool_call.id

        try:
            args = json.loads(options.tool_call.function.arguments)
            self._tool_args = self.tool_call_schema.model_validate(args)
        except ValidationError as err:
            # add a message for the agent
            return create_message(
                content=err.json(include_url=False),
                role="tool",
                name=self.name,
                tool_call_id=options.tool_call.id,
            )

        if not self._tool_args:
            return create_message(
                content="Tool args must be set.",
                role="tool",
                name=self.name,
                toolCallId=options.tool_call.id,
            )

        return None

    @property
    def card(self) -> ChatCompletionToolParam:
        """Return the tool card representation."""
        return create_tool(
            self.name, self.description, self.tool_call_schema, strict=self.strict
        )


# endregion base tool