"""Provider-neutral contracts for small agent runtime experiments."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class RunStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"


class ErrorType(str, Enum):
    INVALID_INPUT = "invalid_input"
    TOOL_ERROR = "tool_error"
    PERMISSION_DENIED = "permission_denied"
    RUNTIME_ERROR = "runtime_error"


@dataclass(frozen=True)
class Task:
    task_id: str
    input: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.task_id.strip():
            raise ValueError("task_id is required")
        if not self.input.strip():
            raise ValueError("input is required")


@dataclass(frozen=True)
class RunResult:
    task_id: str
    status: RunStatus
    output: str | None = None
    error_type: ErrorType | None = None
    error_message: str | None = None

    def __post_init__(self) -> None:
        if self.status is RunStatus.SUCCESS:
            if self.output is None:
                raise ValueError("successful result requires output")
            if self.error_type is not None or self.error_message is not None:
                raise ValueError("successful result cannot contain an error")
        else:
            if self.error_type is None or not self.error_message:
                raise ValueError("failed result requires typed error details")
            if self.output is not None:
                raise ValueError("failed result cannot contain output")

    @classmethod
    def success(cls, task_id: str, output: str) -> "RunResult":
        return cls(task_id=task_id, status=RunStatus.SUCCESS, output=output)

    @classmethod
    def failure(
        cls, task_id: str, error_type: ErrorType, error_message: str
    ) -> "RunResult":
        return cls(
            task_id=task_id,
            status=RunStatus.FAILED,
            error_type=error_type,
            error_message=error_message,
        )
