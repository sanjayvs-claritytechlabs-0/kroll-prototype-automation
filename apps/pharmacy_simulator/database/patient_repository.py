"""Patient and family member persistence."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any

from apps.pharmacy_simulator.database.db_path import DB_PATH
from apps.pharmacy_simulator.database.schema import SCHEMA_STATEMENTS

PATIENT_COLUMNS = (
    "patient_id",
    "first_name",
    "last_name",
    "middle_name",
    "dob",
    "gender",
    "phone",
    "email",
    "address_line1",
    "address_line2",
    "city",
    "province",
    "postal_code",
    "health_card",
    "active",
    "animal",
    "deceased_date",
    "delivery_type",
    "delivery_route",
    "price_group",
    "comments",
    "created_at",
    "last_modified_at",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class PatientRepository:
    """SQLite access for patient general data and family members."""

    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = db_path or str(DB_PATH)
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            for statement in SCHEMA_STATEMENTS:
                conn.execute(statement)

    def patient_exists(self, patient_id: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM patients WHERE patient_id = ?",
                (patient_id,),
            ).fetchone()
        return row is not None

    def list_patients(self) -> list[dict[str, str]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT patient_id, first_name, last_name, last_modified_at
                FROM patients
                ORDER BY last_modified_at DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def search_patients(
        self,
        first_name: str = "",
        last_name: str = "",
        dob: str = "",
    ) -> list[dict[str, str]]:
        """Case-insensitive partial match on name; exact match on DOB when provided."""
        clauses: list[str] = []
        params: list[str] = []

        if first_name.strip():
            clauses.append("LOWER(first_name) LIKE LOWER(?)")
            params.append(f"%{first_name.strip()}%")
        if last_name.strip():
            clauses.append("LOWER(last_name) LIKE LOWER(?)")
            params.append(f"%{last_name.strip()}%")
        if dob.strip():
            clauses.append("dob = ?")
            params.append(dob.strip())

        if not clauses:
            return []

        where = " AND ".join(clauses)
        sql = f"""
            SELECT patient_id, first_name, last_name, dob, phone
            FROM patients
            WHERE {where}
            ORDER BY last_name COLLATE NOCASE, first_name COLLATE NOCASE
            LIMIT 100
        """
        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]

    def get_patient(self, patient_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM patients WHERE patient_id = ?",
                (patient_id,),
            ).fetchone()
        if row is None:
            return None
        data = dict(row)
        data["active"] = bool(data["active"])
        data["animal"] = bool(data["animal"])
        return data

    def save_patient(self, data: dict[str, Any]) -> None:
        now = _utc_now()
        patient_id = str(data["patient_id"])
        exists = self.patient_exists(patient_id)
        if exists:
            existing = self.get_patient(patient_id)
            created_at = str(existing["created_at"]) if existing else now
        else:
            created_at = now

        values = {
            "patient_id": patient_id,
            "first_name": str(data.get("first_name", "")),
            "last_name": str(data.get("last_name", "")),
            "middle_name": str(data.get("middle_name", "")),
            "dob": str(data.get("dob", "")),
            "gender": str(data.get("gender", "")),
            "phone": str(data.get("phone", "")),
            "email": str(data.get("email", "")),
            "address_line1": str(data.get("address_line1", "")),
            "address_line2": str(data.get("address_line2", "")),
            "city": str(data.get("city", "")),
            "province": str(data.get("province", "")),
            "postal_code": str(data.get("postal_code", "")),
            "health_card": str(data.get("health_card", "")),
            "active": 1 if data.get("active", True) else 0,
            "animal": 1 if data.get("animal", False) else 0,
            "deceased_date": str(data.get("deceased_date", "")),
            "delivery_type": str(data.get("delivery_type", "")),
            "delivery_route": str(data.get("delivery_route", "")),
            "price_group": str(data.get("price_group", "")),
            "comments": str(data.get("comments", "")),
            "created_at": created_at,
            "last_modified_at": now,
        }

        placeholders = ", ".join("?" for _ in PATIENT_COLUMNS)
        columns = ", ".join(PATIENT_COLUMNS)
        updates = ", ".join(f"{col} = excluded.{col}" for col in PATIENT_COLUMNS if col != "patient_id")

        sql = f"""
            INSERT INTO patients ({columns})
            VALUES ({placeholders})
            ON CONFLICT(patient_id) DO UPDATE SET {updates}
        """

        with self._connect() as conn:
            conn.execute(sql, tuple(values[col] for col in PATIENT_COLUMNS))

    def get_family_members(self, patient_id: str) -> list[dict[str, str]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT member_patient_id, name, relationship
                FROM family_members
                WHERE patient_id = ?
                ORDER BY id
                """,
                (patient_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def save_family_members(self, patient_id: str, members: list[dict[str, str]]) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM family_members WHERE patient_id = ?", (patient_id,))
            conn.executemany(
                """
                INSERT INTO family_members (patient_id, member_patient_id, name, relationship)
                VALUES (?, ?, ?, ?)
                """,
                [
                    (
                        patient_id,
                        str(m.get("member_patient_id", "")),
                        str(m.get("name", "")),
                        str(m.get("relationship", "")),
                    )
                    for m in members
                ],
            )

    INSURANCE_COLUMNS = (
        "patient_id",
        "plan_type",
        "carrier",
        "policy_number",
        "group_number",
        "expiry_date",
        "relationship",
        "cardholder_name",
    )

    def get_insurance(self, patient_id: str) -> dict[str, str] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM patient_insurance WHERE patient_id = ?",
                (patient_id,),
            ).fetchone()
        return dict(row) if row else None

    def save_insurance(self, patient_id: str, data: dict[str, str]) -> None:
        values = {
            "patient_id": patient_id,
            "plan_type": str(data.get("plan_type", "")),
            "carrier": str(data.get("carrier", "")),
            "policy_number": str(data.get("policy_number", "")),
            "group_number": str(data.get("group_number", "")),
            "expiry_date": str(data.get("expiry_date", "")),
            "relationship": str(data.get("relationship", "")),
            "cardholder_name": str(data.get("cardholder_name", "")),
        }
        placeholders = ", ".join("?" for _ in self.INSURANCE_COLUMNS)
        columns = ", ".join(self.INSURANCE_COLUMNS)
        updates = ", ".join(
            f"{col} = excluded.{col}" for col in self.INSURANCE_COLUMNS if col != "patient_id"
        )
        sql = f"""
            INSERT INTO patient_insurance ({columns})
            VALUES ({placeholders})
            ON CONFLICT(patient_id) DO UPDATE SET {updates}
        """
        with self._connect() as conn:
            conn.execute(sql, tuple(values[col] for col in self.INSURANCE_COLUMNS))

    def get_allergies(self, patient_id: str) -> list[dict[str, str]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT allergy_name, source, date_reported, comments
                FROM patient_allergies
                WHERE patient_id = ?
                ORDER BY id
                """,
                (patient_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def save_allergies(self, patient_id: str, allergies: list[dict[str, str]]) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM patient_allergies WHERE patient_id = ?", (patient_id,))
            conn.executemany(
                """
                INSERT INTO patient_allergies (patient_id, allergy_name, source, date_reported, comments)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        patient_id,
                        str(a.get("allergy_name", "")),
                        str(a.get("source", "")),
                        str(a.get("date_reported", "")),
                        str(a.get("comments", "")),
                    )
                    for a in allergies
                ],
            )

    COMMUNICATIONS_COLUMNS = (
        "patient_id",
        "language",
        "refill_type",
        "pickup_preference",
    )

    def get_communications(self, patient_id: str) -> dict[str, str | list[dict[str, str]]]:
        with self._connect() as conn:
            prefs_row = conn.execute(
                "SELECT language, refill_type, pickup_preference FROM patient_communications WHERE patient_id = ?",
                (patient_id,),
            ).fetchone()
            method_rows = conn.execute(
                """
                SELECT message_type, notification_type, phone_number, email_address
                FROM communication_methods
                WHERE patient_id = ?
                ORDER BY id
                """,
                (patient_id,),
            ).fetchall()

        preferences = dict(prefs_row) if prefs_row else {}
        methods = [dict(row) for row in method_rows]
        return {"preferences": preferences, "methods": methods}

    def save_communications(
        self,
        patient_id: str,
        preferences: dict[str, str],
        methods: list[dict[str, str]],
    ) -> None:
        pref_values = {
            "patient_id": patient_id,
            "language": str(preferences.get("language", "")),
            "refill_type": str(preferences.get("refill_type", "")),
            "pickup_preference": str(preferences.get("pickup_preference", "")),
        }
        placeholders = ", ".join("?" for _ in self.COMMUNICATIONS_COLUMNS)
        columns = ", ".join(self.COMMUNICATIONS_COLUMNS)
        updates = ", ".join(
            f"{col} = excluded.{col}" for col in self.COMMUNICATIONS_COLUMNS if col != "patient_id"
        )
        pref_sql = f"""
            INSERT INTO patient_communications ({columns})
            VALUES ({placeholders})
            ON CONFLICT(patient_id) DO UPDATE SET {updates}
        """

        with self._connect() as conn:
            conn.execute(pref_sql, tuple(pref_values[col] for col in self.COMMUNICATIONS_COLUMNS))
            conn.execute("DELETE FROM communication_methods WHERE patient_id = ?", (patient_id,))
            conn.executemany(
                """
                INSERT INTO communication_methods
                    (patient_id, message_type, notification_type, phone_number, email_address)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        patient_id,
                        str(m.get("message_type", "")),
                        str(m.get("notification_type", "")),
                        str(m.get("phone_number", "")),
                        str(m.get("email_address", "")),
                    )
                    for m in methods
                ],
            )
