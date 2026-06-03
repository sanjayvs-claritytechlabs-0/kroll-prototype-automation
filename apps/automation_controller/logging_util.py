"""Structured JSON-line logs for automation runs."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from apps.automation_controller.paths import AUTOMATION_LOG, LOG_DIR


def log_automation_event(
    workflow: str,
    event: str,
    *,
    field: str | None = None,
    expected: str | None = None,
    actual: str | None = None,
    result: str | None = None,
    window_name: str | None = None,
    control_name: str | None = None,
    error: str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    entry: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "workflow": workflow,
        "event": event,
    }
    for key, value in (
        ("field", field),
        ("expected", expected),
        ("actual", actual),
        ("result", result),
        ("window_name", window_name),
        ("control_name", control_name),
        ("error", error),
    ):
        if value is not None:
            entry[key] = value
    if extra:
        entry.update(extra)
    with AUTOMATION_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")
