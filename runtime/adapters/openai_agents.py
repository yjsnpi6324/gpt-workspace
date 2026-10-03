"""Optional OpenAI Agents boundary; importing it never imports a provider SDK."""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from typing import Any, NoReturn, Protocol

from runtime.contracts import ErrorType, RunResult, Task


class AgentsResult(Protocol):
    final_output: Any
    interruptions: Sequence[Any]


class AgentsRunner(Protocol):
    async def run(
        self, starting_agent: Any, input: str, *, context: Task,
        max_turns: int, run_config: Any,
    ) -> AgentsResult: ...


class ToolExecutionError(RuntimeError):
    """An owned tool failed instead of returning a model-visible error string."""


def raise_tool_error(context: Any, error: Exception) -> NoReturn:
    """Inject as function_tool(failure_error_function=raise_tool_error)."""
    raise ToolExecutionError(str(error).strip() or type(error).__name__) from error


class OpenAIAgentsAdapter:
    """Translate one injected, non-streaming Runner.run into the neutral contract."""

    def __init__(
        self, *, agent: Any, runner: AgentsRunner, run_config: Any = None,
        max_turns: int = 10,
        invalid_input_errors: tuple[type[Exception], ...] = (),
        tool_errors: tuple[type[Exception], ...] = (),
        permission_errors: tuple[type[Exception], ...] = (),
    ) -> None:
        if type(max_turns) is not int or max_turns < 1:
            raise ValueError("max_turns must be a positive integer")
        for errors in (invalid_input_errors, tool_errors, permission_errors):
            if not isinstance(errors, tuple) or any(
                not isinstance(error, type) or not issubclass(error, Exception)
                for error in errors
            ):
                raise TypeError("failure mappings must be tuples of Exception types")
        self._agent = agent
        self._runner = runner
        self._run_config = run_config
        self._max_turns = max_turns
        self._invalid_input_errors = invalid_input_errors
        self._tool_errors = (ToolExecutionError, *tool_errors)
        self._permission_errors = (PermissionError, *permission_errors)

    @classmethod
    def from_sdk(
        cls, *, agent: Any, run_config: Any = None, max_turns: int = 10,
    ) -> OpenAIAgentsAdapter:
        """Opt into the SDK at composition time; callers own agents and clients."""
        try:
            from agents import RunConfig, Runner
            from agents.exceptions import (
                InputGuardrailTripwireTriggered, MCPToolCancellationError,
                ModelRefusalError, OutputGuardrailTripwireTriggered,
                ToolInputGuardrailTripwireTriggered,
                ToolOutputGuardrailTripwireTriggered, ToolTimeoutError, UserError,
            )
            from openai import (
                AuthenticationError, BadRequestError, PermissionDeniedError,
                UnprocessableEntityError,
            )
        except ImportError as error:
            raise ImportError(
                "OpenAI Agents binding requires the optional dependencies in "
                "requirements-openai-agents.txt"
            ) from error
        return cls(
            agent=agent, runner=Runner,
            run_config=(
                RunConfig(tracing_disabled=True) if run_config is None else run_config
            ),
            max_turns=max_turns,
            invalid_input_errors=(UserError, BadRequestError, UnprocessableEntityError),
            tool_errors=(ToolTimeoutError, MCPToolCancellationError),
            permission_errors=(
                AuthenticationError, PermissionDeniedError, ModelRefusalError,
                InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered,
                ToolInputGuardrailTripwireTriggered, ToolOutputGuardrailTripwireTriggered,
            ),
        )

    def _classify(self, error: Exception) -> ErrorType:
        # The SDK wraps tool errors in UserError; inspect explicit causes only.
        causes: list[BaseException] = []
        seen: set[int] = set()
        cause: BaseException | None = error
        while cause is not None and id(cause) not in seen:
            if isinstance(cause, asyncio.CancelledError):
                raise cause
            seen.add(id(cause))
            causes.append(cause)
            cause = cause.__cause__
        for types, category in (
            (self._permission_errors, ErrorType.PERMISSION_DENIED),
            (self._tool_errors, ErrorType.TOOL_ERROR),
            (self._invalid_input_errors, ErrorType.INVALID_INPUT),
        ):
            if any(isinstance(cause, types) for cause in causes):
                return category
        return ErrorType.RUNTIME_ERROR

    @staticmethod
    def _failure(task: Task, category: ErrorType, error: Exception) -> RunResult:
        return RunResult.failure(
            task.task_id, category, str(error).strip() or type(error).__name__,
        )

    async def run(self, task: Task) -> RunResult:
        try:
            task.validate()
        except (ValueError, TypeError, AttributeError) as error:
            return self._failure(task, ErrorType.INVALID_INPUT, error)

        try:
            result = await self._runner.run(
                self._agent, task.input, context=task,
                max_turns=self._max_turns, run_config=self._run_config,
            )
            interruptions = result.interruptions
            if not isinstance(interruptions, Sequence) or isinstance(
                interruptions, (str, bytes)
            ):
                raise TypeError("Runner result requires an interruptions sequence")
            if interruptions:
                return RunResult.failure(
                    task.task_id, ErrorType.PERMISSION_DENIED,
                    "Run interrupted pending tool approval",
                )
            if not isinstance(result.final_output, str):
                raise TypeError("Runner final_output must be a string")
            return RunResult.success(task.task_id, result.final_output)
        except asyncio.CancelledError:
            # Cancellation is control flow, including SDK subclasses of Exception.
            raise
        except Exception as error:
            return self._failure(task, self._classify(error), error)
