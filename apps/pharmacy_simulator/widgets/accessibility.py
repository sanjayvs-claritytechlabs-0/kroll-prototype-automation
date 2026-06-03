"""Helpers for exposing objectName and accessibleName on all controls."""

from PyQt6.QtWidgets import QWidget


def set_accessible(
    widget: QWidget,
    object_name: str,
    accessible_name: str | None = None,
) -> QWidget:
    """Set objectName and accessibleName (defaults to object_name). Returns widget for chaining."""
    widget.setObjectName(object_name)
    widget.setAccessibleName(accessible_name if accessible_name is not None else object_name)
    return widget
