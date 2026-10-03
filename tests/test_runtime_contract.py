import unittest

from runtime.contracts import ErrorType, RunResult, RunStatus, Task


class RuntimeContractTests(unittest.TestCase):
    def test_valid_task_and_success_result(self):
        task = Task(task_id="demo-1", input="look up metric")
        task.validate()

        result = RunResult.success(task.task_id, "verified metric")
        self.assertEqual(result.status, RunStatus.SUCCESS)
        self.assertEqual(result.output, "verified metric")
        self.assertIsNone(result.error_type)

    def test_invalid_task_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "input is required"):
            Task(task_id="demo-2", input="   ").validate()

    def test_failure_is_typed_and_cannot_claim_output(self):
        result = RunResult.failure(
            "demo-3", ErrorType.INVALID_INPUT, "symbol is required"
        )
        self.assertEqual(result.status, RunStatus.FAILED)
        self.assertEqual(result.error_type, ErrorType.INVALID_INPUT)
        self.assertIsNone(result.output)

        with self.assertRaisesRegex(ValueError, "failed result cannot contain output"):
            RunResult(
                task_id="demo-4",
                status=RunStatus.FAILED,
                output="fabricated success",
                error_type=ErrorType.TOOL_ERROR,
                error_message="tool failed",
            )

    def test_blank_task_id_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "task_id is required"):
            Task(task_id="   ", input="valid input").validate()

    def test_success_requires_output_and_cannot_contain_errors(self):
        for fields in (
            {},
            {"output": "text", "error_type": ErrorType.RUNTIME_ERROR},
            {"output": "text", "error_message": "failure"},
        ):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                RunResult(task_id="demo", status=RunStatus.SUCCESS, **fields)

    def test_failure_requires_both_typed_error_and_nonempty_message(self):
        for fields in (
            {},
            {"error_type": ErrorType.TOOL_ERROR},
            {"error_message": "failure"},
            {"error_type": ErrorType.TOOL_ERROR, "error_message": ""},
        ):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                RunResult(task_id="demo", status=RunStatus.FAILED, **fields)


if __name__ == "__main__":
    unittest.main()
