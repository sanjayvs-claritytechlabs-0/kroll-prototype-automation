"""Field verification — expected vs actual, stop workflow on mismatch."""

from __future__ import annotations

from typing import Callable, Protocol

from apps.workflow_engine.models import StepResult, StepStatus


class FieldReader(Protocol):
    def get_field_value(self, object_name: str) -> str: ...


class FieldWriter(Protocol):
    def set_field_value(self, object_name: str, value: str) -> None: ...


class FieldAutomation(FieldReader, FieldWriter, Protocol):
    pass


class FieldVerifier:
    """PRD verification engine: read back after set and compare."""

    def verify_read(
        self,
        step_name: str,
        object_name: str,
        expected: str,
        reader: FieldReader,
        *,
        window_name: str | None = None,
    ) -> StepResult:
        actual = reader.get_field_value(object_name)
        ok = actual.strip() == expected.strip()
        return StepResult(
            name=step_name,
            status=StepStatus.PASS if ok else StepStatus.FAIL,
            expected=expected,
            actual=actual,
            control_name=object_name,
            window_name=window_name,
            error=None if ok else "Field value mismatch after read",
        )

    def set_and_verify(
        self,
        step_name: str,
        object_name: str,
        expected: str,
        automation: FieldAutomation,
        *,
        window_name: str | None = None,
    ) -> StepResult:
        automation.set_field_value(object_name, expected)
        return self.verify_read(
            step_name,
            object_name,
            expected,
            automation,
            window_name=window_name,
        )

    def verify_extraction_fields(
        self,
        step_name: str,
        expected: dict[str, str],
        actual_fields: dict[str, str],
    ) -> StepResult:
        for key, want in expected.items():
            got = (actual_fields.get(key) or "").strip()
            if got != want.strip():
                return StepResult(
                    name=step_name,
                    status=StepStatus.FAIL,
                    expected=want,
                    actual=got,
                    control_name=key,
                    error=f"Extraction mismatch for {key}",
                )
        return StepResult(name=step_name, status=StepStatus.PASS)

    def fill_and_verify_all(
        self,
        step_prefix: str,
        fields: dict[str, str],
        automation: FieldAutomation,
        *,
        window_name: str | None = None,
        field_order: tuple[str, ...] | None = None,
    ) -> StepResult:
        order = field_order or tuple(fields.keys())
        for object_name in order:
            if object_name not in fields:
                continue
            expected = str(fields[object_name])
            result = self.set_and_verify(
                f"{step_prefix}_{object_name}",
                object_name,
                expected,
                automation,
                window_name=window_name,
            )
            if not result.passed:
                return result
        return StepResult(name=step_prefix, status=StepStatus.PASS)
