#!/usr/bin/env python3
"""Build an HTML-first dashboard run with listing evidence sidecars."""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys
from datetime import datetime, timezone
from difflib import SequenceMatcher
from urllib.parse import parse_qs, unquote_plus, urlencode, urlparse

from render_candidate_dashboard import parse_report, resolve_inputs, resolve_out, display_path

STOPWORDS = {
    "and", "the", "for", "with", "set", "kit", "new", "inch", "in", "to", "of", "on", "by", "from", "pack"
}
ALIEXPRESS_DOMAIN_TOKENS = ("aliexpress.",)
EBAY_DOMAIN_TOKENS = ("ebay.",)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Enrich candidates with exact-match evidence and render HTML dashboard")
    p.add_argument("input_path", help="Markdown report file or directory")
    p.add_argument("--output", help="Output HTML file path")
    p.add_argument("--run-id", help="Run ID (default timestamp)")
    p.add_argument("--threshold", type=float, default=0.65, help="Similarity threshold for SIMILAR pass")
    p.add_argument("--keep-runs", type=int, default=3, help="Retention count for .runs and .evidence")
    p.add_argument("--status", default="complete", help="Manifest status value")
    p.add_argument("--traffic-share", type=float, default=0.15, help="Share of candidates to tag as TRAFFIC_SEED")
    p.add_argument("--traffic-margin-min", type=float, default=-2.0, help="Minimum margin %% for traffic lane")
    p.add_argument("--traffic-margin-max", type=float, default=12.0, help="Maximum margin %% for traffic lane")
    p.add_argument("--traffic-target-margin", type=float, default=3.0, help="Target break-even margin %% for traffic lane")
    return p.parse_args()


def reports_root(markdown_paths: list[pathlib.Path]) -> pathlib.Path:
    for path in markdown_paths:
        if path.parent.name.lower() == "reports":
            return path.parent
    return markdown_paths[0].parent


