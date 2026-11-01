#!/usr/bin/env python3
"""Fetch an open-access PDF for a DOI using OpenAlex and Europe PMC.

Usage: fetch_oa.py DOI_OR_URL [--out DIR] [--key CITEKEY]

Exit codes: 0 = saved, 2 = no open-access PDF found, 3 = no DOI found.
"""

from __future__ import annotations

import argparse
import http.client
import json
import re
import socket
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

USER_AGENT = "lit-kb/1.0"
DOI_RE = re.compile(r"10\.\d{4,9}/\S+", re.IGNORECASE)

OPENALEX_TIMEOUT = 30
EUROPEPMC_TIMEOUT = 30
DOWNLOAD_TIMEOUT = 60

NET_ERRORS = (
    HTTPError,
    URLError,
    TimeoutError,
    socket.timeout,
    http.client.HTTPException,
    OSError,
)


def reason(exc: BaseException) -> str:
    """Return a short human-readable cause for a network exception."""
    if isinstance(exc, HTTPError):
        return f"HTTP {exc.code} {exc.reason}"
    if isinstance(exc, URLError):
        return f"URLError {exc.reason}"
    if isinstance(exc, (TimeoutError, socket.timeout)):
        return "timeout"
    return f"{type(exc).__name__}: {exc}"


def normalize_doi(raw: str) -> str | None:
    """Return the bare DOI contained in raw input, or None if no DOI pattern is present."""
    s = raw.strip()
    for _ in range(3):
        t = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", s, flags=re.IGNORECASE)
        t = re.sub(r"^doi:\s*", "", t, flags=re.IGNORECASE)
        t = t.strip()
        if t == s:
            break
        s = t
    match = DOI_RE.search(s)
    return match.group(0) if match else None


def get_json_safe(url: str, timeout: int) -> Any | None:
    """Return JSON decoded from url, or None on network or decode failure."""
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except NET_ERRORS as exc:
        print(f"fail {url}: {reason(exc)}")
        return None
    except json.JSONDecodeError as exc:
        print(f"fail {url}: JSONDecodeError: {exc}")
        return None


def openalex_summary(work: dict[str, Any]) -> dict[str, Any]:
    """Return title, year, first author, journal, is_oa, and oa_status from an OpenAlex work."""
    authorships = work.get("authorships") or []
    first_author = ""
    if authorships and isinstance(authorships[0], dict):
        author = authorships[0].get("author") or {}
        first_author = author.get("display_name") or ""

    journal = ""
    primary = work.get("primary_location") or {}
    if isinstance(primary, dict) and isinstance(primary.get("source"), dict):
        journal = primary["source"].get("display_name") or ""
    if not journal:
        best = work.get("best_oa_location") or {}
        if isinstance(best, dict) and isinstance(best.get("source"), dict):
            journal = best["source"].get("display_name") or ""

    oa = work.get("open_access") or {}
    return {
        "title": work.get("title") or "",
        "year": work.get("publication_year"),
        "first_author": first_author,
        "journal": journal,
        "is_oa": oa.get("is_oa"),
        "oa_status": oa.get("oa_status"),
    }


def openalex_pdf_candidates(work: dict[str, Any]) -> list[str]:
    """Return deduplicated OpenAlex PDF URLs (best_oa_location first, then all locations)."""
    urls: list[str] = []
    seen: set[str] = set()

    def add(value: Any) -> None:
        if isinstance(value, str) and value and value not in seen:
            seen.add(value)
            urls.append(value)

    best = work.get("best_oa_location") or {}
    if isinstance(best, dict):
        add(best.get("pdf_url"))
    for loc in work.get("locations") or []:
        if isinstance(loc, dict):
            add(loc.get("pdf_url"))
    return urls


