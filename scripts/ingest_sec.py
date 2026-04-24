from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

import requests

from src.parsing.parser import parse_raw_filing


BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
CANONICAL_DIR = BASE_DIR / "data" / "processed" / "canonical_docs"

RAW_DIR.mkdir(parents=True, exist_ok=True)
CANONICAL_DIR.mkdir(parents=True, exist_ok=True)

SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
SEC_ARCHIVES_BASE = "https://www.sec.gov/Archives/edgar/data"

TARGET_COMPANIES = {
    "MSFT": {
        "company_name": "Microsoft Corporation",
        "cik": "0000789019",
    },
    "AMZN": {
        "company_name": "Amazon.com, Inc.",
        "cik": "0001018724",
    },
    "NVDA": {
        "company_name": "NVIDIA Corporation",
        "cik": "0001045810",
    },
}

TARGET_FORMS = {"10-K", "10-Q"}
TARGET_YEARS = {2022, 2023, 2024}

# Use your own email here or load from .env.
SEC_USER_AGENT = os.getenv(
    "SEC_USER_AGENT",
    "Darren Clarke darrenjustinclarke@yahoo.com",
)

HEADERS = {
    "User-Agent": SEC_USER_AGENT,
    "Accept-Encoding": "gzip, deflate",
    "Host": "data.sec.gov",
}


def get_json(url: str, headers: dict[str, str]) -> dict[str, Any]:
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


def get_text(url: str, headers: dict[str, str]) -> str:
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.text


def build_primary_document_url(cik: str, accession_number: str, primary_document: str) -> str:
    cik_int = str(int(cik))
    accession_no_dashes = accession_number.replace("-", "")
    return f"{SEC_ARCHIVES_BASE}/{cik_int}/{accession_no_dashes}/{primary_document}"


def save_raw_html(
    ticker: str,
    filing_type: str,
    filing_date: str,
    accession_number: str,
    primary_document: str,
    html_text: str,
) -> Path:
    out_dir = RAW_DIR / ticker / filing_type
    out_dir.mkdir(parents=True, exist_ok=True)

    safe_name = f"{filing_date}_{accession_number}_{primary_document}"
    out_path = out_dir / safe_name
    out_path.write_text(html_text, encoding="utf-8")
    return out_path


def save_canonical_json(ticker: str, filing_type: str, filing_date: str, doc_id: str, filing_obj: Any) -> Path:
    out_dir = CANONICAL_DIR / ticker / filing_type
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / f"{filing_date}_{doc_id}.json"

    if hasattr(filing_obj, "model_dump"):
        payload = filing_obj.model_dump()
    else:
        payload = filing_obj.dict()

    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out_path


def filter_recent_filings(submissions: dict[str, Any]) -> list[dict[str, str]]:
    recent = submissions.get("filings", {}).get("recent", {})

    forms = recent.get("form", [])
    filing_dates = recent.get("filingDate", [])
    accession_numbers = recent.get("accessionNumber", [])
    primary_documents = recent.get("primaryDocument", [])
    report_dates = recent.get("reportDate", [])

    filtered: list[dict[str, str]] = []

    for form, filing_date, accession_number, primary_document, report_date in zip(
        forms,
        filing_dates,
        accession_numbers,
        primary_documents,
        report_dates,
    ):
        if form not in TARGET_FORMS:
            continue

        year = int(filing_date[:4])
        if year not in TARGET_YEARS:
            continue

        filtered.append(
            {
                "form": form,
                "filing_date": filing_date,
                "accession_number": accession_number,
                "primary_document": primary_document,
                "report_date": report_date or "",
            }
        )

    return filtered


def ingest_company(ticker: str, company_name: str, cik: str, max_filings: int | None = None) -> None:
    print(f"\n=== Ingesting {ticker} ({company_name}) ===")

    submissions_url = SEC_SUBMISSIONS_URL.format(cik=cik)
    submissions_headers = {**HEADERS, "Host": "data.sec.gov"}

    submissions = get_json(submissions_url, submissions_headers)
    candidates = filter_recent_filings(submissions)

    if max_filings is not None:
        candidates = candidates[:max_filings]

    print(f"Found {len(candidates)} candidate filings for {ticker}")

    for filing in candidates:
        form = filing["form"]
        filing_date = filing["filing_date"]
        accession_number = filing["accession_number"]
        primary_document = filing["primary_document"]
        report_date = filing["report_date"]

        filing_url = build_primary_document_url(
            cik=cik,
            accession_number=accession_number,
            primary_document=primary_document,
        )

        print(f"Downloading {ticker} {form} {filing_date} -> {primary_document}")

        try:
            archive_headers = {**HEADERS, "Host": "www.sec.gov"}
            raw_html = get_text(filing_url, archive_headers)

            raw_path = save_raw_html(
                ticker=ticker,
                filing_type=form,
                filing_date=filing_date,
                accession_number=accession_number,
                primary_document=primary_document,
                html_text=raw_html,
            )

            filing_obj = parse_raw_filing(
                raw_html=raw_html,
                ticker=ticker,
                company_name=company_name,
                cik=cik,
                accession_number=accession_number,
                filing_type=form,
                filing_date=filing_date,
                source_url=filing_url,
            )

            canonical_path = save_canonical_json(
                ticker=ticker,
                filing_type=form,
                filing_date=filing_date,
                doc_id=filing_obj.doc_id,
                filing_obj=filing_obj,
            )

            print(f"  raw saved      -> {raw_path}")
            print(f"  canonical saved -> {canonical_path}")

            # polite delay
            time.sleep(0.25)

        except Exception as exc:
            print(
                f"  FAILED for {ticker} {form} {filing_date} "
                f"{accession_number}: {exc}"
            )


def main() -> None:
    # Start small. Change to None later if you want all filtered filings.
    max_filings_per_company = 2

    for ticker, info in TARGET_COMPANIES.items():
        ingest_company(
            ticker=ticker,
            company_name=info["company_name"],
            cik=info["cik"],
            max_filings=max_filings_per_company,
        )


if __name__ == "__main__":
    main()