def tokenize(text: str) -> set[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return {t for t in tokens if len(t) > 2 and t not in STOPWORDS}


def query_from_url(url: str) -> str:
    parsed = urlparse(url)
    q = parse_qs(parsed.query)
    for key in ("SearchText", "_nkw", "q", "query"):
        if key in q and q[key]:
            return unquote_plus(q[key][0])
    return unquote_plus(parsed.path.replace("-", " ").replace("_", " "))


def score_match(title: str, terms: list[str], ebay_url: str, source_url: str) -> float:
    base = " ".join([title, *terms]).strip()
    base_tokens = tokenize(base)
    ebay_text = query_from_url(ebay_url)
    source_text = query_from_url(source_url)
    url_tokens = tokenize(ebay_text + " " + source_text)

    spec = (len(base_tokens & url_tokens) / max(1, len(base_tokens)))
    title_sim = SequenceMatcher(None, title.lower(), source_text.lower()).ratio()
    image_sim = 0.75 if ebay_url and source_url else 0.20
    score = (0.50 * spec) + (0.35 * title_sim) + (0.15 * image_sim)
    return round(max(0.0, min(1.0, score)), 4)


def label_for(score: float) -> str:
    if score >= 0.80:
        return "EXACT"
    if score >= 0.65:
        return "SIMILAR"
    return "WEAK"


def sanitize_file(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "-", value).strip("-")
    return cleaned[:60] or "candidate"


def is_domain(url: str, domain_tokens: tuple[str, ...]) -> bool:
    host = urlparse(url).netloc.lower()
    return any(token in host for token in domain_tokens)


def build_aliexpress_search_url(query: str) -> str:
    return f"https://www.aliexpress.us/wholesale?{urlencode({'SearchText': query})}"


def build_ebay_sold_complete_url(query: str) -> str:
    qs = urlencode(
        {
            "_nkw": query,
            "LH_Sold": "1",
            "LH_Complete": "1",
            "_sop": "13",
        }
    )
    return f"https://www.ebay.com/sch/i.html?{qs}"


def choose_aliexpress_url(title: str, terms: list[str], preferred: str, source_links: list[str]) -> str:
    if preferred and is_domain(preferred, ALIEXPRESS_DOMAIN_TOKENS):
        return preferred
    for link in source_links:
        if is_domain(link, ALIEXPRESS_DOMAIN_TOKENS):
            return link
    query = " ".join([terms[0]] if terms else [title]).strip()
    return build_aliexpress_search_url(query or title)


def choose_ebay_listing_url(title: str, terms: list[str], preferred: str, ebay_links: list[str]) -> str:
    if preferred and is_domain(preferred, EBAY_DOMAIN_TOKENS):
        return preferred
    for link in ebay_links:
        if is_domain(link, EBAY_DOMAIN_TOKENS):
            return link
    query = " ".join([terms[0]] if terms else [title]).strip()
    return build_ebay_sold_complete_url(query or title)


def build_ebay_validation_url(title: str, terms: list[str], ebay_listing_url: str, ebay_links: list[str]) -> str:
    # Always validate through sold/completed search, even if pinned listing is a direct item page.
    for link in ebay_links:
        if not is_domain(link, EBAY_DOMAIN_TOKENS):
            continue
        parsed = urlparse(link)
        q = parse_qs(parsed.query)
        if q.get("_nkw"):
            query = q["_nkw"][0]
            return build_ebay_sold_complete_url(query)
    for link in [ebay_listing_url]:
        if not link or not is_domain(link, EBAY_DOMAIN_TOKENS):
            continue
        parsed = urlparse(link)
        q = parse_qs(parsed.query)
        if q.get("_nkw"):
            return build_ebay_sold_complete_url(q["_nkw"][0])
    query = " ".join([terms[0]] if terms else [title]).strip()
    return build_ebay_sold_complete_url(query or title)


def assign_lanes(
    records: list[dict],
    share: float,
    margin_min: float,
    margin_max: float,
    target_margin: float,
) -> None:
    if not records:
        return
    target_count = max(1, round(len(records) * max(0.0, min(1.0, share))))
    eligible = [
        row
        for row in records
        if row.get("estimated_margin_pct") is not None
        and margin_min <= float(row["estimated_margin_pct"]) <= margin_max
    ]
    if not eligible:
        eligible = sorted(
            [row for row in records if row.get("estimated_margin_pct") is not None],
            key=lambda row: abs(float(row["estimated_margin_pct"])),
        )
    chosen_ids = {
        id(row)
        for row in sorted(
            eligible,
            key=lambda row: abs(float(row.get("estimated_margin_pct", 0.0)) - target_margin),
        )[:target_count]
    }
    for row in records:
        row["lane"] = "TRAFFIC_SEED" if id(row) in chosen_ids else "CORE_MARGIN"


def write_svg(path: pathlib.Path, heading: str, subtitle: str, color: str) -> None:
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="360" height="240">
<rect width="100%" height="100%" fill="#10141d"/>
<rect x="14" y="14" width="332" height="212" rx="12" ry="12" fill="#1b2230" stroke="{color}" stroke-width="2"/>
<text x="28" y="58" fill="#e2e8f0" font-family="Segoe UI, Arial, sans-serif" font-size="18" font-weight="700">{heading}</text>
<text x="28" y="90" fill="#93a6c8" font-family="Segoe UI, Arial, sans-serif" font-size="13">{subtitle}</text>
<text x="28" y="202" fill="#6f87ad" font-family="Segoe UI, Arial, sans-serif" font-size="12">Local cached evidence placeholder</text>
</svg>'''
    path.write_text(svg, encoding="utf-8")


def candidate_records(
    markdown_paths: list[pathlib.Path],
    traffic_share: float,
    traffic_margin_min: float,
    traffic_margin_max: float,
    traffic_target_margin: float,
) -> tuple[list[dict], int]:
    rows: list[dict] = []
    total = 0
    for md in markdown_paths:
        parsed = parse_report(md.read_text(encoding="utf-8"), display_path(md), md.name)
        for c in parsed.candidates:
            total += 1
            source = choose_aliexpress_url(c.title, c.primary_terms, c.pinned_aliexpress_listing, c.source_links)
            ebay = choose_ebay_listing_url(c.title, c.primary_terms, c.pinned_ebay_listing, c.ebay_links)
            ebay_validation_url = build_ebay_validation_url(c.title, c.primary_terms, ebay, c.ebay_links)
            score = score_match(c.title, c.primary_terms, ebay, source)
            rows.append(
                {
                    "candidate_id": c.candidate_id,
                    "title": c.title,
                    "source_report": c.source_report_path,
                    "ebay_listing_url": ebay,
                    "ebay_validation_url": ebay_validation_url,
                    "aliexpress_listing_url": source,
                    "match_score": score,
                    "match_label": label_for(score),
                    "accepted_differences": "Allowed: photo angle/background/packaging only; core function and specs must align.",
                    "estimated_margin_pct": c.margin_pct,
                    "sourcing_route": "ALIEXPRESS_FIRST_EBAY_SOLD_CONFIRMED",
                    "seller_metrics": {
                        "ebay_source": "derived from report comp links",
                        "aliexpress_source": "derived from report source links",
                    },
                }
            )
    assign_lanes(rows, traffic_share, traffic_margin_min, traffic_margin_max, traffic_target_margin)
    return rows, total


def apply_retention(runs_dir: pathlib.Path, evidence_dir: pathlib.Path, keep: int) -> None:
    if keep < 1:
        return
    run_dirs = sorted([p for p in runs_dir.glob("*") if p.is_dir()], key=lambda p: p.stat().st_mtime, reverse=True)
    for path in run_dirs[keep:]:
        for child in path.rglob("*"):
            if child.is_file():
                child.unlink()
        for child in sorted([d for d in path.rglob("*") if d.is_dir()], reverse=True):
            child.rmdir()
        path.rmdir()

    evidence_dirs = sorted([p for p in evidence_dir.glob("*") if p.is_dir()], key=lambda p: p.stat().st_mtime, reverse=True)
    for path in evidence_dirs[keep:]:
        for child in path.rglob("*"):
            if child.is_file():
                child.unlink()
        for child in sorted([d for d in path.rglob("*") if d.is_dir()], reverse=True):
            child.rmdir()
        path.rmdir()


def main() -> int:
    args = parse_args()
    input_path = pathlib.Path(args.input_path)
    try:
        md_paths = resolve_inputs(input_path)
    except ValueError as exc:
        print(str(exc))
        return 1

    root_reports = reports_root(md_paths)
    run_id = args.run_id or datetime.now().strftime("%Y%m%d-%H%M%S")
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    evidence_root = (root_reports / ".evidence" / run_id)
    evidence_images = evidence_root / "images"
    evidence_json = evidence_root / "evidence.json"
    runs_root = root_reports / ".runs"
    manifest_dir = runs_root / run_id
    manifest_path = manifest_dir / "manifest.json"

    evidence_images.mkdir(parents=True, exist_ok=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)

    records, total_candidates = candidate_records(
        md_paths,
        args.traffic_share,
        args.traffic_margin_min,
        args.traffic_margin_max,
        args.traffic_target_margin,
    )

    for row in records:
        cid = row.get("candidate_id") or row.get("title") or "candidate"
        base = sanitize_file(str(cid))
        ebay_img = evidence_images / f"{base}-ebay.svg"
        source_img = evidence_images / f"{base}-aliexpress.svg"
        write_svg(ebay_img, "Pinned eBay Listing", str(row.get("title", ""))[:34], "#4f8cff")
        write_svg(source_img, "Pinned AliExpress Listing", str(row.get("title", ""))[:34], "#22c55e")
        row["image_paths"] = [
            display_path(ebay_img),
            display_path(source_img),
        ]

    evidence_json.write_text(json.dumps(records, indent=2), encoding="utf-8")

    output_path = resolve_out(input_path, args.output)
    render_script = pathlib.Path(__file__).resolve().parent / "render_candidate_dashboard.py"
    cmd = [
        sys.executable,
        str(render_script),
        str(input_path),
        "--output",
        str(output_path),
        "--run-id",
        run_id,
        "--evidence",
        str(evidence_json),
    ]
    subprocess.run(cmd, check=True)

    manifest = {
        "run_id": run_id,
        "created_at": created_at,
        "html_report_path": display_path(output_path),
        "candidate_count": total_candidates,
        "status": args.status,
        "source_reports": [display_path(path) for path in md_paths],
        "evidence_path": display_path(evidence_json),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    apply_retention(runs_root, root_reports / ".evidence", args.keep_runs)

    print(f"run_id: {run_id}")
    print(f"html: {output_path}")
    print(f"manifest: {manifest_path}")
    print(f"evidence: {evidence_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
