"""Shuffle UI layouts while preserving control objectName / accessibleName."""

from __future__ import annotations

import random
from typing import Sequence

from PyQt6.QtWidgets import QFormLayout, QLayout, QVBoxLayout, QWidget

FormRow = tuple[QWidget | None, QWidget]


def _add_form_row(form: QFormLayout, label: QWidget | None, field: QWidget) -> None:
    """Add a form row; checkboxes use a single widget (no separate label)."""
    if label is None or label is field:
        form.addRow(field)
    else:
        form.addRow(label, field)


def _clear_form_rows(form: QFormLayout) -> None:
    """Remove all rows without deleting widgets (removeRow would delete them)."""
    while form.rowCount() > 0:
        form.takeRow(0)


def restore_form_rows(form: QFormLayout, rows: Sequence[FormRow]) -> None:
    """Restore form rows to their original order."""
    _clear_form_rows(form)
    for label, field in rows:
        _add_form_row(form, label, field)


def shuffle_form_rows(form: QFormLayout, rows: Sequence[FormRow]) -> None:
    """Reorder form rows; labels and fields keep their objectName."""
    _clear_form_rows(form)
    order = list(rows)
    random.shuffle(order)
    for label, field in order:
        _add_form_row(form, label, field)


def clear_layout(layout: QLayout, host: QWidget | None = None) -> None:
    """Remove all items from a layout; optional host keeps child widgets alive."""
    while layout.count() > 0:
        item = layout.takeAt(0)
        if item is None:
            break
        widget = item.widget()
        if widget is not None:
            if host is not None:
                widget.setParent(host)
            continue
        child_layout = item.layout()
        if child_layout is not None:
            clear_layout(child_layout, host)


def shuffle_widgets_in_layout(
    layout: QVBoxLayout,
    widgets: Sequence[QWidget],
    host: QWidget | None = None,
) -> None:
    """Stack widgets in random order inside a vertical layout."""
    clear_layout(layout, host)
    order = list(widgets)
    random.shuffle(order)
    for widget in order:
        layout.addWidget(widget)
