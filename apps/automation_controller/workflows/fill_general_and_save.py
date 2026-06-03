"""Fill General tab fields on a new patient record and save."""

from __future__ import annotations

from apps.automation_controller.logging_util import log_automation_event
from apps.automation_controller.paths import SCREENSHOT_DIR
from apps.automation_controller.simulator_adapter import SimulatorUIAAdapter
from apps.automation_controller.uia_client import ControlNotFoundError

WORKFLOW_NAME = "fill_general_and_save"

# Fields to fill and verify (order matters for logging only).
FIELD_ORDER = (
    "txt_first_name",
    "txt_last_name",
    "txt_middle_name",
    "txt_dob",
    "cmb_gender",
    "txt_phone",
    "txt_email",
    "txt_address_line1",
    "txt_address_line2",
    "txt_city",
    "cmb_province",
    "txt_postal_code",
    "txt_health_card",
    "cmb_delivery_type",
    "cmb_delivery_route",
    "cmb_price_group",
    "txt_comments",
)


def run(adapter: SimulatorUIAAdapter, fields: dict[str, str]) -> bool:
    """
    Open new patient, enter values by objectName, verify read-back, save.
    Returns True on success.
    """
    try:
        adapter.connect()
        adapter.open_new_patient_record()
        adapter.client.screenshot(SCREENSHOT_DIR / "patient_record_open.png")

        for object_name in FIELD_ORDER:
            if object_name not in fields:
                continue
            expected = str(fields[object_name])
            adapter.set_field_value(object_name, expected)
            if not adapter.verify_field(object_name, expected):
                adapter.client.screenshot(SCREENSHOT_DIR / "error_field_mismatch.png")
                log_automation_event(
                    WORKFLOW_NAME,
                    "workflow_failed",
                    field=object_name,
                    expected=expected,
                    actual=adapter.get_field_value(object_name),
                    result="fail",
                    error="Field value mismatch after set",
                )
                return False

        adapter.save_patient()
        log_automation_event(WORKFLOW_NAME, "workflow_complete", result="pass")
        return True

    except (ControlNotFoundError, AttributeError) as exc:
        if adapter._connected:
            adapter.client.screenshot(SCREENSHOT_DIR / "error_control_not_found.png")
        log_automation_event(
            WORKFLOW_NAME,
            "workflow_failed",
            result="fail",
            error=str(exc),
        )
        return False
