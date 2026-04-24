from __future__ import annotations

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
import re


ACCESSION_PATTERN = re.compile(r"^\d{10}-\d{2}-\d{6}$")


class LifecycleStatus(str, Enum):
    ACCEPTED_PRIMARY = "accepted_primary"
    DUPLICATE_FETCH = "duplicate_fetch"
    ACCEPTED_AMENDMENT = "accepted_amendment"
    SUPERSEDED_BY_AMENDMENT = "superseded_by_amendment"
    REJECTED_PARSE_FAILURE = "rejected_parse_failure"
    QUARANTINED = "quarantined"


class MatchStrategy(str, Enum):
    REGEX = "regex"
    TOC_ANCHOR = "toc_anchor"
    HEURISTIC = "heuristic"
    FALLBACK = "fallback"


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Provenance(BaseModel):
    source_url: str
    source_sha256: str
    fetched_at: str
    parser_version: str


class CanonicalSection(BaseModel):
    section_id: str
    normalized_section: str
    raw_heading: Optional[str] = None
    content: str
    start_offset: int
    end_offset: int
    match_strategy: MatchStrategy
    match_confidence: ConfidenceLevel
    validation_flags: List[str] = Field(default_factory=list)

    @field_validator("end_offset")
    @classmethod
    def end_must_be_greater_than_start(cls, value: int, info):
        start = info.data.get("start_offset")
        if start is not None and value <= start:
            raise ValueError("end_offset must be greater than start_offset")
        return value

    @field_validator("content")
    @classmethod
    def content_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("section content must not be empty")
        return value


class CanonicalFiling(BaseModel):
    doc_id: str
    ticker: str
    company_name: str
    cik: str
    accession_number: str
    filing_type: str
    filing_date: str
    report_period: Optional[str] = None

    lifecycle_status: LifecycleStatus
    is_active_for_retrieval: bool = True

    supersedes_doc_id: Optional[str] = None
    superseded_by_doc_id: Optional[str] = None
    amendment_parent_doc_id: Optional[str] = None

    provenance: Provenance
    sections: List[CanonicalSection]
    validation_flags: List[str] = Field(default_factory=list)

    @field_validator("accession_number")
    @classmethod
    def validate_accession_number(cls, value: str) -> str:
        if not ACCESSION_PATTERN.match(value):
            raise ValueError("invalid accession number format")
        return value

    @field_validator("cik")
    @classmethod
    def cik_must_be_10_digits(cls, value: str) -> str:
        if not re.fullmatch(r"\d{10}", value):
            raise ValueError("CIK must be exactly 10 digits")
        return value

    @model_validator(mode="after")
    def validate_sections_and_lineage(self) -> "CanonicalFiling":
        sorted_sections = sorted(self.sections, key=lambda s: s.start_offset)

        for i in range(1, len(sorted_sections)):
            prev = sorted_sections[i - 1]
            curr = sorted_sections[i]
            if curr.start_offset < prev.end_offset:
                raise ValueError("sections overlap")

        if self.lifecycle_status == LifecycleStatus.ACCEPTED_AMENDMENT:
            if not self.amendment_parent_doc_id:
                raise ValueError(
                    "accepted_amendment requires amendment_parent_doc_id"
                )

        return self