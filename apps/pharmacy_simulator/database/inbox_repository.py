"""Inbox document persistence and file storage."""

from __future__ import annotations

import json
import shutil
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from apps.pharmacy_simulator.database.db_path import DB_PATH, INBOX_STORAGE, PROJECT_ROOT
from apps.pharmacy_simulator.database.schema import SCHEMA_STATEMENTS

_SAMPLE_MANIFEST = PROJECT_ROOT / "config" / "sample_inbox.json"
_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
_PDF_EXTENSIONS = {".pdf"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class InboxRepository:
    """SQLite + filesystem storage for incoming documents."""

    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = db_path or str(DB_PATH)
        INBOX_STORAGE.mkdir(parents=True, exist_ok=True)
        self._init_schema()
        self._seed_samples_if_empty()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            for statement in SCHEMA_STATEMENTS:
                conn.execute(statement)

    def _seed_samples_if_empty(self) -> None:
        if self.count_documents() > 0:
            return
        if not _SAMPLE_MANIFEST.exists():
            return

        with _SAMPLE_MANIFEST.open(encoding="utf-8") as handle:
            samples = json.load(handle)

        for sample in samples:
            rel = sample.get("relative_path", "")
            src = PROJECT_ROOT / rel
            if not src.exists():
                continue
            dest_name = f"sample_{sample['file_name']}"
            dest = INBOX_STORAGE / dest_name
            shutil.copy2(src, dest)
            self.add_document(
                source_type=str(sample.get("source_type", "Upload")),
                subject=str(sample.get("subject", "")),
                sender=str(sample.get("sender", "")),
                file_path=str(dest),
                file_name=str(sample.get("file_name", dest.name)),
            )

    def count_documents(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS cnt FROM inbox_documents").fetchone()
        return int(row["cnt"]) if row else 0

    def list_documents(self, source_type: str = "") -> list[dict[str, Any]]:
        sql = """
            SELECT id, source_type, subject, sender, file_name, file_path, received_at, status
            FROM inbox_documents
        """
        params: tuple[str, ...] = ()
        if source_type.strip():
            sql += " WHERE source_type = ?"
            params = (source_type.strip(),)
        sql += " ORDER BY received_at DESC"

        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]

    def get_document(self, document_id: int) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM inbox_documents WHERE id = ?",
                (document_id,),
            ).fetchone()
        return dict(row) if row else None

    def add_document(
        self,
        source_type: str,
        subject: str,
        sender: str,
        file_path: str,
        file_name: str | None = None,
    ) -> int:
        path = Path(file_path)
        now = _utc_now()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO inbox_documents
                    (source_type, subject, sender, file_name, file_path, received_at, status)
                VALUES (?, ?, ?, ?, ?, ?, 'New')
                """,
                (
                    source_type,
                    subject,
                    sender,
                    file_name or path.name,
                    str(path.resolve()),
                    now,
                ),
            )
            return int(cursor.lastrowid)

    def import_upload(
        self,
        source_path: str,
        source_type: str = "Upload",
        subject: str = "",
        sender: str = "",
    ) -> int:
        src = Path(source_path)
        if not src.exists():
            raise FileNotFoundError(source_path)

        ext = src.suffix.lower()
        stored_name = f"{uuid.uuid4().hex[:10]}_{src.name}"
        dest = INBOX_STORAGE / stored_name
        shutil.copy2(src, dest)

        if not subject:
            subject = src.stem.replace("_", " ").title()

        return self.add_document(
            source_type=source_type,
            subject=subject,
            sender=sender or "Local Upload",
            file_path=str(dest),
            file_name=src.name,
        )

    def update_status(self, document_id: int, status: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE inbox_documents SET status = ? WHERE id = ?",
                (status, document_id),
            )

    def delete_document(self, document_id: int) -> None:
        doc = self.get_document(document_id)
        if doc is None:
            return
        path = Path(str(doc.get("file_path", "")))
        with self._connect() as conn:
            conn.execute("DELETE FROM inbox_documents WHERE id = ?", (document_id,))
        if path.exists() and INBOX_STORAGE in path.resolve().parents:
            path.unlink(missing_ok=True)

    @staticmethod
    def is_image(path: str) -> bool:
        return Path(path).suffix.lower() in _IMAGE_EXTENSIONS

    @staticmethod
    def is_pdf(path: str) -> bool:
        return Path(path).suffix.lower() in _PDF_EXTENSIONS
