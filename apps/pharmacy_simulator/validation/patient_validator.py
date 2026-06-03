"""Validation rules for patient General tab fields."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class ValidationError:
    field: str
    message: str
    object_name: str


_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PHONE_DIGITS_RE = re.compile(r"\D")
_HEALTH_CARD_RE = re.compile(r"^[A-Za-z0-9\-]{4,20}$")
_POSTAL_CODE_RE = re.compile(r"^[A-Za-z]\d[A-Za-z][ -]?\d[A-Za-z]\d$")


def validate_patient(data: dict[str, str | bool]) -> list[ValidationError]:
    """Return all validation errors; empty list means valid."""
    errors: list[ValidationError] = []

    last_name = str(data.get("last_name", "")).strip()
    if not last_name:
        errors.append(ValidationError("last_name", "Last Name is required.", "txt_last_name"))

    dob = str(data.get("dob", "")).strip()
    if dob:
        errors.extend(_validate_dob(dob))
    else:
        errors.append(ValidationError("dob", "Date Of Birth is required.", "txt_dob"))

    phone = str(data.get("phone", "")).strip()
    if phone:
        errors.extend(_validate_phone(phone))

    email = str(data.get("email", "")).strip()
    if email and not _EMAIL_RE.match(email):
        errors.append(ValidationError("email", "Enter a valid email address.", "txt_email"))

    health_card = str(data.get("health_card", "")).strip()
    if health_card and not _HEALTH_CARD_RE.match(health_card):
        errors.append(
            ValidationError(
                "health_card",
                "Health card must be 4–20 letters, numbers, or hyphens.",
                "txt_health_card",
            )
        )

    postal_code = str(data.get("postal_code", "")).strip()
    if postal_code and not _POSTAL_CODE_RE.match(postal_code):
        errors.append(
            ValidationError(
                "postal_code",
                "Postal code format should be A1A 1A1.",
                "txt_postal_code",
            )
        )

    return errors


def _validate_dob(dob: str) -> list[ValidationError]:
    try:
        parsed = datetime.strptime(dob, "%Y-%m-%d").date()
    except ValueError:
        return [ValidationError("dob", "Date Of Birth must be YYYY-MM-DD.", "txt_dob")]

    today = date.today()
    if parsed > today:
        return [ValidationError("dob", "Date Of Birth cannot be in the future.", "txt_dob")]

    age_years = today.year - parsed.year - ((today.month, today.day) < (parsed.month, parsed.day))
    if age_years > 130:
        return [ValidationError("dob", "Date Of Birth is not valid.", "txt_dob")]

    return []


def _validate_phone(phone: str) -> list[ValidationError]:
    digits = _PHONE_DIGITS_RE.sub("", phone)
    if len(digits) < 10:
        return [ValidationError("phone", "Phone must contain at least 10 digits.", "txt_phone")]
    if len(digits) > 15:
        return [ValidationError("phone", "Phone number is too long.", "txt_phone")]
    return []
