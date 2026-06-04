"""High-level adapter: pywinauto UIA against the pharmacy simulator."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from apps.automation_controller.logging_util import log_automation_event
from apps.automation_controller.paths import SCREENSHOT_DIR, TEST_PATIENT_CONFIG
from apps.automation_controller.uia_client import (
    DOCUMENT_VIEWER_AUTO_ID,
    EXTRACTION_DIALOG_AUTO_ID,
    INBOX_AUTO_ID,
    ControlNotFoundError,
    UIAClient,
)

WORKFLOW_NAME = "simulator_uia"


class SimulatorUIAAdapter:
    """Automate this prototype via UI Automation (objectName / accessibleName)."""

    def __init__(self, timeout: float = 15.0) -> None:
        self._client = UIAClient(timeout=timeout)
        self._connected = False
        self._patient_window = None
        self._inbox_window = None
        self._viewer_window = None
        self._search_window = None

    @property
    def client(self) -> UIAClient:
        return self._client

    def connect(self) -> bool:
        self._client.connect()
        self._connected = True
        log_automation_event(WORKFLOW_NAME, "connected", window_name="win_main")
        return True

    def open_new_patient_record(self) -> None:
        if not self._connected:
            raise RuntimeError("Adapter not connected")
        main = self._client.main_window
        existing_handles = {
            self._client._window_handle(w)
            for w in self._client.list_patient_record_windows()
        }
        self._client.screenshot(SCREENSHOT_DIR / "before_new_patient.png")

        last_method = ""
        end = time.monotonic() + 25
        last_error: ControlNotFoundError | None = None
        while time.monotonic() < end:
            if not last_method:
                last_method = self._client.try_open_new_patient_record(main)
                log_automation_event(
                    WORKFLOW_NAME,
                    "open_patient_attempt",
                    result=last_method,
                )
            time.sleep(0.6)
            try:
                self._patient_window = self._client.wait_for_patient_record(
                    timeout=4,
                    exclude_handles=existing_handles if existing_handles else None,
                )
                log_automation_event(
                    WORKFLOW_NAME,
                    "patient_record_opened",
                    window_name=self._patient_window.window_text(),
                    result=last_method,
                )
                return
            except ControlNotFoundError as exc:
                last_error = exc
                last_method = ""
                self._client.bring_to_foreground(main)

        raise last_error or ControlNotFoundError(
            "Patient Record window did not open after multiple attempts"
        )

    def patient_record(self):
        if self._patient_window is None:
            windows = self._client.list_patient_record_windows()
            if not windows:
                raise ControlNotFoundError("No Patient Record window is open")
            self._patient_window = windows[-1]
        return self._patient_window

    def set_field_value(self, object_name: str, value: str) -> None:
        self._client.set_value(self.patient_record(), object_name, value)

    def get_field_value(self, object_name: str) -> str:
        return self._client.get_value(self.patient_record(), object_name)

    def click(self, object_name: str) -> None:
        self._client.click(self.patient_record(), object_name)

    def verify_field(self, object_name: str, expected: str) -> bool:
        actual = self.get_field_value(object_name)
        ok = actual.strip() == expected.strip()
        log_automation_event(
            WORKFLOW_NAME,
            "field_verify",
            field=object_name,
            expected=expected,
            actual=actual,
            result="pass" if ok else "fail",
            control_name=object_name,
        )
        return ok

    def open_inbox(self) -> None:
        if not self._connected:
            raise RuntimeError("Adapter not connected")
        main = self._client.main_window
        self._client.screenshot(SCREENSHOT_DIR / "before_inbox.png")
        method = self._client.try_open_inbox(main)
        log_automation_event(WORKFLOW_NAME, "open_inbox_attempt", result=method)
        self._inbox_window = self._client.wait_for_inbox(timeout=20)
        log_automation_event(WORKFLOW_NAME, "inbox_opened", result=method)

    def inbox(self):
        if self._inbox_window is None:
            self._inbox_window = self._client.wait_for_inbox(timeout=12)
        return self._inbox_window

    def select_inbox_row(self, row_index: int = 0) -> None:
        self._client.select_table_row(self.inbox(), "grid_inbox", row_index)

    def open_inbox_selection(self) -> None:
        inbox = self.inbox()
        method = self._client.open_document_from_inbox(inbox)
        log_automation_event(WORKFLOW_NAME, "open_document_attempt", result=method)
        end = time.monotonic() + 22
        last_error: ControlNotFoundError | None = None
        while time.monotonic() < end:
            try:
                self._viewer_window = self._client.wait_for_document_viewer(timeout=4)
                log_automation_event(WORKFLOW_NAME, "document_viewer_opened", result=method)
                return
            except ControlNotFoundError as exc:
                last_error = exc
                self._client.bring_to_foreground(inbox)
                time.sleep(0.4)
        raise last_error or ControlNotFoundError("Document Viewer did not open")

    def process_open_document(self) -> None:
        scope = self._viewer_window or self._client.wait_for_document_viewer(
            timeout=12,
        )
        self._client.click(scope, "btn_process_document")
        self._viewer_window = None

    def accept_extraction_dialog(self) -> None:
        dialog = self._client.wait_for_window_marker(
            EXTRACTION_DIALOG_AUTO_ID,
            timeout=15,
        )
        self._client.click(dialog, "btn_extraction_search")

    def get_extraction_label_value(self, field_key: str) -> str:
        dialog = self._client.wait_for_window_marker(EXTRACTION_DIALOG_AUTO_ID, timeout=8)
        return self._client.get_value(dialog, f"lbl_extracted_{field_key}")

    def open_patient_search(self) -> None:
        if not self._connected:
            raise RuntimeError("Adapter not connected")
        main = self._client.main_window
        self._client.screenshot(SCREENSHOT_DIR / "before_patient_search.png")
        method = self._client.try_open_patient_search(main)
        log_automation_event(
            WORKFLOW_NAME,
            "open_patient_search_attempt",
            result=method,
        )
        self._search_window = self._client.wait_for_patient_search(timeout=20)
        log_automation_event(
            WORKFLOW_NAME,
            "patient_search_opened",
            window_name=self._search_window.window_text(),
            result=method,
        )

    def patient_search(self):
        if self._search_window is None:
            self._search_window = self._client.wait_for_patient_search(timeout=15)
        return self._search_window

    def _ensure_patient_search_window(self) -> None:
        """Re-resolve search window if cache points at wrong process (e.g. IDE)."""
        if self._search_window is not None:
            try:
                if self._client._scan_descendant_by_object_name(
                    self._search_window, "txt_search_first_name"
                ):
                    return
            except Exception:
                pass
            self._search_window = None
        self._search_window = self._client.wait_for_patient_search(timeout=12)

    def fill_patient_search(self, criteria: dict[str, str]) -> None:
        self._ensure_patient_search_window()
        scope = self.patient_search()
        if criteria.get("first_name"):
            self._client.set_value(scope, "txt_search_first_name", criteria["first_name"])
        if criteria.get("last_name"):
            self._client.set_value(scope, "txt_search_last_name", criteria["last_name"])
        if criteria.get("dob"):
            self._client.set_value(scope, "txt_search_dob", criteria["dob"])

    def run_patient_search(self) -> None:
        self._client.click(self.patient_search(), "btn_search_patient")
        time.sleep(0.4)

    def create_new_patient_from_search(self) -> None:
        self._client.click(self.patient_search(), "btn_create_new_patient")
        self._patient_window = self._client.wait_for_patient_record(timeout=20)
        self._search_window = None
        log_automation_event(WORKFLOW_NAME, "patient_record_from_search")

    def fill_and_verify_fields(
        self,
        fields: dict[str, str],
        field_order: tuple[str, ...] | None = None,
    ) -> tuple[bool, str | None, str | None]:
        """Returns (ok, failed_object_name, error_message)."""
        order = field_order or tuple(fields.keys())
        for object_name in order:
            if object_name not in fields:
                continue
            expected = str(fields[object_name])
            self.set_field_value(object_name, expected)
            if not self.verify_field(object_name, expected):
                return False, object_name, "Field value mismatch after set"
        return True, None, None

    def read_patient_id_field(self) -> str:
        return self.get_field_value("txt_patient_id").strip()

    def save_patient(self) -> None:
        self._client.screenshot(SCREENSHOT_DIR / "before_save.png", self.patient_record())
        self.click("btn_save")
        self._client.dismiss_message_box("Save")
        self._client.dismiss_message_box("Validation")
        self._client.screenshot(SCREENSHOT_DIR / "after_save.png", self.patient_record())
        log_automation_event(WORKFLOW_NAME, "save_clicked", result="ok")

    def enumerate_patient_record_controls(self) -> list[dict[str, str]]:
        return [
            {
                "automation_id": c.automation_id,
                "name": c.name,
                "control_type": c.control_type,
                "class_name": c.class_name,
            }
            for c in self._client.enumerate_controls(self.patient_record())
        ]

    @staticmethod
    def load_test_patient(path: Path | None = None) -> dict[str, str]:
        config_path = path or TEST_PATIENT_CONFIG
        with config_path.open(encoding="utf-8") as handle:
            data = json.load(handle)
        return dict(data.get("fields", {}))
