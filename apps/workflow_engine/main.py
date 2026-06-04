"""Workflow engine CLI — orchestrated inbox → save with audit logging.

Start the pharmacy simulator first, then:

    python apps/workflow_engine/main.py --workflow inbox_to_save
    python apps/workflow_engine/main.py --workflow inbox_to_save --mode hybrid
    python apps/workflow_engine/main.py --list-reviews
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from apps.automation_controller.simulator_adapter import SimulatorUIAAdapter
    from apps.automation_controller.uia_client import ControlNotFoundError
    from apps.workflow_engine.audit_store import AuditStore
    from apps.workflow_engine.paths import AUDIT_JSONL
    from apps.workflow_engine.workflows.inbox_to_save import (
        WORKFLOW_NAME,
        load_config,
        run as run_inbox_to_save,
    )
except ImportError as _import_err:
    SimulatorUIAAdapter = None  # type: ignore[misc, assignment]
    ControlNotFoundError = RuntimeError  # type: ignore[misc, assignment]
    _IMPORT_ERROR = _import_err
else:
    _IMPORT_ERROR = None


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Kroll pharmacy workflow engine (Module 11)",
    )
    parser.add_argument(
        "--workflow",
        choices=("inbox_to_save",),
        help="End-to-end workflow to run",
    )
    parser.add_argument(
        "--mode",
        choices=("ui", "hybrid"),
        default="ui",
        help="ui = full desktop path; hybrid = headless extract then F3 search UI",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Workflow JSON config (default: config/workflow_inbox_to_save.json)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=25.0,
        help="UIA wait timeout in seconds",
    )
    parser.add_argument(
        "--list-reviews",
        action="store_true",
        help="Print pending human review queue entries",
    )
    return parser.parse_args()


def _print_last_audit_error() -> None:
    if not AUDIT_JSONL.is_file():
        return
    try:
        lines = AUDIT_JSONL.read_text(encoding="utf-8").strip().splitlines()
        if not lines:
            return
        entry = json.loads(lines[-1])
        if entry.get("result") in ("fail", "failed") or entry.get("event") == "run_failed":
            print(f"Last audit: {entry.get('error') or entry.get('step')}", file=sys.stderr)
            if entry.get("expected") is not None:
                print(f"  expected: {entry['expected']!r}", file=sys.stderr)
            if entry.get("actual") is not None:
                print(f"  actual:   {entry['actual']!r}", file=sys.stderr)
    except (json.JSONDecodeError, OSError):
        pass


def main() -> int:
    args = _parse_args()

    if args.list_reviews:
        if _IMPORT_ERROR:
            print(f"Cannot load audit store: {_IMPORT_ERROR}", file=sys.stderr)
            return 1
        pending = AuditStore().pending_reviews()
        if not pending:
            print("No pending review items.")
            return 0
        for row in pending:
            print(
                f"{row['created_at']}  run={row['run_id']}  step={row['step_name']}  "
                f"field={row.get('field') or '-'}  expected={row.get('expected')!r}  "
                f"actual={row.get('actual')!r}"
            )
        return 0

    if not args.workflow:
        print("Specify --workflow inbox_to_save or --list-reviews")
        return 2

    if _IMPORT_ERROR is not None:
        print(
            "Missing dependencies. Install:\n"
            "  pip install -r requirements.txt\n"
            f"Details: {_IMPORT_ERROR}",
            file=sys.stderr,
        )
        return 1

    config = load_config(args.config)
    adapter = SimulatorUIAAdapter(timeout=args.timeout)

    try:
        if args.workflow == "inbox_to_save":
            print(f"Running '{WORKFLOW_NAME}' (mode={args.mode})...")
            ok, ctx = run_inbox_to_save(adapter, mode=args.mode, config=config)
            if ok:
                print(
                    f"Workflow completed — run_id={ctx.run_id}  "
                    f"patient_id={ctx.patient_id or 'n/a'}"
                )
                print(f"Audit: database/workflow_audit.db  logs/workflow_audit.jsonl")
                return 0
            print(
                f"Workflow failed — run_id={ctx.run_id}. "
                "See database/workflow_audit.db and logs/workflow_audit.jsonl",
                file=sys.stderr,
            )
            _print_last_audit_error()
            return 1
    except ControlNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
