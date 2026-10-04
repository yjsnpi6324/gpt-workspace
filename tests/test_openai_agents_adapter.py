import asyncio
import subprocess
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from runtime.adapters.openai_agents import (
    OpenAIAgentsAdapter, ToolExecutionError, raise_tool_error,
)
from runtime.contracts import ErrorType, RunStatus, Task


class InputFailure(Exception):
    pass


class ToolFailure(Exception):
    pass


class AccessFailure(Exception):
    pass


class SDKCancellation(asyncio.CancelledError, Exception):
    pass


class OpenAIAgentsAdapterTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.task = Task("adapter-1", "look up metric", {"source": "fixture"})
        self.agent = object()
        self.config = object()
        self.runner = SimpleNamespace(run=AsyncMock(
            return_value=SimpleNamespace(final_output="verified metric", interruptions=[])
        ))
        self.adapter = OpenAIAgentsAdapter(
            agent=self.agent, runner=self.runner, run_config=self.config, max_turns=3,
            invalid_input_errors=(InputFailure,), tool_errors=(ToolFailure,),
            permission_errors=(AccessFailure,),
        )

    def assert_failure(self, result, category):
        self.assertEqual(result.task_id, self.task.task_id)
        self.assertIs(result.status, RunStatus.FAILED)
        self.assertIs(result.error_type, category)
        self.assertIsNone(result.output)
        self.assertTrue(result.error_message.strip())

    async def test_success_forwards_injected_dependencies_and_task(self):
        result = await self.adapter.run(self.task)
        self.assertEqual(result.task_id, self.task.task_id)
        self.assertIs(result.status, RunStatus.SUCCESS)
        self.assertEqual(result.output, "verified metric")
        self.assertIsNone(result.error_type)
        self.assertIsNone(result.error_message)
        self.runner.run.assert_awaited_once_with(
            self.agent, self.task.input, context=self.task,
            max_turns=3, run_config=self.config,
        )

    async def test_empty_string_remains_valid_contract_output(self):
        self.runner.run.return_value.final_output = ""
        result = await self.adapter.run(self.task)
        self.assertIs(result.status, RunStatus.SUCCESS)
        self.assertEqual(result.output, "")

    async def test_invalid_tasks_never_invoke_runner(self):
        for task in (Task("", "x"), Task("  ", "x"), Task("valid", "  ")):
            with self.subTest(task=task):
                result = await self.adapter.run(task)
                self.assertIs(result.error_type, ErrorType.INVALID_INPUT)
                self.assertIs(result.status, RunStatus.FAILED)
                self.assertIsNone(result.output)
                self.assertEqual(result.task_id, task.task_id)
        self.runner.run.assert_not_called()

    async def test_exception_mapping_is_typed_and_stage_specific(self):
        cases = (
            (InputFailure("invalid"), ErrorType.INVALID_INPUT),
            (ToolFailure("tool failed"), ErrorType.TOOL_ERROR),
            (ToolExecutionError("tool failed"), ErrorType.TOOL_ERROR),
            (AccessFailure("denied"), ErrorType.PERMISSION_DENIED),
            (PermissionError("denied"), ErrorType.PERMISSION_DENIED),
            (RuntimeError("crash"), ErrorType.RUNTIME_ERROR),
            (ValueError("backend bug"), ErrorType.RUNTIME_ERROR),
            (TimeoutError("model timeout"), ErrorType.RUNTIME_ERROR),
            (type("UserError", (Exception,), {})("same name"), ErrorType.RUNTIME_ERROR),
        )
        for error, category in cases:
            with self.subTest(error=type(error).__name__):
                self.runner.run.side_effect = error
                self.assert_failure(await self.adapter.run(self.task), category)

    async def test_permission_mapping_has_precedence(self):
        adapter = OpenAIAgentsAdapter(
            agent=self.agent, runner=self.runner,
            invalid_input_errors=(AccessFailure,), tool_errors=(AccessFailure,),
            permission_errors=(AccessFailure,),
        )
        self.runner.run.side_effect = AccessFailure("denied")
        self.assert_failure(await adapter.run(self.task), ErrorType.PERMISSION_DENIED)

    async def test_malformed_results_cannot_be_success(self):
        responses = [None, object(), SimpleNamespace(final_output="partial")]
        responses += [
            SimpleNamespace(final_output=output, interruptions=[])
            for output in (None, False, 0, {}, ["text"])
        ]
        responses += [
            SimpleNamespace(final_output="text", interruptions=value)
            for value in (None, "", 0)
        ]
        for response in responses:
            with self.subTest(response=response):
                self.runner.run.return_value = response
                self.assert_failure(await self.adapter.run(self.task), ErrorType.RUNTIME_ERROR)

    async def test_interruption_discards_partial_output(self):
        self.runner.run.return_value = SimpleNamespace(
            final_output="fabricated success", interruptions=[object()],
        )
        self.assert_failure(await self.adapter.run(self.task), ErrorType.PERMISSION_DENIED)

    async def test_blank_errors_still_have_required_details(self):
        for message in ("", "  "):
            with self.subTest(message=message):
                self.runner.run.side_effect = RuntimeError(message)
                result = await self.adapter.run(self.task)
                self.assert_failure(result, ErrorType.RUNTIME_ERROR)
                self.assertEqual(result.error_message, "RuntimeError")

    async def test_tool_error_handler_preserves_cause_and_permissions(self):
        for error, category in (
            (ValueError("tool crash"), ErrorType.TOOL_ERROR),
            (PermissionError("tool denied"), ErrorType.PERMISSION_DENIED),
            (AccessFailure("provider denied"), ErrorType.PERMISSION_DENIED),
        ):
            with self.subTest(category=category):
                with self.assertRaises(ToolExecutionError) as caught:
                    raise_tool_error(None, error)
                self.assertIs(caught.exception.__cause__, error)
                self.runner.run.side_effect = caught.exception
                self.assert_failure(await self.adapter.run(self.task), category)

    async def test_cancellation_is_propagated(self):
        wrapped = InputFailure("wrapped cancellation")
        wrapped.__cause__ = SDKCancellation()
        for error in (asyncio.CancelledError(), SDKCancellation(), wrapped):
            with self.subTest(error=type(error).__name__):
                self.runner.run.side_effect = error
                with self.assertRaises(asyncio.CancelledError):
                    await self.adapter.run(self.task)

    async def test_wrapped_tool_causes_keep_their_category(self):
        for cause, category in (
            (ToolExecutionError("tool failed"), ErrorType.TOOL_ERROR),
            (PermissionError("denied"), ErrorType.PERMISSION_DENIED),
        ):
            with self.subTest(category=category):
                tool_error = ToolExecutionError("tool wrapper")
                tool_error.__cause__ = cause
                wrapper = InputFailure("SDK wrapper")
                wrapper.__cause__ = tool_error
                self.runner.run.side_effect = wrapper
                self.assert_failure(await self.adapter.run(self.task), category)

    async def test_cyclic_explicit_causes_terminate(self):
        error = RuntimeError("cyclic cause")
        error.__cause__ = error
        self.runner.run.side_effect = error
        self.assert_failure(await self.adapter.run(self.task), ErrorType.RUNTIME_ERROR)

    def test_configuration_rejects_invalid_limits_and_error_types(self):
        for limit in (0, -1, True, 1.5, "3"):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                OpenAIAgentsAdapter(agent=self.agent, runner=self.runner, max_turns=limit)
        with self.assertRaises(TypeError):
            OpenAIAgentsAdapter(
                agent=self.agent, runner=self.runner, tool_errors=(BaseException,),
            )

    def test_missing_sdk_has_explicit_install_message(self):
        with patch.dict(sys.modules, {"agents": None}):
            with self.assertRaisesRegex(ImportError, "requirements-openai-agents.txt"):
                OpenAIAgentsAdapter.from_sdk(agent=self.agent)

    def test_core_and_adapter_import_without_provider_sdks(self):
        code = """
import builtins
original_import = builtins.__import__
def reject_provider(name, *args, **kwargs):
    if name.split('.')[0] in ('agents', 'openai'):
        raise AssertionError('provider imported: ' + name)
    return original_import(name, *args, **kwargs)
builtins.__import__ = reject_provider
import runtime.contracts
import runtime.adapters.openai_agents
"""
        result = subprocess.run(
            [sys.executable, "-c", code], capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
