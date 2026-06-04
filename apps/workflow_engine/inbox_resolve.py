"""Resolve inbox documents for workflows (stable match, not fragile row index)."""

from __future__ import annotations

from typing import Any

from apps.pharmacy_simulator.database.inbox_repository import InboxRepository


def list_inbox_display_order(repo: InboxRepository) -> list[dict[str, Any]]:
    """Same order as Inbox UI grid (newest first)."""
    return repo.list_documents()


def resolve_inbox_document(
    repo: InboxRepository,
    config: dict[str, Any],
) -> tuple[dict[str, Any] | None, str | None]:
    """
    Pick document by explicit id, file_name, subject substring, or display row.
    Returns (document, error_message).
    """
    doc_id = config.get("document_id")
    if doc_id is not None:
        doc = repo.get_document(int(doc_id))
        if doc is None:
            return None, f"document_id {doc_id} not found"
        return doc, None

    file_name = str(config.get("document_file_name", "")).strip()
    if file_name:
        for doc in list_inbox_display_order(repo):
            if doc.get("file_name") == file_name:
                return doc, None
            if file_name in str(doc.get("file_path", "")):
                return doc, None
        return None, f"No inbox document with file_name {file_name!r}"

    subject_contains = str(config.get("document_subject_contains", "")).strip()
    if subject_contains:
        needle = subject_contains.lower()
        for doc in list_inbox_display_order(repo):
            if needle in str(doc.get("subject", "")).lower():
                return doc, None
        return None, f"No inbox document with subject containing {subject_contains!r}"

    docs = list_inbox_display_order(repo)
    if not docs:
        return None, "Inbox is empty"

    row = int(config.get("document_row", 0))
    if row < 0 or row >= len(docs):
        return None, f"document_row {row} out of range ({len(docs)} documents)"
    return docs[row], None


def inbox_grid_row_index(repo: InboxRepository, document_id: int) -> int | None:
    """Row index in the Inbox table for a given document id."""
    for index, doc in enumerate(list_inbox_display_order(repo)):
        if int(doc["id"]) == document_id:
            return index
    return None