def europepmc_pdf_candidates(doi: str) -> list[str]:
    """Return Europe PMC PDF render URLs for open-access records matching doi."""
    query = quote(f'DOI:"{doi}"', safe=":")
    url = (
        "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
        f"?query={query}&format=json&resultType=core"
    )
    data = get_json_safe(url, EUROPEPMC_TIMEOUT)
    if not isinstance(data, dict):
        return []
    results = (data.get("resultList") or {}).get("result") or []
    urls: list[str] = []
    for record in results:
        if not isinstance(record, dict):
            continue
        pmcid = record.get("pmcid")
        if pmcid and record.get("isOpenAccess") == "Y":
            urls.append(f"https://europepmc.org/articles/{pmcid}?pdf=render")
            urls.append(f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/pdf/")
            urls.append(f"XML:https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML")
    return urls


def try_download(url: str, out_path: Path) -> bool:
    """Download url, save body to out_path if it starts with %PDF, and report success."""
    req = Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/pdf,*/*"},
    )
    try:
        with urlopen(req, timeout=DOWNLOAD_TIMEOUT) as resp:
            body = resp.read()
    except NET_ERRORS as exc:
        print(f"fail {url}: {reason(exc)}")
        return False

    if not body.startswith(b"%PDF"):
        print(f"fail {url}: response is not a PDF")
        return False

    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(body)
    except OSError as exc:
        print(f"fail {out_path}: {reason(exc)}")
        return False

    print(f"saved {out_path} from {url}")
    return True


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and return a process exit code."""
    parser = argparse.ArgumentParser(
        description="Fetch an open-access PDF for a DOI via OpenAlex and Europe PMC."
    )
    parser.add_argument("doi_or_url", help="DOI or URL containing a DOI")
    parser.add_argument(
        "--out",
        default="reference/literature/pdfs",
        help="output directory (default: reference/literature/pdfs)",
    )
    parser.add_argument("--key", help="output filename stem (default: DOI, / replaced by _)")
    args = parser.parse_args(argv)

    doi = normalize_doi(args.doi_or_url)
    if doi is None:
        print("no DOI found")
        return 3

    out_path = Path(args.out) / f"{args.key or doi.replace('/', '_')}.pdf"

    summary: dict[str, Any] | None = None
    candidates: list[str] = []

    work = get_json_safe(f"https://api.openalex.org/works/doi:{doi}", OPENALEX_TIMEOUT)
    if isinstance(work, dict):
        summary = openalex_summary(work)
        for key, value in summary.items():
            print(f"{key}: {value}")
        candidates = openalex_pdf_candidates(work)
        print("candidates:")
        for candidate in candidates:
            print(f"  {candidate}")
    else:
        print("openalex: unavailable")

    seen = set(candidates)
    for candidate in europepmc_pdf_candidates(doi):
        if candidate not in seen:
            seen.add(candidate)
            candidates.append(candidate)
            print(f"candidate: {candidate}")

    preprint_hosts = ("biorxiv.org", "medrxiv.org", "arxiv.org", "researchsquare.com", "preprints.org")
    # Prefer published versions; preprints last.
    candidates.sort(key=lambda u: any(h in u for h in preprint_hosts))
    xml_urls = [c[4:] for c in candidates if c.startswith("XML:")]
    candidates = [c for c in candidates if not c.startswith("XML:")]
    for candidate in candidates:
        if try_download(candidate, out_path):
            if any(h in candidate for h in preprint_hosts):
                print("version: PREPRINT (published version not openly downloadable; check differences)")
            else:
                print("version: published")
            return 0

    for xml_url in xml_urls:  # full text (no PDF): fine for reading/summarizing
        try:
            req = Request(xml_url, headers={"User-Agent": "lit-kb/1.0"})
            with urlopen(req, timeout=60) as resp:
                body = resp.read()
            if b"<article" in body[:5000]:
                xml_path = out_path.with_suffix(".xml")
                xml_path.parent.mkdir(parents=True, exist_ok=True)
                xml_path.write_bytes(body)
                print(f"saved {xml_path} from {xml_url}")
                print("version: published (full-text XML, no PDF)")
                return 0
        except Exception as exc:  # noqa: BLE001 - report and continue
            print(f"fail {xml_url}: {reason(exc)}")
    print("NO_OA_PDF")
    if summary is not None:
        for key, value in summary.items():
            print(f"{key}: {value}")
    else:
        print(f"doi: {doi}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
