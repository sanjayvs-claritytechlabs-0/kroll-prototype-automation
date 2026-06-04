"""Inbox → OCR/extract → Patient Search → Patient Record → Save."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from apps.automation_controller.simulator_adapter import SimulatorUIAAdapter
from apps.automation_controller.uia_client import ControlNotFoundError
from apps.pharmacy_simulator.database.inbox_repository import InboxRepository
from apps.pharmacy_simulator.extraction.document_processor import DocumentProcessor
from apps.workflow_engine.engine import WorkflowEngine
from apps.workflow_engine.field_mapping import record_fields_from_extraction
from apps.workflow_engine.models import StepResult, WorkflowContext
from apps.workflow_engine.paths import INBOX_WORKFLOW_CONFIG, SCREENSHOT_DIR
from apps.workflow_engine.inbox_resolve import inbox_grid_row_index, resolve_inbox_document
from apps.workflow_engine.verification import FieldVerifier

WORKFLOW_NAME = "inbox_to_save"

EXTRACTION_DIALOG_KEYS = (
    "first_name",
    "last_name",
    "dob",
    "phone",
    "email",
    "health_card",
)


def load_config(path: Path | None = None) -> dict[str, Any]:
    config_path = path or INBOX_WORKFLOW_CONFIG
    with config_path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _read_extraction_from_dialog(adapter: SimulatorUIAAdapter) -> dict[str, str]:
    fields: dict[str, str] = {}
    for key in EXTRACTION_DIALOG_KEYS:
        try:
            raw = adapter.get_extraction_label_value(key).strip()
        except ControlNotFoundError:
            continue
        if raw and "(not found)" not in raw.lower():
            fields[key] = raw
    return fields


def build_steps(
    adapter: SimulatorUIAAdapter,
    verifier: FieldVerifier,
    *,
    mode: str = "ui",
) -> list:
    """Build step functions for the workflow engine."""

    def step_connect(_ctx: WorkflowContext) -> StepResult:
        adapter.connect()
        adapter.client.screenshot(SCREENSHOT_DIR / "workflow_start.png")
        return WorkflowEngine.ok("connect", window_name="win_main")

    def step_extract_headless(ctx: WorkflowContext) -> StepResult:
        if mode != "hybrid":
            return WorkflowEngine.ok("extract_headless", extra={"skipped": True})

        repo = InboxRepository()
        doc, err = resolve_inbox_document(repo, ctx.config)
        if doc is None:
            return WorkflowEngine.fail("extract_headless", error=err or "Document not found")

        doc_id = int(doc["id"])
        ctx.document_id = doc_id
        processor = DocumentProcessor(repo)
        try:
            result = processor.process(doc_id)
        except (OSError, ValueError) as exc:
            return WorkflowEngine.fail("extract_headless", error=str(exc))

        ctx.extraction_fields = dict(result.fields)
        if not ctx.extraction_fields:
            return WorkflowEngine.fail(
                "extract_headless",
                error=(
                    f"No fields extracted from {doc.get('file_name')!r}. "
                    "Use a .txt sample fax/email or set document_file_name in config."
                ),
                extra={"document_id": doc_id, "file_name": doc.get("file_name")},
            )

        expect = ctx.config.get("expect_extraction", {})
        if expect:
            check = verifier.verify_extraction_fields(
                "extract_headless",
                expect,
                ctx.extraction_fields,
            )
            if not check.passed:
                return check
        return WorkflowEngine.ok(
            "extract_headless",
            extra={
                "document_id": doc_id,
                "file_name": doc.get("file_name"),
                "fields": ctx.extraction_fields,
            },
        )

    def step_open_inbox(_ctx: WorkflowContext) -> StepResult:
        if mode == "hybrid":
            return WorkflowEngine.ok("open_inbox", extra={"skipped": True})
        try:
            adapter.open_inbox()
            adapter.client.screenshot(SCREENSHOT_DIR / "inbox_open.png")
            return WorkflowEngine.ok("open_inbox", window_name="win_inbox")
        except ControlNotFoundError as exc:
            return WorkflowEngine.fail("open_inbox", error=str(exc))

    def step_select_document(ctx: WorkflowContext) -> StepResult:
        if mode == "hybrid":
            return WorkflowEngine.ok("select_document", extra={"skipped": True})
        try:
            repo = InboxRepository()
            doc, err = resolve_inbox_document(repo, ctx.config)
            if doc is None:
                return WorkflowEngine.fail("select_document", error=err or "Document not found")
            ctx.document_id = int(doc["id"])
            row = inbox_grid_row_index(repo, ctx.document_id)
            if row is None:
                return WorkflowEngine.fail(
                    "select_document",
                    error=f"Document id {ctx.document_id} not in inbox grid",
                )
            adapter.select_inbox_row(row)
            return WorkflowEngine.ok(
                "select_document",
                extra={"row": row, "file_name": doc.get("file_name")},
            )
        except ControlNotFoundError as exc:
            return WorkflowEngine.fail("select_document", error=str(exc))

    def step_open_document(_ctx: WorkflowContext) -> StepResult:
        if mode == "hybrid":
            return WorkflowEngine.ok("open_document", extra={"skipped": True})
        try:
            adapter.open_inbox_selection()
            return WorkflowEngine.ok("open_document", window_name="win_document_viewer")
        except ControlNotFoundError as exc:
            return WorkflowEngine.fail("open_document", error=str(exc))

    def step_process_document(_ctx: WorkflowContext) -> StepResult:
        if mode == "hybrid":
            return WorkflowEngine.ok("process_document", extra={"skipped": True})
        try:
            adapter.process_open_document()
            return WorkflowEngine.ok("process_document")
        except ControlNotFoundError as exc:
            return WorkflowEngine.fail("process_document", error=str(exc))

    def step_verify_extraction_dialog(ctx: WorkflowContext) -> StepResult:
        if mode == "hybrid":
            return WorkflowEngine.ok("verify_extraction_dialog", extra={"skipped": True})
        try:
            ctx.extraction_fields = _read_extraction_from_dialog(adapter)
            expect = ctx.config.get("expect_extraction", {})
            if expect:
                check = verifier.verify_extraction_fields(
                    "verify_extraction_dialog",
                    expect,
                    ctx.extraction_fields,
                )
                if not check.passed:
                    return check
            if not ctx.extraction_fields:
                return WorkflowEngine.fail(
                    "verify_extraction_dialog",
                    error="No extracted fields visible on dialog",
                )
            return WorkflowEngine.ok(
                "verify_extraction_dialog",
                extra={"fields": ctx.extraction_fields},
            )
        except ControlNotFoundError as exc:
            return WorkflowEngine.fail("verify_extraction_dialog", error=str(exc))

    def step_accept_extraction(_ctx: WorkflowContext) -> StepResult:
        if mode == "hybrid":
            return WorkflowEngine.ok("accept_extraction", extra={"skipped": True})
        try:
            adapter.accept_extraction_dialog()
            return WorkflowEngine.ok("accept_extraction")
        except ControlNotFoundError as exc:
            return WorkflowEngine.fail("accept_extraction", error=str(exc))

    def step_open_search_hybrid(_ctx: WorkflowContext) -> StepResult:
        if mode != "hybrid":
            return WorkflowEngine.ok("open_search_hybrid", extra={"skipped": True})
        try:
            adapter.open_patient_search()
            return WorkflowEngine.ok("open_search_hybrid", window_name="win_patient_search")
        except ControlNotFoundError as exc:
            return WorkflowEngine.fail("open_search_hybrid", error=str(exc))

    def step_fill_search(ctx: WorkflowContext) -> StepResult:
        if not ctx.extraction_fields:
            return WorkflowEngine.fail(
                "fill_search",
                error="No extraction fields available for search",
            )
        criteria = {
            k: ctx.extraction_fields[k]
            for k in ("first_name", "last_name", "dob")
            if ctx.extraction_fields.get(k)
        }
        if not criteria:
            return WorkflowEngine.fail("fill_search", error="No search criteria from extraction")
        try:
            adapter.fill_patient_search(criteria)
            return WorkflowEngine.ok("fill_search", extra=criteria)
        except ControlNotFoundError as exc:
            return WorkflowEngine.fail("fill_search", error=str(exc))

    def step_run_search(_ctx: WorkflowContext) -> StepResult:
        try:
            adapter.run_patient_search()
            return WorkflowEngine.ok("run_search", window_name="win_patient_search")
        except ControlNotFoundError as exc:
            return WorkflowEngine.fail("run_search", error=str(exc))

    def step_create_patient(ctx: WorkflowContext) -> StepResult:
        try:
            adapter.create_new_patient_from_search()
            ctx.patient_id = adapter.read_patient_id_field()
            adapter.client.screenshot(SCREENSHOT_DIR / "patient_record_open.png")
            return WorkflowEngine.ok(
                "create_patient",
                actual=ctx.patient_id,
                window_name="win_patient_record",
            )
        except ControlNotFoundError as exc:
            return WorkflowEngine.fail("create_patient", error=str(exc))

    def step_fill_record(ctx: WorkflowContext) -> StepResult:
        defaults = ctx.config.get("record_defaults", {})
        ctx.record_fields = record_fields_from_extraction(
            ctx.extraction_fields,
            defaults=defaults,
        )
        order = tuple(ctx.config.get("record_field_order", ()))
        ok, failed_field, msg = adapter.fill_and_verify_fields(
            ctx.record_fields,
            field_order=order or None,
        )
        if not ok:
            failed = failed_field or "unknown"
            return WorkflowEngine.fail(
                "fill_record",
                error=msg or "fill failed",
                control_name=failed,
                expected=str(ctx.record_fields.get(failed, "")),
                actual=adapter.get_field_value(failed),
                window_name="win_patient_record",
            )
        return WorkflowEngine.ok("fill_record", extra={"field_count": len(ctx.record_fields)})

    def step_save(_ctx: WorkflowContext) -> StepResult:
        try:
            adapter.save_patient()
            adapter.client.screenshot(SCREENSHOT_DIR / "workflow_complete.png")
            return WorkflowEngine.ok("save", window_name="win_patient_record")
        except ControlNotFoundError as exc:
            return WorkflowEngine.fail("save", error=str(exc))

    return [
        step_connect,
        step_extract_headless,
        step_open_inbox,
        step_select_document,
        step_open_document,
        step_process_document,
        step_verify_extraction_dialog,
        step_accept_extraction,
        step_open_search_hybrid,
        step_fill_search,
        step_run_search,
        step_create_patient,
        step_fill_record,
        step_save,
    ]


def run(
    adapter: SimulatorUIAAdapter,
    *,
    mode: str = "ui",
    config: dict[str, Any] | None = None,
    run_id: str | None = None,
) -> tuple[bool, WorkflowContext]:
    cfg = config or load_config()
    engine = WorkflowEngine()
    verifier = FieldVerifier()

    def screenshot_on_fail(_ctx: WorkflowContext, result: StepResult) -> str | None:
        if not adapter._connected:
            return None
        name = f"error_{result.name}.png".replace(" ", "_")
        saved = adapter.client.screenshot(SCREENSHOT_DIR / name)
        return str(saved) if saved else None

    return engine.run(
        WORKFLOW_NAME,
        build_steps(adapter, verifier, mode=mode),
        config=cfg,
        run_id=run_id,
        on_step_fail_screenshot=screenshot_on_fail,
    )
