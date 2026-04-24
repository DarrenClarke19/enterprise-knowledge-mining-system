from src.parsing.dedupe_resolver import (
    ExistingDocInfo,
    resolve_dedupe,
)


def test_new_primary_is_accepted():
    decision = resolve_dedupe(
        incoming_accession="0000789019-24-000012",
        incoming_filing_type="10-K",
        incoming_sha256="abc123",
        existing_doc=None,
    )
    assert decision.lifecycle_status == "accepted_primary"
    assert decision.is_active_for_retrieval is True


def test_exact_duplicate_fetch_is_inactive():
    existing = ExistingDocInfo(
        doc_id="doc1",
        accession_number="0000789019-24-000012",
        filing_type="10-K",
        source_sha256="abc123",
        is_active_for_retrieval=True,
    )
    decision = resolve_dedupe(
        incoming_accession="0000789019-24-000012",
        incoming_filing_type="10-K",
        incoming_sha256="abc123",
        existing_doc=existing,
    )
    assert decision.lifecycle_status == "duplicate_fetch"
    assert decision.is_active_for_retrieval is False