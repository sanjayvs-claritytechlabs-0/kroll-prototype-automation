"""Automation Controller — pywinauto UIA against the pharmacy simulator.

Start the simulator first, then run:

    python apps/automation_controller/main.py --workflow fill_save
    python apps/automation_controller/main.py --enumerate
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
    from apps.automation_controller.workflows.fill_general_and_save import (
        WORKFLOW_NAME,
        run as run_fill_save,
    )
except ImportError as _import_err:
    SimulatorUIAAdapter = None  # type: ignore[misc, assignment]
    ControlNotFoundError = RuntimeError  # type: ignore[misc, assignment]
    WORKFLOW_NAME = "fill_general_and_save"
    _PYWINAUTO_IMPORT_ERROR = _import_err
else:
    _PYWINAUTO_IMPORT_ERROR = None


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="UI Automation controller for the Kroll pharmacy simulator",
    )
    parser.add_argument(
        "--workflow",
        choices=("fill_save", "inbox_to_save"),
        help="Run an end-to-end workflow script",
    )
    parser.add_argument(
        "--mode",
        choices=("ui", "hybrid"),
        default="ui",
        help="For inbox_to_save: ui = full desktop path; hybrid = headless extract + search UI",
    )
    parser.add_argument(
        "--enumerate",
        action="store_true",
        help="Connect, open a new patient record, and print the UIA control tree",
    )
    parser.add_argument(
        "--connect-only",
        action="store_true",
        help="Verify the simulator main window is reachable",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=20.0,
        help="Seconds to wait for windows and controls (default: 20)",
    )
    parser.add_argument(
        "--patient-config",
        type=Path,
        default=None,
        help="JSON file with fields keyed by objectName (default: config/automation_test_patient.json)",
    )
    return parser.parse_args()


def _print_last_automation_error() -> None:
    log_path = PROJECT_ROOT / "logs" / "automation.jsonl"
    if not log_path.is_file():
        return
    try:
        lines = log_path.read_text(encoding="utf-8").strip().splitlines()
        if not lines:
            return
        entry = json.loads(lines[-1])
        if entry.get("result") == "fail" or entry.get("event") == "workflow_failed":
            err = entry.get("error") or entry.get("field") or entry.get("event")
            actual = entry.get("actual")
            expected = entry.get("expected")
            print(f"Last log: {err}", file=sys.stderr)
            if expected is not None:
                print(f"  expected: {expected!r}", file=sys.stderr)
            if actual is not None:
                print(f"  actual:   {actual!r}", file=sys.stderr)
    except (json.JSONDecodeError, OSError):
        pass


def _print_controls(records: list[dict[str, str]]) -> None:
    seen: set[tuple[str, str]] = set()
    for row in sorted(records, key=lambda r: (r["automation_id"], r["name"])):
        key = (row["automation_id"], row["name"])
        if key in seen:
            continue
        seen.add(key)
        auto_id = row["automation_id"] or "(none)"
        print(f"{auto_id:32}  {row['name']:32}  {row['control_type']}")


def main() -> int:
    args = _parse_args()
    if not any((args.workflow, args.enumerate, args.connect_only)):
        print(
            "Specify --workflow fill_save|inbox_to_save, --enumerate, or --connect-only"
        )
        return 2

    if _PYWINAUTO_IMPORT_ERROR is not None:
        print(
            "pywinauto is required. Install dependencies:\n"
            "  pip install -r requirements.txt\n"
            f"Details: {_PYWINAUTO_IMPORT_ERROR}",
            file=sys.stderr,
        )
        return 1

    adapter = SimulatorUIAAdapter(timeout=args.timeout)

    try:
        if args.connect_only:
            adapter.connect()
            print(f"Connected to: {adapter.client.main_window.window_text()}")
            return 0

        if args.enumerate:
            adapter.connect()
            adapter.open_new_patient_record()
            records = adapter.enumerate_patient_record_controls()
            print(f"Found {len(records)} accessible controls on Patient Record:\n")
            _print_controls(records)
            return 0

        if args.workflow == "fill_save":
            fields = SimulatorUIAAdapter.load_test_patient(args.patient_config)
            print(f"Running workflow '{WORKFLOW_NAME}' with {len(fields)} fields...")
            ok = run_fill_save(adapter, fields)
            if ok:
                print("Workflow completed successfully.")
                return 0
            print(
                "Workflow failed — see logs/automation.jsonl and screenshots/",
                file=sys.stderr,
            )
            _print_last_automation_error()
            return 1

        if args.workflow == "inbox_to_save":
            from apps.workflow_engine.workflows.inbox_to_save import (
                load_config,
                run as run_inbox_to_save,
            )

            config = load_config()
            print(f"Running workflow 'inbox_to_save' (mode={args.mode})...")
            ok, ctx = run_inbox_to_save(adapter, mode=args.mode, config=config)
            if ok:
                print(
                    f"Workflow completed — run_id={ctx.run_id}  "
                    f"patient_id={ctx.patient_id or 'n/a'}"
                )
                return 0
            print(
                "Workflow failed — see database/workflow_audit.db and "
                "logs/workflow_audit.jsonl",
                file=sys.stderr,
            )
            return 1
    except ControlNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
