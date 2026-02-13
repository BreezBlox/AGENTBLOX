#!/usr/bin/env python3
"""
Render eBay candidate-card markdown reports into an HTML dashboard.

Usage:
  python scripts/render_candidate_dashboard.py reports/my-report.md
  python scripts/render_candidate_dashboard.py reports --output reports/dashboard.html
"""

from __future__ import annotations

import argparse
import dataclasses
import html
import pathlib
import re
import statistics
from datetime import datetime


@dataclasses.dataclass
class Candidate:
    title: str = ""
    candidate_id: str = ""
    category: str = ""
    primary_terms: list[str] = dataclasses.field(default_factory=list)
    ebay_links: list[str] = dataclasses.field(default_factory=list)
    source_links: list[str] = dataclasses.field(default_factory=list)
    sell_price: float | None = None
    landed_cost: float | None = None
    margin_pct: float | None = None
    roi_pct: float | None = None
    decision: str = ""
    source_report_path: str = ""
    source_report_label: str = ""
    rank: int = 0
    score: float = 0.0


@dataclasses.dataclass
class SourceReport:
    path: str
    label: str
    candidate_count: int
    modified_at: str


@dataclasses.dataclass
class ParsedReport:
    title: str = ""
    date: str = ""
    market: str = ""
    theme: str = ""
    compliance: str = ""
    candidates: list[Candidate] = dataclasses.field(default_factory=list)
    agent_team: list[str] = dataclasses.field(default_factory=list)
    summary_lines: list[str] = dataclasses.field(default_factory=list)
    source_reports: list[SourceReport] = dataclasses.field(default_factory=list)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render report markdown to dashboard HTML.")
    parser.add_argument("input_path", help="Markdown report file or directory of markdown reports")
    parser.add_argument("--output", help="Output HTML path")
    return parser.parse_args()


def parse_money(line: str, key: str) -> float | None:
    match = re.search(rf"{re.escape(key)} ~\$(\d+(?:\.\d+)?)", line, flags=re.IGNORECASE)
    return float(match.group(1)) if match else None


def parse_percent(line: str, key: str) -> float | None:
    match = re.search(rf"{re.escape(key)} ~(\d+(?:\.\d+)?)%", line, flags=re.IGNORECASE)
    return float(match.group(1)) if match else None


def parse_float(line: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)", line)
    return float(match.group(1)) if match else None


