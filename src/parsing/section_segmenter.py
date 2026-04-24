from __future__ import annotations

import re
from typing import List, Tuple

from src.parsing.schema import CanonicalSection, MatchStrategy, ConfidenceLevel


SECTION_PATTERNS = {
    "item_1a_risk_factors": [
        r"item\s*1a[\.\:\-\s]*risk\s*factors",
    ],
    "item_3_legal_proceedings": [
        r"item\s*3[\.\:\-\s]*legal\s*proceedings",
    ],
    "item_7_md&a": [
        r"item\s*7[\.\:\-\s]*(management[’'`s]{0,2}\s+discussion\s+and\s+analysis|management\s+discussion\s+and\s+analysis)",
    ],
    "item_7a_quantitative_disclosures": [
        r"item\s*7a[\.\:\-\s]*quantitative\s+and\s+qualitative\s+disclosures",
    ],
    "item_8_financial_statements": [
        r"item\s*8[\.\:\-\s]*financial\s+statements",
    ],
}


def _find_section_matches(text: str) -> List[Tuple[str, re.Match]]:
    matches: List[Tuple[str, re.Match]] = []

    for normalized_name, patterns in SECTION_PATTERNS.items():
        for pattern in patterns:
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                matches.append((normalized_name, match))

    matches.sort(key=lambda item: item[1].start())
    return matches


def segment_sections(doc_id: str, text: str) -> List[CanonicalSection]:
    matches = _find_section_matches(text)

    if not matches:
        return [
            CanonicalSection(
                section_id=f"{doc_id}_other_0",
                normalized_section="other",
                raw_heading=None,
                content=text.strip(),
                start_offset=0,
                end_offset=len(text),
                match_strategy=MatchStrategy.FALLBACK,
                match_confidence=ConfidenceLevel.LOW,
                validation_flags=["no_reliable_headings_found"],
            )
        ]

    sections: List[CanonicalSection] = []

    for idx, (section_name, match) in enumerate(matches):
        start = match.start()
        end = matches[idx + 1][1].start() if idx + 1 < len(matches) else len(text)
        raw_heading = match.group(0)
        content = text[start:end].strip()

        flags = []
        if any(
            section_name == existing.normalized_section for existing in sections
        ):
            flags.append("header_ambiguous")

        sections.append(
            CanonicalSection(
                section_id=f"{doc_id}_{section_name}_{idx}",
                normalized_section=section_name,
                raw_heading=raw_heading,
                content=content,
                start_offset=start,
                end_offset=end,
                match_strategy=MatchStrategy.REGEX,
                match_confidence=ConfidenceLevel.HIGH,
                validation_flags=flags,
            )
        )

    return sections