from __future__ import annotations

import hashlib
from datetime import datetime, UTC
from pathlib import Path
from bs4 import BeautifulSoup

from src.parsing.schema import CanonicalFiling, Provenance, LifecycleStatus
from src.parsing.section_segmenter import segment_sections


def clean_html_to_text(raw_html: str) -> str:
    soup = BeautifulSoup(raw_html, "lxml")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines()]
    non_empty = [line for line in lines if line]
    return "\n".join(non_empty)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_doc_id(cik: str, accession_number: str) -> str:
    return f"{cik}_{accession_number.replace('-', '')}"


def parse_raw_filing(
    raw_html: str,
    ticker: str,
    company_name: str,
    cik: str,
    accession_number: str,
    filing_type: str,
    filing_date: str,
    source_url: str,
) -> CanonicalFiling:
    cleaned_text = clean_html_to_text(raw_html)
    doc_id = build_doc_id(cik, accession_number)
    sections = segment_sections(doc_id, cleaned_text)

    provenance = Provenance(
        source_url=source_url,
        source_sha256=sha256_text(raw_html),
        fetched_at=datetime.now(UTC).isoformat(),
        parser_version="0.1.0",
    )

    return CanonicalFiling(
        doc_id=doc_id,
        ticker=ticker,
        company_name=company_name,
        cik=cik,
        accession_number=accession_number,
        filing_type=filing_type,
        filing_date=filing_date,
        lifecycle_status=LifecycleStatus.ACCEPTED_PRIMARY,
        is_active_for_retrieval=True,
        provenance=provenance,
        sections=sections,
        validation_flags=[],
    )