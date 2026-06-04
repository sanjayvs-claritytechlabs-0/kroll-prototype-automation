"""SQLite persistence for workflow runs, steps, and review queue."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from apps.workflow_engine.audit_schema import AUDIT_SCHEMA_STATEMENTS
from apps.workflow_engine.models import StepResult, StepStatus
from apps.workflow_engine.paths import AUDIT_DB_PATH


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AuditStore:
    """Workflow audit trail (PRD: SQLite + JSON mirror)."""

    def __init__(self, db_path: Path | None = None) -> None:
        self._path = db_path or AUDIT_DB_PATH
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            for statement in AUDIT_SCHEMA_STATEMENTS:
                conn.execute(statement)
            conn.commit()

    def start_run(self, run_id: str, workflow_name: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO workflow_runs (run_id, workflow_name, status, started_at)
                VALUES (?, ?, 'running', ?)
                """,
                (run_id, workflow_name, _utc_now()),
            )
            conn.commit()

    def complete_run(self, run_id: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE workflow_runs
                SET status = 'completed', finished_at = ?
                WHERE run_id = ?
                """,
                (_utc_now(), run_id),
            )
            conn.commit()

    def fail_run(self, run_id: str, error: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE workflow_runs
                SET status = 'failed', finished_at = ?, error = ?
                WHERE run_id = ?
                """,
                (_utc_now(), error, run_id),
            )
            conn.commit()

    def record_step(self, run_id: str, result: StepResult) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO workflow_steps (
                    run_id, step_name, status, expected, actual,
                    control_name, window_name, screenshot_path, error, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    result.name,
                    result.status.value,
                    result.expected,
                    result.actual,
                    result.control_name,
                    result.window_name,
                    result.screenshot_path,
                    result.error,
                    _utc_now(),
                ),
            )
            conn.commit()

    def enqueue_review(
        self,
        run_id: str,
        step_name: str,
        *,
        field: str | None = None,
        expected: str | None = None,
        actual: str | None = None,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO review_queue (
                    run_id, step_name, field, expected, actual, status, created_at
                ) VALUES (?, ?, ?, ?, ?, 'pending', ?)
                """,
                (run_id, step_name, field, expected, actual, _utc_now()),
            )
            conn.commit()

    def pending_reviews(self, limit: int = 20) -> list[dict[str, str]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT run_id, step_name, field, expected, actual, status, created_at
                FROM review_queue
                WHERE status = 'pending'
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]
