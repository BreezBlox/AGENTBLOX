#!/usr/bin/env python3
"""
Validate and normalize links in eBay candidate-card markdown reports.

Why this exists:
- eBay item-page links (/itm/{id}) expire, redirect, or become irrelevant over time.
- A report can look complete while containing dead or low-confidence links.

This tool provides:
1) Link audit (HTTP status + lightweight relevance checks).
2) Optional normalization that replaces eBay comp links with evergreen sold-search URLs.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import dataclasses
import glob
import pathlib
import re
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Iterable


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)

STOPWORDS = {
    "and",
    "the",
    "for",
    "with",
    "set",
    "kit",
    "inch",
    "in",
    "tier",
    "slide",
    "out",
    "piece",
    "pc",
    "pcs",
    "plus",
    "new",
}

EBAY_COMP_MARKER = "- eBay comp links (3-5):"
SOURCE_LINK_MARKER = "- Source links:"
CANDIDATE_PREFIX = "## Candidate Card - "
PRIMARY_TERMS_PREFIX = "- Primary search terms used:"


@dataclasses.dataclass
class Candidate:
    title: str
    start_line: int
    end_line: int
    primary_terms: list[str]


@dataclasses.dataclass
class LinkRecord:
    report: pathlib.Path
    candidate: str
    line: int
    url: str
    link_type: str
    keyword_overlap: int
    status_code: int | None = None
    final_url: str | None = None
    fetch_error: str | None = None
    warnings: list[str] = dataclasses.field(default_factory=list)
    failures: list[str] = dataclasses.field(default_factory=list)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit and optionally normalize links in candidate-card markdown reports."
    )
    parser.add_argument("reports", nargs="*", help="Markdown report path(s), directory path(s), or glob(s)")
    parser.add_argument(
        "--all-reports",
        action="store_true",
        help="Include all markdown files from reports/ or ebay-arbitrage-plugin/reports/",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=12.0,
        help="Per-request timeout in seconds (default: 12)",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=1,
        help="Retry count for transient network failures (default: 1)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=12,
        help="Concurrent link checks (default: 12)",
    )
    parser.add_argument(
        "--skip-network",
        action="store_true",
        help="Run structural/relevance checks only, no HTTP requests",
    )
    parser.add_argument(
        "--normalize-ebay-links",
        action="store_true",
        help="Replace eBay comp links with sold-search URLs based on primary terms",
    )
    parser.add_argument(
        "--normalize-source-links",
        action="store_true",
        help="Replace source links with AliExpress search URLs based on primary terms",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write normalized content back to file (requires --normalize-ebay-links)",
    )
    parser.add_argument(
        "--strict-warnings",
        action="store_true",
        help="Exit non-zero if warnings are present",
    )
    return parser.parse_args()


def has_wildcard(value: str) -> bool:
    return any(char in value for char in "*?[]")


def default_report_dirs() -> list[pathlib.Path]:
    candidates = [
        pathlib.Path("reports"),
        pathlib.Path("ebay-arbitrage-plugin/reports"),
    ]
    return [path for path in candidates if path.is_dir()]


def resolve_report_paths(
    report_inputs: list[str],
    include_all_reports: bool,
) -> tuple[list[pathlib.Path], list[pathlib.Path]]:
    targets = list(report_inputs)
    if include_all_reports:
        for report_dir in default_report_dirs():
            targets.append(str(report_dir / "*.md"))

    seen: set[str] = set()
    resolved: list[pathlib.Path] = []
    missing: list[pathlib.Path] = []

    for target in targets:
        path = pathlib.Path(target)
        matches: list[pathlib.Path] = []

        if path.exists():
            if path.is_dir():
                matches = sorted(candidate for candidate in path.rglob("*.md") if candidate.is_file())
            elif path.is_file():
                matches = [path]
        elif has_wildcard(target):
            matches = sorted(
                pathlib.Path(candidate)
                for candidate in glob.glob(target, recursive=True)
                if pathlib.Path(candidate).is_file()
            )
        else:
            missing.append(path)
            continue

        for match in matches:
            if match.suffix.lower() != ".md":
                continue
            key = str(match.resolve())
            if key in seen:
                continue
            seen.add(key)
            resolved.append(match)

    return resolved, missing


def tokenize(value: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", value.lower())
    return [token for token in tokens if len(token) >= 3 and token not in STOPWORDS]


def extract_primary_terms(line: str) -> list[str]:
    return [value.strip() for value in re.findall(r"`([^`]+)`", line)]


def normalize_title_for_query(title: str) -> str:
    normalized = re.sub(r"\([^)]*\)", "", title)
    normalized = re.sub(r"[^a-zA-Z0-9 ]+", " ", normalized)
    return " ".join(normalized.split()).strip()


def build_sold_search_url(query: str) -> str:
    encoded = urllib.parse.quote_plus(query)
    return (
        "https://www.ebay.com/sch/i.html?"
        f"_nkw={encoded}&LH_Sold=1&LH_Complete=1&_sop=13"
    )


def build_aliexpress_search_url(query: str) -> str:
    encoded = urllib.parse.quote_plus(query)
    return f"https://www.aliexpress.us/wholesale?SearchText={encoded}"


def unique_preserving_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        key = value.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        ordered.append(value.strip())
    return ordered


def normalize_report_text(text: str, normalize_ebay_links: bool, normalize_source_links: bool) -> tuple[str, int, int]:
    lines = text.splitlines(keepends=True)
    current_title = ""
    current_terms: list[str] = []
    ebay_replacements = 0
    source_replacements = 0
    i = 0

    while i < len(lines):
        stripped = lines[i].strip()

        if stripped.startswith(CANDIDATE_PREFIX):
            current_title = stripped[len(CANDIDATE_PREFIX) :].strip()
            current_terms = []
            i += 1
            continue

        if stripped.startswith(PRIMARY_TERMS_PREFIX):
            current_terms = extract_primary_terms(stripped)
            i += 1
            continue

        if normalize_ebay_links and stripped == EBAY_COMP_MARKER:
            j = i + 1
            ebay_link_lines: list[int] = []

            while j < len(lines):
                bullet_match = re.match(r"\s*-\s+(https?://\S+)\s*$", lines[j].strip())
                if not bullet_match:
                    break
                url = bullet_match.group(1)
                netloc = urllib.parse.urlparse(url).netloc.lower()
                if "ebay." in netloc:
                    ebay_link_lines.append(j)
                j += 1

            if ebay_link_lines:
                seed_queries = unique_preserving_order(
                    [*current_terms, normalize_title_for_query(current_title)]
                )
                if not seed_queries:
                    seed_queries = [normalize_title_for_query(current_title)]
                if not seed_queries:
                    seed_queries = ["ebay comp"]

                replacement_urls = [
                    build_sold_search_url(seed_queries[idx % len(seed_queries)])
                    for idx in range(len(ebay_link_lines))
                ]
                for target_idx, new_url in zip(ebay_link_lines, replacement_urls):
                    lines[target_idx] = f"  - {new_url}\n"
                    ebay_replacements += 1

            i = j
            continue

        if normalize_source_links and stripped.startswith(SOURCE_LINK_MARKER):
            j = i + 1
            source_link_lines: list[int] = []

            while j < len(lines):
                bullet_match = re.match(r"\s*-\s+(https?://\S+)\s*$", lines[j].strip())
                if not bullet_match:
                    break
                source_link_lines.append(j)
                j += 1

            if source_link_lines:
                seed_queries = unique_preserving_order(
                    [*current_terms, normalize_title_for_query(current_title)]
                )
                if not seed_queries:
                    seed_queries = [normalize_title_for_query(current_title)]
                if not seed_queries:
                    seed_queries = ["aliexpress product"]

                replacement_urls = [
                    build_aliexpress_search_url(seed_queries[idx % len(seed_queries)])
                    for idx in range(len(source_link_lines))
                ]
                for target_idx, new_url in zip(source_link_lines, replacement_urls):
                    lines[target_idx] = f"  - {new_url}\n"
                    source_replacements += 1

            i = j
            continue

        if normalize_source_links:
            bullet_match = re.match(r"\s*[-\d\)\.]+\s+(https?://\S+)\s*$", stripped)
            if bullet_match:
                url = bullet_match.group(1)
                netloc = urllib.parse.urlparse(url).netloc.lower()
                if "alibaba.com" in netloc:
                    seed_queries = unique_preserving_order(
                        [*current_terms, normalize_title_for_query(current_title)]
                    )
                    query = seed_queries[0] if seed_queries else normalize_title_for_query(current_title) or "aliexpress product"
                    lines[i] = re.sub(
                        re.escape(url),
                        build_aliexpress_search_url(query),
                        lines[i],
                        count=1,
                    )
                    source_replacements += 1
                    i += 1
                    continue

        i += 1

    return "".join(lines), ebay_replacements, source_replacements


def parse_candidates(text: str) -> list[Candidate]:
    lines = text.splitlines()
    candidates: list[Candidate] = []
    current_title: str | None = None
    current_start = 1
    current_terms: list[str] = []

    for idx, line in enumerate(lines, start=1):
        if line.startswith(CANDIDATE_PREFIX):
            if current_title is not None:
                candidates.append(
                    Candidate(
                        title=current_title,
                        start_line=current_start,
                        end_line=idx - 1,
                        primary_terms=current_terms,
                    )
                )
            current_title = line[len(CANDIDATE_PREFIX) :].strip()
            current_start = idx
            current_terms = []
            continue

        if current_title and line.startswith(PRIMARY_TERMS_PREFIX):
            current_terms = extract_primary_terms(line)

    if current_title is not None:
        candidates.append(
            Candidate(
                title=current_title,
                start_line=current_start,
                end_line=len(lines),
                primary_terms=current_terms,
            )
        )
    return candidates


def classify_link(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    netloc = parsed.netloc.lower()
    path = parsed.path.lower()
    if "ebay." in netloc:
        if path.startswith("/itm/"):
            return "ebay_item"
        if path.startswith("/sch/i.html"):
            return "ebay_search"
        if path.startswith("/b/"):
            return "ebay_category"
        return "ebay_other"
    if "aliexpress." in netloc:
        if path.startswith("/wholesale") or "/w/wholesale" in path:
            return "aliexpress_search"
        return "aliexpress_other"
    if "alibaba.com" in netloc:
        return "alibaba_disallowed"
    return "other"


def candidate_keywords(candidate: Candidate) -> set[str]:
    combined = " ".join([candidate.title, *candidate.primary_terms])
    return set(tokenize(combined))


def url_keyword_overlap(url: str, keywords: set[str]) -> int:
    parsed = urllib.parse.urlparse(url)
    text = urllib.parse.unquote(f"{parsed.path} {parsed.query}")
    text = text.replace("-", " ").replace("_", " ").replace("+", " ")
    url_tokens = set(tokenize(text))
    return len(url_tokens & keywords)


def extract_link_records(report_path: pathlib.Path, text: str) -> list[LinkRecord]:
    lines = text.splitlines()
    candidates = parse_candidates(text)
    records: list[LinkRecord] = []

    for candidate in candidates:
        keywords = candidate_keywords(candidate)
        for line_no in range(candidate.start_line, candidate.end_line + 1):
            line = lines[line_no - 1]
            for url in re.findall(r"https?://[^\s)]+", line):
                link_type = classify_link(url)
                overlap = url_keyword_overlap(url, keywords) if keywords else 0
                records.append(
                    LinkRecord(
                        report=report_path,
                        candidate=candidate.title,
                        line=line_no,
                        url=url,
                        link_type=link_type,
                        keyword_overlap=overlap,
                    )
                )
    return records


def fetch_url(url: str, timeout: float, retries: int) -> tuple[int | None, str | None, str | None]:
    headers = {"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"}
    last_error: str | None = None
    last_code: int | None = None
    last_url: str | None = None

    for attempt in range(retries + 1):
        request = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return int(response.getcode()), response.geturl(), None
        except urllib.error.HTTPError as exc:
            last_code = int(exc.code)
            last_url = exc.geturl() or url
            last_error = str(exc)
            if exc.code in {429, 500, 502, 503, 504} and attempt < retries:
                continue
            return last_code, last_url, last_error
        except (urllib.error.URLError, socket.timeout, TimeoutError) as exc:
            last_error = str(exc)
            if attempt < retries:
                continue
            return None, None, last_error

    return last_code, last_url, last_error


def is_ebay(link_type: str) -> bool:
    return link_type.startswith("ebay_")


def evaluate_record(record: LinkRecord) -> None:
    if record.link_type == "alibaba_disallowed":
        record.failures.append("alibaba links disallowed; use aliexpress links only")
        return

    if record.link_type == "ebay_item":
        record.warnings.append(
            "direct eBay item link is fragile; prefer sold-search URLs for evergreen reports"
        )

    if record.link_type != "ebay_item" and record.keyword_overlap == 0:
        if record.link_type in {"ebay_search", "ebay_category", "ebay_other", "aliexpress_search", "aliexpress_other"}:
            record.warnings.append("no keyword overlap between candidate terms and URL text")

    if record.status_code is None and record.fetch_error:
        if is_ebay(record.link_type):
            record.warnings.append("eBay URL could not be verified from this runtime")
        else:
            record.failures.append("network error while fetching URL")
        return

    if record.status_code is None:
        return

    code = record.status_code
    if 200 <= code < 400:
        return

    if is_ebay(record.link_type) and code in {403, 429, 500, 503}:
        record.warnings.append(f"eBay returned HTTP {code} (often bot/rate-limit/proxy sensitive)")
        return

    if code in {404, 410, 451}:
        record.failures.append(f"HTTP {code}")
        return

    if code >= 400:
        if is_ebay(record.link_type):
            record.warnings.append(f"eBay returned HTTP {code}")
        else:
            record.failures.append(f"HTTP {code}")


def check_records_network(records: list[LinkRecord], timeout: float, retries: int, workers: int) -> None:
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
        future_map = {
            executor.submit(fetch_url, record.url, timeout, retries): record for record in records
        }
        for future in concurrent.futures.as_completed(future_map):
            record = future_map[future]
            try:
                code, final_url, error = future.result()
            except Exception as exc:  # defensive catch for thread failures
                code, final_url, error = None, None, str(exc)
            record.status_code = code
            record.final_url = final_url
            record.fetch_error = error


def print_results(records: list[LinkRecord], report_path: pathlib.Path) -> tuple[int, int]:
    failures = [record for record in records if record.failures]
    warnings = [record for record in records if record.warnings and not record.failures]

    print(f"\nReport: {report_path}")
    print(f"Links checked: {len(records)}")

    for record in failures:
        reason = "; ".join(record.failures)
        print(
            f"[FAIL] {report_path}:{record.line} | {record.candidate} | {record.url} | {reason}"
        )

    for record in warnings:
        reason = "; ".join(record.warnings)
        code = f"HTTP {record.status_code}" if record.status_code is not None else "NO_HTTP_STATUS"
        print(
            f"[WARN] {report_path}:{record.line} | {record.candidate} | {record.url} | {code} | {reason}"
        )

    ok_count = len(records) - len(warnings) - len(failures)
    print(
        f"Summary: ok={ok_count} warn={len(warnings)} fail={len(failures)} total={len(records)}"
    )
    return len(warnings), len(failures)


def process_report(
    report_path: pathlib.Path,
    args: argparse.Namespace,
) -> tuple[int, int]:
    original_text = report_path.read_text(encoding="utf-8")
    working_text = original_text

    if args.normalize_ebay_links or args.normalize_source_links:
        normalized_text, ebay_replacements, source_replacements = normalize_report_text(
            working_text,
            normalize_ebay_links=args.normalize_ebay_links,
            normalize_source_links=args.normalize_source_links,
        )
        working_text = normalized_text
        print(
            f"\n{report_path}: normalized {ebay_replacements} eBay comp link(s), "
            f"{source_replacements} source link(s)"
        )
        if args.write and normalized_text != original_text:
            report_path.write_text(normalized_text, encoding="utf-8")
            print(f"{report_path}: wrote normalized content")

    records = extract_link_records(report_path, working_text)
    if not args.skip_network and records:
        check_records_network(records, args.timeout, args.retries, args.workers)

    for record in records:
        evaluate_record(record)

    return print_results(records, report_path)


def main() -> int:
    args = parse_args()
    if args.write and not (args.normalize_ebay_links or args.normalize_source_links):
        print("--write requires --normalize-ebay-links or --normalize-source-links", file=sys.stderr)
        return 2
    if not args.reports and not args.all_reports:
        print("provide report path(s) or use --all-reports", file=sys.stderr)
        return 2

    all_warnings = 0
    all_failures = 0
    report_paths, missing_paths = resolve_report_paths(args.reports, args.all_reports)

    for missing_path in missing_paths:
        print(f"missing report: {missing_path}", file=sys.stderr)
        all_failures += 1

    if not report_paths:
        print("no report files matched", file=sys.stderr)
        return 2 if all_failures == 0 else 1

    for report_path in report_paths:
        warnings, failures = process_report(report_path, args)
        all_warnings += warnings
        all_failures += failures

    if all_failures > 0:
        return 1
    if args.strict_warnings and all_warnings > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
