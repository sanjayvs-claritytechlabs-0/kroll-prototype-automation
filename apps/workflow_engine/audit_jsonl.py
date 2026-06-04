"""Append-only JSON audit log (mirrors SQLite step events)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from apps.workflow_engine.models import StepResult
from apps.workflow_engine.paths import AUDIT_JSONL, LOG_DIR


def log_workflow_event(
    run_id: str,
    workflow: str,
    event: str,
    *,
    step: str | None = None,
    field: str | None = None,
    expected: str | None = None,
    actual: str | None = None,
    result: str | None = None,
    window_name: str | None = None,
    control_name: str | None = None,
    error: str | None = None,
    screenshot_path: str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    entry: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "workflow": workflow,
        "event": event,
    }
    for key, value in (
        ("step", step),
        ("field", field),
        ("expected", expected),
        ("actual", actual),
        ("result", result),
        ("window_name", window_name),
        ("control_name", control_name),
        ("error", error),
        ("screenshot_path", screenshot_path),
    ):
        if value is not None:
            entry[key] = value
    if extra:
        entry.update(extra)
    with AUDIT_JSONL.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")


def log_step_result(run_id: str, workflow: str, result: StepResult) -> None:
    log_workflow_event(
        run_id,
        workflow,
        "step",
        step=result.name,
        field=result.control_name,
        expected=result.expected,
        actual=result.actual,
        result=result.status.value,
        window_name=result.window_name,
        control_name=result.control_name,
        error=result.error,
        screenshot_path=result.screenshot_path,
        extra=result.extra or None,
    )
