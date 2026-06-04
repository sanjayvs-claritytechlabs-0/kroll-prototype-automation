"""Sequential workflow runner with audit and review queue."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

from apps.workflow_engine.audit_jsonl import log_step_result, log_workflow_event
from apps.workflow_engine.audit_store import AuditStore
from apps.workflow_engine.models import StepResult, StepStatus, WorkflowContext
from apps.workflow_engine.paths import SCREENSHOT_DIR


StepFn = Callable[[WorkflowContext], StepResult]


class WorkflowEngine:
    """Run ordered steps; stop on first failure; audit every step."""

    def __init__(
        self,
        audit: AuditStore | None = None,
        screenshot_dir: Path | None = None,
    ) -> None:
        self._audit = audit or AuditStore()
        self._screenshot_dir = screenshot_dir or SCREENSHOT_DIR

    def new_run_id(self) -> str:
        return f"WF-{uuid.uuid4().hex[:10].upper()}"

    def run(
        self,
        workflow_name: str,
        steps: list[StepFn],
        *,
        config: dict[str, Any] | None = None,
        run_id: str | None = None,
        on_step_fail_screenshot: Callable[[WorkflowContext, StepResult], str | None]
        | None = None,
    ) -> tuple[bool, WorkflowContext]:
        rid = run_id or self.new_run_id()
        ctx = WorkflowContext(
            run_id=rid,
            workflow_name=workflow_name,
            config=dict(config or {}),
        )
        self._audit.start_run(rid, workflow_name)
        log_workflow_event(rid, workflow_name, "run_started")

        for step_fn in steps:
            result = step_fn(ctx)
            screenshot = result.screenshot_path
            if not result.passed and on_step_fail_screenshot and not screenshot:
                screenshot = on_step_fail_screenshot(ctx, result)
                if screenshot:
                    result = StepResult(
                        name=result.name,
                        status=result.status,
                        expected=result.expected,
                        actual=result.actual,
                        control_name=result.control_name,
                        window_name=result.window_name,
                        screenshot_path=screenshot,
                        error=result.error,
                        extra=result.extra,
                    )

            self._audit.record_step(rid, result)
            log_step_result(rid, workflow_name, result)

            if not result.passed:
                self._audit.fail_run(rid, result.error or f"Step failed: {result.name}")
                self._audit.enqueue_review(
                    rid,
                    result.name,
                    field=result.control_name,
                    expected=result.expected,
                    actual=result.actual,
                )
                log_workflow_event(
                    rid,
                    workflow_name,
                    "run_failed",
                    step=result.name,
                    error=result.error,
                    result="fail",
                )
                return False, ctx

        self._audit.complete_run(rid)
        log_workflow_event(rid, workflow_name, "run_completed", result="pass")
        return True, ctx

    @staticmethod
    def ok(name: str, **kwargs: Any) -> StepResult:
        return StepResult(name=name, status=StepStatus.PASS, **kwargs)

    @staticmethod
    def fail(name: str, error: str, **kwargs: Any) -> StepResult:
        return StepResult(
            name=name,
            status=StepStatus.FAIL,
            error=error,
            **kwargs,
        )
