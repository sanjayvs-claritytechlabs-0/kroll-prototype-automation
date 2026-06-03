"""Placeholder adapters for future real Kroll UI automation."""

from __future__ import annotations

from typing import Any


class KrollUIAutomationAdapter:
    """Future: pywinauto-based adapter targeting real Kroll windows."""

    def connect(self) -> bool:
        raise NotImplementedError("Real Kroll UI automation is not implemented yet.")

    def set_field_value(self, object_name: str, value: str) -> None:
        raise NotImplementedError

    def get_field_value(self, object_name: str) -> str:
        raise NotImplementedError


class SimulatorAdapter:
    """
    In-process stub for workflow engine wiring.

    Real desktop automation lives in apps.automation_controller.SimulatorUIAAdapter.
    """

    def __init__(self) -> None:
        self._connected = False

    def connect(self) -> bool:
        self._connected = True
        return True

    def set_field_value(self, object_name: str, value: str) -> None:
        if not self._connected:
            raise RuntimeError("SimulatorAdapter not connected")
        raise NotImplementedError(
            "Use apps.automation_controller.SimulatorUIAAdapter for pywinauto automation"
        )

    def get_field_value(self, object_name: str) -> str:
        if not self._connected:
            raise RuntimeError("SimulatorAdapter not connected")
        raise NotImplementedError(
            "Use apps.automation_controller.SimulatorUIAAdapter for pywinauto automation"
        )
