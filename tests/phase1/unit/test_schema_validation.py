import pytest

from src.parsing.schema import (
    CanonicalFiling,
    CanonicalSection,
    Provenance,
    MatchStrategy,
    ConfidenceLevel,
    LifecycleStatus,
)


def build_valid_section():
    return CanonicalSection(
        section_id="doc_item1a_0",
        normalized_section="item_1a_risk_factors",
        raw_heading="Item 1A. Risk Factors",
        content="Item 1A. Risk Factors\nSome risk text here.",
        start_offset=0,
        end_offset=40,
        match_strategy=MatchStrategy.REGEX,
        match_confidence=ConfidenceLevel.HIGH,
        validation_flags=[],
    )


def build_valid_provenance():
    return Provenance(
        source_url="https://example.com/doc.htm",
        source_sha256="a" * 64,
        fetched_at="2026-04-23T12:00:00+00:00",
        parser_version="0.1.0",
    )


def test_valid_canonical_filing_passes():
    filing = CanonicalFiling(
        doc_id="0000789019_000078901924000012",
        ticker="MSFT",
        company_name="Microsoft Corporation",
        cik="0000789019",
        accession_number="0000789019-24-000012",
        filing_type="10-K",
        filing_date="2024-07-30",
        lifecycle_status=LifecycleStatus.ACCEPTED_PRIMARY,
        provenance=build_valid_provenance(),
        sections=[build_valid_section()],
    )
    assert filing.doc_id.startswith("0000789019")


def test_invalid_accession_fails():
    with pytest.raises(Exception):
        CanonicalFiling(
            doc_id="bad",
            ticker="MSFT",
            company_name="Microsoft Corporation",
            cik="0000789019",
            accession_number="bad-accession",
            filing_type="10-K",
            filing_date="2024-07-30",
            lifecycle_status=LifecycleStatus.ACCEPTED_PRIMARY,
            provenance=build_valid_provenance(),
            sections=[build_valid_section()],
        )