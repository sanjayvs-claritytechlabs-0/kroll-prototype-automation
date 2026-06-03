"""UI Automation client (pywinauto UIA) for the pharmacy simulator."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pywinauto import Desktop
from pywinauto.base_wrapper import BaseWrapper
from pywinauto.findwindows import (
    ElementAmbiguousError,
    ElementNotFoundError,
    find_elements,
)
from pywinauto.timings import TimeoutError as PywinautoTimeoutError

MAIN_TITLE = "Kroll by Telus Health"
MAIN_TITLE_RE = r"^Kroll by Telus Health$"
MAIN_AUTO_ID = "win_main"
PATIENT_RECORD_TITLE_RE = r"Patient Record.*"
PATIENT_RECORD_AUTO_ID = "win_patient_record"


@dataclass(frozen=True)
class ControlInfo:
    automation_id: str
    name: str
    control_type: str
    class_name: str


class ControlNotFoundError(RuntimeError):
    """Raised when a control cannot be located by automation metadata."""


class UIAClient:
    """Connect to simulator windows and read/write controls by objectName / accessibleName."""

    def __init__(self, backend: str = "uia", timeout: float = 10.0) -> None:
        self._backend = backend
        self._timeout = timeout
        self._desktop = Desktop(backend=backend)
        self._main_window: BaseWrapper | None = None

    @property
    def main_window(self) -> BaseWrapper:
        if self._main_window is None:
            raise RuntimeError("Not connected — call connect() first")
        return self._main_window

    def list_visible_window_titles(self, limit: int = 25) -> list[str]:
        """Top-level window titles visible to UIA (for diagnostics)."""
        titles: list[str] = []
        for win in self._desktop.windows():
            try:
                text = (win.window_text() or "").strip()
                if text and text not in titles:
                    titles.append(text)
            except Exception:
                continue
            if len(titles) >= limit:
                break
        return titles

    def _try_attach_window(self, criteria: dict[str, Any]) -> BaseWrapper | None:
        """Return a ready top-level window wrapper, or None if this criteria set fails."""
        try:
            window = self._desktop.window(**criteria)
            window.wait("exists visible", timeout=3)
            return window
        except ElementAmbiguousError:
            elements = find_elements(
                backend=self._backend,
                top_level_only=True,
                **criteria,
            )
            if not elements:
                return None
            window = self._desktop.window(handle=elements[-1].handle)
            window.wait("exists visible", timeout=3)
            return window
        except (ElementNotFoundError, PywinautoTimeoutError):
            return None

    def bring_to_foreground(self, window: BaseWrapper) -> None:
        """Force a window to the foreground (needed when the terminal has focus)."""
        try:
            import ctypes

            hwnd = int(window.handle)
            ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            ctypes.windll.user32.SetForegroundWindow(hwnd)
        except Exception:
            pass
        try:
            window.set_focus()
        except Exception:
            pass

    def _is_patient_record_window(self, win: BaseWrapper) -> bool:
        title_pattern = re.compile(PATIENT_RECORD_TITLE_RE)
        try:
            info = win.element_info
            auto_id = (info.automation_id or "").strip()
            name = (info.name or "").strip()
            text = (win.window_text() or "").strip()
            return (
                auto_id == PATIENT_RECORD_AUTO_ID
                or name == PATIENT_RECORD_AUTO_ID
                or PATIENT_RECORD_AUTO_ID in auto_id
                or PATIENT_RECORD_AUTO_ID in name
                or bool(title_pattern.search(text))
                or bool(title_pattern.search(name))
            )
        except Exception:
            return False

    def _has_patient_record_markers(self, win: BaseWrapper) -> bool:
        if self._is_patient_record_window(win):
            return True
        return self._scan_descendant_by_object_name(win, "btn_save") is not None

    def list_patient_record_windows(self) -> list[BaseWrapper]:
        """Top-level windows that look like Patient Record (name or btn_save inside)."""
        handles_seen: set[int] = set()
        windows: list[BaseWrapper] = []
        for win in self._desktop.windows():
            try:
                if not self._has_patient_record_markers(win):
                    continue
                handle = self._window_handle(win)
                if handle in handles_seen:
                    continue
                handles_seen.add(handle)
                windows.append(win)
            except Exception:
                continue
        return windows

    def _click_descendant(self, scope: BaseWrapper, object_name: str) -> None:
        control = self._scan_descendant_by_object_name(scope, object_name)
        if control is None:
            raise ControlNotFoundError(
                f"Control '{object_name}' not found under {scope.window_text()!r}"
            )
        control.click_input()

    def try_open_new_patient_record(self, main: BaseWrapper) -> str:
        """Try several UI paths to open Patient Record; returns the method used."""
        self.bring_to_foreground(main)
        time.sleep(0.35)

        for method, action in (
            ("btn_new_patient", lambda: self._click_descendant(main, "btn_new_patient")),
            (
                "menu_file_new",
                lambda: main.type_keys("%fn", pause=0.08, set_foreground=True),
            ),
            ("shortcut_ctrl_n", lambda: main.type_keys("^n", set_foreground=True)),
        ):
            try:
                action()
                return method
            except (ControlNotFoundError, PywinautoTimeoutError, OSError):
                self.bring_to_foreground(main)
                continue

        self.bring_to_foreground(main)
        main.type_keys("^n", set_foreground=True)
        return "shortcut_ctrl_n_forced"

    @staticmethod
    def _window_handle(win: BaseWrapper) -> int:
        return int(win.element_info.handle)

    def _scan_for_main_window(self) -> BaseWrapper | None:
        """Qt UIA often exposes objectName (win_main) instead of setWindowTitle."""
        for win in self._desktop.windows():
            try:
                info = win.element_info
                auto_id = (info.automation_id or "").strip()
                name = (info.name or "").strip()
                text = (win.window_text() or "").strip()
                matched = (
                    auto_id == MAIN_AUTO_ID
                    or name == MAIN_AUTO_ID
                    or text == MAIN_AUTO_ID
                    or text == MAIN_TITLE
                    or name == MAIN_TITLE
                )
                if not matched:
                    continue
                win.wait("exists visible", timeout=3)
                return win
            except Exception:
                continue
        return None

    def connect(self, title: str = MAIN_TITLE) -> BaseWrapper:
        """Attach to the simulator main window."""
        # PyQt6 + UIA: Name/Title is often objectName (win_main), not setWindowTitle.
        search_sets: list[dict[str, Any]] = [
            {"auto_id": MAIN_AUTO_ID},
            {"title": MAIN_AUTO_ID},
            {"title": title},
            {"title_re": MAIN_TITLE_RE},
            {"title_re": r".*Kroll by Telus.*"},
        ]

        end = time.monotonic() + self._timeout
        last_error: Exception | None = None
        while time.monotonic() < end:
            scanned = self._scan_for_main_window()
            if scanned is not None:
                self._main_window = scanned
                return scanned
            for criteria in search_sets:
                window = self._try_attach_window(criteria)
                if window is not None:
                    self._main_window = window
                    return window
            last_error = PywinautoTimeoutError("no matching simulator window")
            time.sleep(0.35)

        hints = self.list_visible_window_titles()
        hint_block = ""
        if hints:
            sample = "\n  ".join(hints[:12])
            hint_block = f"\n\nVisible top-level windows (sample):\n  {sample}"
        raise ControlNotFoundError(
            f"Simulator main window '{title}' not found within {self._timeout}s.\n"
            "Start the simulator first in another terminal:\n"
            "  python apps/pharmacy_simulator/main.py\n"
            "Then leave the main window open (not minimized) and retry."
            f"{hint_block}"
        ) from last_error

    def wait_for_window(
        self,
        *,
        title_re: str | None = None,
        title: str | None = None,
        automation_id: str | None = None,
        timeout: float | None = None,
    ) -> BaseWrapper:
        wait_for = timeout if timeout is not None else self._timeout
        criteria: dict[str, Any] = {}
        if title_re:
            criteria["title_re"] = title_re
        if title:
            criteria["title"] = title
        if automation_id:
            criteria["auto_id"] = automation_id
        window = self._desktop.window(**criteria)
        window.wait("exists visible", timeout=wait_for)
        return window

    def wait_for_patient_record(
        self,
        timeout: float | None = None,
        *,
        exclude_handles: set[int] | None = None,
    ) -> BaseWrapper:
        """Wait for a Patient Record window; prefers newest when several are open."""
        wait_for = timeout if timeout is not None else self._timeout
        prior_count = len(exclude_handles) if exclude_handles else 0
        end = time.monotonic() + wait_for
        while time.monotonic() < end:
            candidates = self.list_patient_record_windows()
            if exclude_handles:
                fresh = [
                    w
                    for w in candidates
                    if self._window_handle(w) not in exclude_handles
                ]
                if fresh:
                    window = fresh[-1]
                    window.set_focus()
                    return window
            if len(candidates) > prior_count:
                window = candidates[-1]
                window.set_focus()
                return window
            time.sleep(0.35)
        hint = ""
        if exclude_handles:
            hint = (
                f" ({len(exclude_handles)} existing record(s) still open — "
                "close extra Patient Record windows or retry)"
            )
        with_save = [
            (w.window_text() or "").strip()
            for w in self._desktop.windows()
            if self._scan_descendant_by_object_name(w, "btn_save") is not None
        ]
        save_hint = ""
        if with_save:
            save_hint = f"\nWindows containing btn_save: {with_save!r}"

        raise ControlNotFoundError(
            f"Patient Record window not found within {wait_for}s{hint} "
            f"(looked for {PATIENT_RECORD_AUTO_ID!r}, Patient Record title, or btn_save)."
            f"{save_hint}\n"
            "Ensure the simulator main window is focused and not minimized."
        )

    def _scan_descendant_by_object_name(
        self, scope: BaseWrapper, object_name: str
    ) -> BaseWrapper | None:
        """Qt UIA: Name is objectName; AutomationId is often a long dotted path."""
        suffix = f".{object_name}"
        for desc in scope.descendants():
            try:
                info = desc.element_info
                name = (info.name or "").strip()
                auto_id = (info.automation_id or "").strip()
                if name == object_name or auto_id == object_name or auto_id.endswith(suffix):
                    return desc
            except Exception:
                continue
        return None

    def _set_date_value(self, control: BaseWrapper, wrapper: BaseWrapper, value: str) -> None:
        """Set date fields: QLineEdit (txt_dob) or QDateEdit Spinner (deceased, etc.)."""
        match = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", value.strip())
        control_type = (control.element_info.control_type or "").lower()

        if "edit" in control_type and "spinner" not in control_type:
            wrapper.set_focus()
            try:
                wrapper.set_edit_text(value)
            except Exception:
                wrapper.click_input()
                wrapper.type_keys("^a", set_foreground=True)
                wrapper.type_keys(value, with_spaces=False, set_foreground=True)
            return

        if match:
            year, month, day = match.groups()
            wrapper.click_input()
            time.sleep(0.15)
            wrapper.type_keys("{HOME}", set_foreground=True)
            wrapper.type_keys(year, with_spaces=False, set_foreground=True)
            wrapper.type_keys("{RIGHT}", set_foreground=True)
            wrapper.type_keys(month, with_spaces=False, set_foreground=True)
            wrapper.type_keys("{RIGHT}", set_foreground=True)
            wrapper.type_keys(day, with_spaces=False, set_foreground=True)
            wrapper.type_keys("{TAB}", set_foreground=True)
            return

        wrapper.click_input()
        wrapper.type_keys("^a", set_foreground=True)
        wrapper.type_keys(value, with_spaces=False, set_foreground=True)
        wrapper.type_keys("{TAB}", set_foreground=True)

    def _get_date_value(self, wrapper: BaseWrapper) -> str:
        """Read QDateEdit value from Spinner or nested Edit controls."""
        parts: list[str] = []
        for target in wrapper.descendants():
            try:
                ctype = (target.element_info.control_type or "").lower()
                if "edit" not in ctype:
                    continue
                text = (target.window_text() or "").strip()
                if text and text.isdigit():
                    parts.append(text)
            except Exception:
                continue
        if len(parts) >= 3:
            year, month, day = parts[0], parts[1], parts[2]
            if len(year) == 4:
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

        for getter in (
            lambda: wrapper.window_text(),
            lambda: wrapper.get_value(),
        ):
            try:
                text = (getter() or "").strip()
                if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
                    return text
            except Exception:
                continue
        return ""

    def _set_combo_value(self, wrapper: BaseWrapper, value: str) -> None:
        """Set QComboBox via select(), list item click, or keyboard type-ahead."""
        if not value:
            return
        try:
            wrapper.select(value)
            if (self._get_combo_value(wrapper) or "").strip() == value:
                return
        except Exception:
            pass

        wrapper.click_input()
        time.sleep(0.2)
        try:
            wrapper.type_keys("%{DOWN}", set_foreground=True)
            time.sleep(0.25)
        except Exception:
            pass

        for item in wrapper.descendants():
            try:
                text = (item.window_text() or "").strip()
                if text == value:
                    item.click_input()
                    return
            except Exception:
                continue

        wrapper.click_input()
        wrapper.type_keys("^a{BACKSPACE}", set_foreground=True)
        wrapper.type_keys(value, with_spaces=False, set_foreground=True)
        wrapper.type_keys("{ENTER}", set_foreground=True)

    def _get_combo_value(self, wrapper: BaseWrapper) -> str:
        for getter in (
            lambda: wrapper.selected_text(),
            lambda: wrapper.window_text(),
            lambda: (wrapper.texts() or [None])[0],
        ):
            try:
                text = getter()
                if text is not None and str(text).strip():
                    return str(text).strip()
            except Exception:
                continue
        return ""

    @staticmethod
    def _control_wrapper(control: BaseWrapper) -> BaseWrapper:
        """UIA Desktop wrappers may already be the control (no wrapper_object)."""
        try:
            return control.wrapper_object()
        except AttributeError:
            return control

    def find_control(self, scope: BaseWrapper, object_name: str) -> BaseWrapper:
        """Find a descendant by accessible Name / objectName (Qt UIA-friendly)."""
        scanned = self._scan_descendant_by_object_name(scope, object_name)
        if scanned is not None:
            return scanned

        if hasattr(scope, "child_window"):
            for kwargs in (
                {"title": object_name},
                {"auto_id": object_name},
                {"best_match": object_name},
            ):
                try:
                    control = scope.child_window(**kwargs, found_index=0)
                    control.wait("exists", timeout=2)
                    return control
                except (
                    AttributeError,
                    ElementNotFoundError,
                    ElementAmbiguousError,
                    PywinautoTimeoutError,
                ):
                    continue

        raise ControlNotFoundError(
            f"Control '{object_name}' not found under {scope.window_text()!r}"
        )

    def click(self, scope: BaseWrapper, object_name: str) -> None:
        control = self.find_control(scope, object_name)
        control.click_input()

    def send_shortcut(self, scope: BaseWrapper, keys: str) -> None:
        scope.set_focus()
        scope.type_keys(keys, set_foreground=True)

    def get_value(self, scope: BaseWrapper, object_name: str) -> str:
        control = self.find_control(scope, object_name)
        wrapper = self._control_wrapper(control)
        control_type = (control.element_info.control_type or "").lower()

        if "checkbox" in control_type:
            try:
                return "true" if wrapper.get_toggle_state() == 1 else "false"
            except Exception:
                return "true" if wrapper.is_checked() else "false"

        if "combobox" in control_type:
            return self._get_combo_value(wrapper)

        if "spinner" in control_type or "date" in object_name:
            parsed = self._get_date_value(wrapper)
            if parsed:
                return parsed

        try:
            text = wrapper.window_text()
            if text:
                return text
        except Exception:
            pass

        try:
            return wrapper.get_value() or ""
        except Exception:
            return ""

    def set_value(self, scope: BaseWrapper, object_name: str, value: str) -> None:
        control = self.find_control(scope, object_name)
        wrapper = self._control_wrapper(control)
        control_type = (control.element_info.control_type or "").lower()
        normalized = value.strip()

        if "checkbox" in control_type:
            want_on = normalized.lower() in ("1", "true", "yes", "on")
            try:
                is_on = wrapper.get_toggle_state() == 1
            except Exception:
                is_on = wrapper.is_checked()
            if is_on != want_on:
                wrapper.click_input()
            return

        if "combobox" in control_type:
            self._set_combo_value(wrapper, normalized)
            return

        if "spinner" in control_type or "date" in object_name:
            self._set_date_value(control, wrapper, normalized)
            return

        wrapper.set_focus()
        try:
            wrapper.set_edit_text(normalized)
        except Exception:
            wrapper.type_keys("^a{BACKSPACE}", set_foreground=True)
            if normalized:
                wrapper.type_keys(normalized, with_spaces=False, set_foreground=True)

    def enumerate_controls(self, scope: BaseWrapper) -> list[ControlInfo]:
        records: list[ControlInfo] = []
        for desc in scope.descendants():
            try:
                info = desc.element_info
                auto_id = (info.automation_id or "").strip()
                name = (info.name or "").strip()
                if not auto_id and not name:
                    continue
                records.append(
                    ControlInfo(
                        automation_id=auto_id,
                        name=name,
                        control_type=str(info.control_type or ""),
                        class_name=str(info.class_name or ""),
                    )
                )
            except Exception:
                continue
        return records

    def dismiss_message_box(self, title: str, button: str = "OK") -> None:
        try:
            dialog = self._desktop.window(title=title)
            dialog.wait("exists visible", timeout=3)
            dialog.child_window(title=button, control_type="Button").click_input()
        except (ElementNotFoundError, PywinautoTimeoutError):
            pass

    def screenshot(self, path: Path, scope: BaseWrapper | None = None) -> Path | None:
        """Save a window capture; returns None if Pillow is missing or capture fails."""
        target = scope or self.main_window
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            image = target.capture_as_image()
        except Exception:
            image = None
        if image is None:
            return None
        try:
            image.save(str(path))
            return path
        except Exception:
            return None
