"""High-level adapter: pywinauto UIA against the pharmacy simulator."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from apps.automation_controller.logging_util import log_automation_event
from apps.automation_controller.paths import SCREENSHOT_DIR, TEST_PATIENT_CONFIG
from apps.automation_controller.uia_client import ControlNotFoundError, UIAClient

WORKFLOW_NAME = "simulator_uia"


class SimulatorUIAAdapter:
    """Automate this prototype via UI Automation (objectName / accessibleName)."""

    def __init__(self, timeout: float = 15.0) -> None:
        self._client = UIAClient(timeout=timeout)
        self._connected = False
        self._patient_window = None

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