def resolve_display_path(path: pathlib.Path) -> str:
    try:
        return path.resolve().relative_to(pathlib.Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def resolve_input_paths(input_path: pathlib.Path) -> list[pathlib.Path]:
    if input_path.is_file():
        if input_path.suffix.lower() != ".md":
            raise ValueError(f"input file must be .md: {input_path}")
        return [input_path.resolve()]
    if input_path.is_dir():
        paths = sorted(path.resolve() for path in input_path.glob("*.md") if path.is_file())
        if not paths:
            raise ValueError(f"no markdown reports in: {input_path}")
        return paths
    raise ValueError(f"input path not found: {input_path}")


def parse_report(text: str, source_path: str, source_label: str) -> ParsedReport:
    report = ParsedReport()
    current: Candidate | None = None
    link_block: str | None = None
    in_agent_team = False
    in_summary = False

    for raw in text.splitlines():
        line = raw.strip()

        if line.startswith("# "):
            report.title = line[2:].strip()
            continue
        if line.startswith("Date:"):
            report.date = line.split(":", 1)[1].strip()
            continue
        if line.startswith("Market:"):
            report.market = line.split(":", 1)[1].strip()
            continue
        if line.startswith("Theme:"):
            report.theme = line.split(":", 1)[1].strip()
            continue
        if line.startswith("Scope:") and not report.theme:
            report.theme = line.split(":", 1)[1].strip()
            continue
        if line.startswith("Compliance:"):
            report.compliance = line.split(":", 1)[1].strip()
            continue

        if line.startswith("## Agent Team Used"):
            in_agent_team = True
            in_summary = False
            continue
        if line.startswith("## Portfolio Summary"):
            in_summary = True
            in_agent_team = False
            continue
        if line.startswith("## Candidate Card - "):
            in_agent_team = False
            in_summary = False
            if current:
                report.candidates.append(current)
            current = Candidate(
                title=line.replace("## Candidate Card - ", "", 1).strip(),
                source_report_path=source_path,
                source_report_label=source_label,
            )
            link_block = None
            continue

        if in_agent_team and line.startswith("- "):
            report.agent_team.append(line[2:].strip())
            continue
        if in_summary and line.startswith("- "):
            report.summary_lines.append(line[2:].strip())
            continue

        if not current:
            continue

        if line.startswith("- Candidate ID:"):
            current.candidate_id = line.split(":", 1)[1].strip()
            continue
        if line.startswith("- Category:"):
            current.category = line.split(":", 1)[1].strip()
            continue
        if line.startswith("- Primary search terms:") or line.startswith("- Primary search terms used:"):
            current.primary_terms = re.findall(r"`([^`]+)`", line)
            continue
        if line.startswith("- eBay comp links"):
            link_block = "ebay"
            continue
        if line.startswith("- Source links"):
            link_block = "source"
            continue
        if line.startswith("- Gate D quick economics:"):
            current.sell_price = parse_money(line, "sell")
            current.landed_cost = parse_money(line, "landed")
            current.margin_pct = parse_percent(line, "margin")
            current.roi_pct = parse_percent(line, "ROI")
            continue
        if line.startswith("- Expected sell price:"):
            current.sell_price = parse_float(line)
            continue
        if line.startswith("- Landed cost"):
            current.landed_cost = parse_float(line)
            continue
        if line.startswith("- Estimated margin:"):
            current.margin_pct = parse_float(line)
            continue
        if line.startswith("- Notes") and current.roi_pct is None:
            roi = re.search(r"ROI\s+(\d+(?:\.\d+)?)%", line, flags=re.IGNORECASE)
            if roi:
                current.roi_pct = float(roi.group(1))
            continue
        if line.startswith("- Decision:"):
            current.decision = line.split(":", 1)[1].strip()
            continue
        if line.startswith("- http") and link_block:
            url = line[2:].strip()
            if link_block == "ebay":
                current.ebay_links.append(url)
            else:
                current.source_links.append(url)
            continue
        if line.startswith("- "):
            link_block = None

    if current:
        report.candidates.append(current)
    return report


def safe(value: float | None, default: float = 0.0) -> float:
    return value if value is not None else default


def decorate_candidates(candidates: list[Candidate]) -> None:
    for item in candidates:
        margin = safe(item.margin_pct)
        roi = min(safe(item.roi_pct), 200.0)
        item.score = (margin * 0.6) + ((roi / 200.0) * 40.0)
    for idx, item in enumerate(sorted(candidates, key=lambda c: c.score, reverse=True), start=1):
        item.rank = idx


def combine_reports(parsed_reports: list[ParsedReport], source_reports: list[SourceReport]) -> ParsedReport:
    if len(parsed_reports) == 1:
        parsed_reports[0].source_reports = source_reports
        return parsed_reports[0]

    combined = ParsedReport(
        title=f"eBay Candidate Dashboard ({len(parsed_reports)} reports)",
        theme=f"Aggregated across {len(parsed_reports)} report files",
        compliance="Mixed by source report. Review each report before launch.",
        source_reports=source_reports,
    )
    dates = [report.date for report in parsed_reports if report.date]
    combined.date = max(dates) if dates else "-"
    markets = sorted({report.market for report in parsed_reports if report.market})
    combined.market = ", ".join(markets) if markets else "-"

    for report in parsed_reports:
        combined.candidates.extend(report.candidates)
        for member in report.agent_team:
            if member not in combined.agent_team:
                combined.agent_team.append(member)

    combined.summary_lines = [
        f"Report files loaded: {len(source_reports)}",
        f"Total candidates loaded: {len(combined.candidates)}",
        "Use the Reports tab to hide rows locally or delete files when served with report_dashboard_server.py",
    ]
    return combined


def format_money(value: float | None) -> str:
    return "-" if value is None else f"${value:,.2f}"


def format_pct(value: float | None) -> str:
    return "-" if value is None else f"{value:.1f}%"


def build_html(report: ParsedReport) -> str:
    candidates = sorted(report.candidates, key=lambda c: c.rank)
    avg_margin = statistics.mean([safe(c.margin_pct) for c in candidates]) if candidates else 0.0
    avg_roi = statistics.mean([safe(c.roi_pct) for c in candidates]) if candidates else 0.0
    greenlights = sum(1 for c in candidates if c.decision.upper() == "GREENLIGHT")

    candidate_rows = []
    link_rows = []
    for item in candidates:
        candidate_rows.append(
            "<tr class=\"candidate-row\" data-report=\"{path}\"><td>{rank}</td><td>{title}</td><td>{report}</td><td>{category}</td><td>{sell}</td><td>{landed}</td><td>{margin}</td><td>{roi}</td><td>{decision}</td></tr>".format(
                path=html.escape(item.source_report_path, quote=True),
                rank=item.rank,
                title=html.escape(item.title),
                report=html.escape(item.source_report_label),
                category=html.escape(item.category or "-"),
                sell=format_money(item.sell_price),
                landed=format_money(item.landed_cost),
                margin=format_pct(item.margin_pct),
                roi=format_pct(item.roi_pct),
                decision=html.escape(item.decision or "-"),
            )
        )
        ebay = "<br>".join(
            f"<a href=\"{html.escape(url)}\" target=\"_blank\" rel=\"noopener noreferrer\">{html.escape(url)}</a>"
            for url in item.ebay_links
        )
        source = "<br>".join(
            f"<a href=\"{html.escape(url)}\" target=\"_blank\" rel=\"noopener noreferrer\">{html.escape(url)}</a>"
            for url in item.source_links
        )
        link_rows.append(
            "<tr class=\"candidate-row\" data-report=\"{path}\"><td>{id}</td><td>{title}</td><td>{report}</td><td>{ebay}</td><td>{source}</td></tr>".format(
                path=html.escape(item.source_report_path, quote=True),
                id=html.escape(item.candidate_id or "-"),
                title=html.escape(item.title),
                report=html.escape(item.source_report_label),
                ebay=ebay,
                source=source,
            )
        )

    report_rows = []
    for source in report.source_reports:
        report_rows.append(
            "<tr data-report=\"{path}\"><td>{label}</td><td>{count}</td><td>{modified}</td><td><a class=\"chip\" href=\"{href}\" target=\"_blank\" rel=\"noopener noreferrer\">Open</a><button class=\"chip\" data-action=\"toggle-hide\" data-report=\"{path}\">Hide</button><button class=\"chip danger\" data-action=\"delete-report\" data-report=\"{path}\" data-label=\"{label}\">Delete</button></td></tr>".format(
                path=html.escape(source.path, quote=True),
                label=html.escape(source.label),
                count=source.candidate_count,
                modified=html.escape(source.modified_at),
                href=html.escape(source.path),
            )
        )

    team = "".join(f"<li>{html.escape(line)}</li>" for line in report.agent_team) or "<li>No agent-team block found.</li>"
    summary = "".join(f"<li>{html.escape(line)}</li>" for line in report.summary_lines) or "<li>No summary block found.</li>"

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>{html.escape(report.title)} - Dashboard</title>
<style>body{{margin:0;font-family:Segoe UI,Arial,sans-serif;background:#0b1218;color:#e9f3f9}}.wrap{{max-width:1400px;margin:0 auto;padding:20px}}.card{{background:#111b22;border:1px solid #223542;border-radius:10px;padding:14px;margin-bottom:14px}}table{{width:100%;border-collapse:collapse}}th,td{{padding:8px;border-bottom:1px solid #223542;vertical-align:top}}th{{text-align:left;color:#9eb3bf;font-size:12px;text-transform:uppercase}}a{{color:#84dcff}}.muted{{color:#9eb3bf}}.chip{{background:#25b7d322;border:1px solid #25b7d355;color:#c6eff9;padding:4px 8px;border-radius:999px;font-size:11px;cursor:pointer;margin-right:6px;text-decoration:none}}.chip.danger{{background:#ff5b5b22;border-color:#ff5b5b55;color:#ffd2d2}}.is-hidden-by-report{{display:none !important}}</style></head>
<body><div class="wrap">
<h1>{html.escape(report.title or "eBay Candidate Dashboard")}</h1>
<p class="muted">{html.escape(report.date)} | {html.escape(report.market)} | {html.escape(report.theme)}</p>
<div class="card"><strong>Candidates:</strong> {len(candidates)} | <strong>Reports:</strong> {len(report.source_reports)} | <strong>Greenlights:</strong> {greenlights} | <strong>Avg Margin:</strong> {avg_margin:.1f}% | <strong>Avg ROI:</strong> {avg_roi:.1f}%</div>

<div class="card"><h3>All Candidates</h3><table><thead><tr><th>Rank</th><th>Candidate</th><th>Report</th><th>Category</th><th>Sell</th><th>Landed</th><th>Margin</th><th>ROI</th><th>Decision</th></tr></thead><tbody>{''.join(candidate_rows)}</tbody></table></div>
<div class="card"><h3>Links</h3><table><thead><tr><th>ID</th><th>Candidate</th><th>Report</th><th>eBay</th><th>Source</th></tr></thead><tbody>{''.join(link_rows)}</tbody></table></div>
<div class="card"><h3>Reports</h3><table><thead><tr><th>File</th><th>Candidates</th><th>Modified</th><th>Actions</th></tr></thead><tbody>{''.join(report_rows)}</tbody></table><p class="muted" id="status">Hide persists in local storage. Delete uses /api/reports when served with scripts/report_dashboard_server.py.</p></div>
<div class="card"><h3>Agent Team</h3><ul>{team}</ul></div>
<div class="card"><h3>Summary</h3><ul>{summary}</ul><p class="muted"><strong>Compliance:</strong> {html.escape(report.compliance or "-")}</p></div>
</div>
<script>
const hiddenKey='abx-hidden-reports-v1';
const hiddenReports=new Set(JSON.parse(localStorage.getItem(hiddenKey)||'[]'));
const status=document.getElementById('status');
function saveHidden(){{localStorage.setItem(hiddenKey,JSON.stringify(Array.from(hiddenReports)));}}
function applyHidden(){{document.querySelectorAll('[data-report]').forEach(node=>{{const key=node.dataset.report||'';node.classList.toggle('is-hidden-by-report',hiddenReports.has(key));}});document.querySelectorAll('button[data-action="toggle-hide"]').forEach(btn=>{{const key=btn.dataset.report||'';btn.textContent=hiddenReports.has(key)?'Unhide':'Hide';}});}}
function removeNodes(reportKey){{document.querySelectorAll('[data-report]').forEach(node=>{{if((node.dataset.report||'')===reportKey)node.remove();}});}}
document.addEventListener('click',async(event)=>{{const btn=event.target.closest('button[data-action]');if(!btn)return;const action=btn.dataset.action;const reportKey=btn.dataset.report||'';const label=btn.dataset.label||reportKey;if(!reportKey)return;if(action==='toggle-hide'){{if(hiddenReports.has(reportKey))hiddenReports.delete(reportKey);else hiddenReports.add(reportKey);saveHidden();applyHidden();status.textContent=`Toggled visibility for ${{label}}`;return;}}if(action==='delete-report'){{if(!confirm(`Delete ${{label}} from disk?`))return;btn.disabled=true;try{{const res=await fetch(`/api/reports?path=${{encodeURIComponent(reportKey)}}`,{{method:'DELETE'}});if(!res.ok)throw new Error();hiddenReports.delete(reportKey);saveHidden();removeNodes(reportKey);status.textContent=`Deleted ${{label}}`;}}catch{{status.textContent='Delete failed. Serve with scripts/report_dashboard_server.py and open via localhost.';}}finally{{btn.disabled=false;}}}}}});
applyHidden();
</script></body></html>"""


def main() -> int:
    args = parse_args()
    input_path = pathlib.Path(args.input_path)

    try:
        markdown_paths = resolve_input_paths(input_path)
    except ValueError as exc:
        print(str(exc))
        return 1

    output_path = pathlib.Path(args.output) if args.output else (
        input_path.with_suffix(".html") if input_path.is_file() else input_path / "dashboard.html"
    )
    output_path = output_path.resolve()

    parsed_reports: list[ParsedReport] = []
    source_reports: list[SourceReport] = []
    for md_path in markdown_paths:
        source_path = resolve_display_path(md_path)
        source_label = md_path.name
        parsed = parse_report(md_path.read_text(encoding="utf-8"), source_path, source_label)
        parsed_reports.append(parsed)
        source_reports.append(
            SourceReport(
                path=source_path,
                label=source_label,
                candidate_count=len(parsed.candidates),
                modified_at=datetime.fromtimestamp(md_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
            )
        )

    report = combine_reports(parsed_reports, source_reports)
    decorate_candidates(report.candidates)
    output_path.write_text(build_html(report), encoding="utf-8")
    print(f"wrote dashboard: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
