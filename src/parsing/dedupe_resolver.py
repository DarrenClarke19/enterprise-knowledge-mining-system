from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ExistingDocInfo:
    doc_id: str
    accession_number: str
    filing_type: str
    source_sha256: str
    is_active_for_retrieval: bool


@dataclass
class DedupeDecision:
    lifecycle_status: str
    is_active_for_retrieval: bool
    supersedes_doc_id: Optional[str] = None
    amendment_parent_doc_id: Optional[str] = None
    reason: Optional[str] = None


def is_amendment(filing_type: str) -> bool:
    return filing_type.endswith("/A")


def resolve_dedupe(
    incoming_accession: str,
    incoming_filing_type: str,
    incoming_sha256: str,
    existing_doc: Optional[ExistingDocInfo],
) -> DedupeDecision:
    if existing_doc is None:
        return DedupeDecision(
            lifecycle_status="accepted_primary",
            is_active_for_retrieval=True,
            reason="new_document",
        )

    if (
        incoming_accession == existing_doc.accession_number
        and incoming_sha256 == existing_doc.source_sha256
    ):
        return DedupeDecision(
            lifecycle_status="duplicate_fetch",
            is_active_for_retrieval=False,
            reason="exact_duplicate",
        )

    if is_amendment(incoming_filing_type):
        return DedupeDecision(
            lifecycle_status="accepted_amendment",
            is_active_for_retrieval=True,
            amendment_parent_doc_id=existing_doc.doc_id,
            reason="amendment_supersedes_prior",
        )

    return DedupeDecision(
        lifecycle_status="accepted_primary",
        is_active_for_retrieval=True,
        supersedes_doc_id=existing_doc.doc_id,
        reason="newer_primary_replaces_prior",
    )