"""Optional real SDK compatibility tests: scripted models, no keys or network."""

import os
import socket
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx2
from agents import (
    Agent, GuardrailFunctionOutput, Model, RunConfig, Runner, Usage,
    function_tool, input_guardrail,
)
from agents.exceptions import (
    MCPToolCancellationError, MaxTurnsExceeded, ModelBehaviorError,
    ModelRefusalError, ModelTimeoutError, ToolTimeoutError, UserError,
)
from agents.items import ModelResponse
from openai import AuthenticationError, BadRequestError, PermissionDeniedError
from openai.types.responses import (
    ResponseFunctionToolCall, ResponseOutputMessage, ResponseOutputText,
)

from runtime.adapters.openai_agents import OpenAIAgentsAdapter, raise_tool_error
from runtime.contracts import ErrorType, RunStatus, Task


def text_output(text):
    return [ResponseOutputMessage(
        id="message-fixture", role="assistant", status="completed", type="message",
        content=[ResponseOutputText(text=text, annotations=[], type="output_text")],
    )]


def tool_call(name):
    return [ResponseFunctionToolCall(
        id="tool-fixture", call_id="call-fixture", name=name,
        arguments="{}", type="function_call",
    )]


class ScriptedModel(Model):
    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.calls = 0

    async def get_response(self, *args, **kwargs):
        self.calls += 1
        if not self.outputs:
            raise AssertionError("unexpected model call")
        return ModelResponse(
            output=self.outputs.pop(0), usage=Usage(), response_id="response-fixture",
        )

    def stream_response(self, *args, **kwargs):
        raise AssertionError("streaming is outside this adapter")


class OpenAIAgentsSDKTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.task = Task("sdk-1", "run fixture")
        self.addCleanup(patch.stopall)
        patch.dict(os.environ, {"OPENAI_API_KEY": ""}).start()
        self.network_mocks = [
            patch.object(target, name, side_effect=AssertionError("network forbidden")).start()
            for target, name in (
                (socket, "create_connection"), (socket.socket, "connect"),
                (socket.socket, "connect_ex"),
            )
        ]

    def tearDown(self):
        for mock in self.network_mocks:
            mock.assert_not_called()

    def assert_failure(self, result, category):
        self.assertIs(result.status, RunStatus.FAILED)
        self.assertIs(result.error_type, category)
        self.assertEqual(result.task_id, self.task.task_id)
        self.assertIsNone(result.output)
        self.assertTrue(result.error_message)

    async def test_real_runner_returns_text_with_tracing_disabled(self):
        model = ScriptedModel([text_output("verified metric")])
        adapter = OpenAIAgentsAdapter.from_sdk(agent=Agent(name="fixture", model=model))
        self.assertTrue(adapter._run_config.tracing_disabled)
        result = await adapter.run(self.task)
        self.assertIs(result.status, RunStatus.SUCCESS)
        self.assertEqual(result.output, "verified metric")
        self.assertEqual(model.calls, 1)

    async def test_real_tool_failures_cannot_turn_into_model_success(self):
        for error, category in (
            (ValueError("tool failed"), ErrorType.TOOL_ERROR),
            (PermissionError("tool denied"), ErrorType.PERMISSION_DENIED),
        ):
            with self.subTest(category=category):
                @function_tool(failure_error_function=raise_tool_error)
                def failing_tool() -> str:
                    """A deterministic failing tool."""
                    raise error

                model = ScriptedModel([
                    tool_call(failing_tool.name), text_output("fabricated success"),
                ])
                adapter = OpenAIAgentsAdapter.from_sdk(
                    agent=Agent(name="fixture", model=model, tools=[failing_tool]),
                )
                self.assert_failure(await adapter.run(self.task), category)
                self.assertEqual(model.calls, 1)

    async def test_real_tool_approval_is_failed_without_running_tool(self):
        calls = []

        @function_tool(needs_approval=True, failure_error_function=raise_tool_error)
        def protected_tool() -> str:
            """A tool requiring approval."""
            calls.append("executed")
            return "protected data"

        model = ScriptedModel([tool_call(protected_tool.name)])
        adapter = OpenAIAgentsAdapter.from_sdk(
            agent=Agent(name="fixture", model=model, tools=[protected_tool]),
        )
        self.assert_failure(await adapter.run(self.task), ErrorType.PERMISSION_DENIED)
        self.assertEqual(calls, [])

    async def test_real_input_guardrail_is_permission_denied(self):
        @input_guardrail(run_in_parallel=False)
        async def deny(context, agent, input):
            return GuardrailFunctionOutput(output_info="fixture", tripwire_triggered=True)

        model = ScriptedModel([text_output("fabricated success")])
        adapter = OpenAIAgentsAdapter.from_sdk(
            agent=Agent(name="fixture", model=model, input_guardrails=[deny]),
        )
        self.assert_failure(await adapter.run(self.task), ErrorType.PERMISSION_DENIED)
        self.assertEqual(model.calls, 0)

    async def test_sdk_exception_types_use_existing_failure_categories(self):
        response = httpx2.Response(
            403, request=httpx2.Request("POST", "https://fixture.invalid"),
        )
        cases = (
            (UserError("bad configuration"), ErrorType.INVALID_INPUT),
            (BadRequestError("bad request", response=response, body=None), ErrorType.INVALID_INPUT),
            (AuthenticationError("no access", response=response, body=None), ErrorType.PERMISSION_DENIED),
            (PermissionDeniedError("denied", response=response, body=None), ErrorType.PERMISSION_DENIED),
            (ModelRefusalError("refused"), ErrorType.PERMISSION_DENIED),
            (ToolTimeoutError("fixture", 1), ErrorType.TOOL_ERROR),
            (MCPToolCancellationError("tool cancelled"), ErrorType.TOOL_ERROR),
            (MaxTurnsExceeded("turn limit"), ErrorType.RUNTIME_ERROR),
            (ModelBehaviorError("malformed model output"), ErrorType.RUNTIME_ERROR),
            (ModelTimeoutError(1), ErrorType.RUNTIME_ERROR),
        )
        adapter = OpenAIAgentsAdapter.from_sdk(agent=Agent(name="fixture"))
        for error, category in cases:
            with self.subTest(error=type(error).__name__):
                with patch.object(Runner, "run", AsyncMock(side_effect=error)):
                    self.assert_failure(await adapter.run(self.task), category)

    async def test_sdk_binding_preserves_injected_run_configuration(self):
        config = RunConfig(tracing_disabled=True)
        agent = Agent(name="fixture")
        adapter = OpenAIAgentsAdapter.from_sdk(agent=agent, run_config=config, max_turns=2)
        with patch.object(Runner, "run", AsyncMock(return_value=SimpleNamespace(
            final_output="fixture", interruptions=[],
        ))) as run:
            await adapter.run(self.task)
            run.assert_awaited_once_with(
                agent, self.task.input, context=self.task, max_turns=2, run_config=config,
            )


if __name__ == "__main__":
    unittest.main()
