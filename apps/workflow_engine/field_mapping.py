"""Map extracted patient fields to Patient Record objectNames."""

from __future__ import annotations

# Extraction keys → General tab objectName
EXTRACTION_TO_RECORD: dict[str, str] = {
    "first_name": "txt_first_name",
    "last_name": "txt_last_name",
    "middle_name": "txt_middle_name",
    "dob": "txt_dob",
    "gender": "cmb_gender",
    "phone": "txt_phone",
    "email": "txt_email",
    "address_line1": "txt_address_line1",
    "address_line2": "txt_address_line2",
    "city": "txt_city",
    "province": "cmb_province",
    "postal_code": "txt_postal_code",
    "health_card": "txt_health_card",
    "delivery_type": "cmb_delivery_type",
    "delivery_route": "cmb_delivery_route",
    "price_group": "cmb_price_group",
    "comments": "txt_comments",
}


def record_fields_from_extraction(
    extracted: dict[str, str],
    defaults: dict[str, str] | None = None,
) -> dict[str, str]:
    """Build objectName-keyed field map for Patient Record automation."""
    merged = dict(defaults or {})
    for src_key, object_name in EXTRACTION_TO_RECORD.items():
        value = extracted.get(src_key, "").strip()
        if value:
            merged[object_name] = value
    return merged
