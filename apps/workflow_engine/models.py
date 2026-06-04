"""Workflow run models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class StepStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"


@dataclass
class StepResult:
    name: str
    status: StepStatus
    expected: str | None = None
    actual: str | None = None
    control_name: str | None = None
    window_name: str | None = None
    screenshot_path: str | None = None
    error: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.status == StepStatus.PASS


@dataclass
class WorkflowContext:
    """Mutable state passed through workflow steps."""

    run_id: str
    workflow_name: str
    config: dict[str, Any] = field(default_factory=dict)
    extraction_fields: dict[str, str] = field(default_factory=dict)
    record_fields: dict[str, str] = field(default_factory=dict)
    document_id: int | None = None
    patient_id: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)
