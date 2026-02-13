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
    avg_margin = statistics.mean([safe(c.margin_pct) for c in candidates if c.margin_pct is not None]) if candidates else 0.0
    avg_roi = statistics.mean([safe(c.roi_pct) for c in candidates if c.roi_pct is not None]) if candidates else 0.0
    avg_landed = statistics.mean([safe(c.landed_cost) for c in candidates if c.landed_cost is not None]) if candidates else 0.0
    avg_sell = statistics.mean([safe(c.sell_price) for c in candidates if c.sell_price is not None]) if candidates else 0.0
    greenlights = sum(1 for c in candidates if c.decision.upper() == "GREENLIGHT")

    total = len(candidates)
    cut1 = max(1, total // 3) if total else 0
    cut2 = max(cut1 + 1, (2 * total) // 3) if total > 1 else cut1

    def tier_for_rank(rank: int) -> str:
        if rank <= cut1:
            return "TIER 1"
        if rank <= cut2:
            return "TIER 2"
        return "TIER 3"

    def badge_class_for_tier(tier: str) -> str:
        if tier == "TIER 1":
            return "badge-green"
        if tier == "TIER 2":
            return "badge-blue"
        return "badge-yellow"

    def item_tier_class(tier: str) -> str:
        if tier == "TIER 1":
            return "tier1"
        if tier == "TIER 2":
            return "tier2"
        return "tier3"

    category_buckets: dict[str, list[Candidate]] = {}
    for item in candidates:
        category_buckets.setdefault(item.category or "Uncategorized", []).append(item)

    category_rows = []
    for category, items in sorted(category_buckets.items(), key=lambda kv: len(kv[1]), reverse=True):
        cat_margin = statistics.mean([safe(c.margin_pct) for c in items if c.margin_pct is not None]) if items else 0.0
        cat_roi = statistics.mean([safe(c.roi_pct) for c in items if c.roi_pct is not None]) if items else 0.0
        category_rows.append(
            f"""
<tr>
  <td>{html.escape(category)}</td>
  <td class=\"center\">{len(items)}</td>
  <td class=\"right\">{cat_margin:.1f}%</td>
  <td class=\"right\">{cat_roi:.1f}%</td>
</tr>
"""
        )

    ranking_rows = []
    link_rows = []
    item_cards = []
    for item in candidates:
        tier = tier_for_rank(item.rank)
        score_width = max(5.0, min(100.0, item.score))
        decision_class = "badge-green" if item.decision.upper() == "GREENLIGHT" else "badge-yellow"

        ranking_rows.append(
            f"""
<tr class=\"candidate-row\" data-report=\"{html.escape(item.source_report_path, quote=True)}\">
  <td>{item.rank}</td>
  <td>{html.escape(item.title)}</td>
  <td>{html.escape(item.source_report_label)}</td>
  <td>{html.escape(item.category or '-')}</td>
  <td><span class=\"badge {badge_class_for_tier(tier)}\">{tier}</span></td>
  <td>{item.score:.1f} <span class=\"score-bar\"><span class=\"score-fill\" style=\"width:{score_width:.1f}%\"></span></span></td>
  <td class=\"right\">{format_money(item.landed_cost)}</td>
  <td class=\"right\">{format_money(item.sell_price)}</td>
  <td class=\"right\">{format_pct(item.margin_pct)}</td>
  <td class=\"right\">{format_pct(item.roi_pct)}</td>
  <td><span class=\"badge {decision_class}\">{html.escape(item.decision or '-')}</span></td>
</tr>
"""
        )

        ebay_chips = "".join(
            f'<a class="link-chip" href="{html.escape(url)}" target="_blank" rel="noopener noreferrer">eBay Comp {idx}</a>'
            for idx, url in enumerate(item.ebay_links, start=1)
        )
        source_chips = "".join(
            f'<a class="link-chip source" href="{html.escape(url)}" target="_blank" rel="noopener noreferrer">Source {idx}</a>'
            for idx, url in enumerate(item.source_links, start=1)
        )
        terms = ", ".join(html.escape(term) for term in item.primary_terms) or "-"
        item_cards.append(
            f"""
<div class=\"item-card candidate-row\" data-report=\"{html.escape(item.source_report_path, quote=True)}\">
  <div class=\"item-header\">
    <div class=\"item-name\">#{item.rank} {html.escape(item.title)}</div>
    <span class=\"item-tier {item_tier_class(tier)}\">{tier}</span>
  </div>
  <div class=\"meta\">{html.escape(item.candidate_id or '-')} | {html.escape(item.category or '-')} | {html.escape(item.source_report_label)}</div>
  <div class=\"item-stats\">
    <div class=\"item-stat\"><div class=\"s-label\">Sell</div><div class=\"s-value\">{format_money(item.sell_price)}</div></div>
    <div class=\"item-stat\"><div class=\"s-label\">Landed</div><div class=\"s-value\">{format_money(item.landed_cost)}</div></div>
    <div class=\"item-stat\"><div class=\"s-label\">Margin</div><div class=\"s-value\">{format_pct(item.margin_pct)}</div></div>
    <div class=\"item-stat\"><div class=\"s-label\">ROI</div><div class=\"s-value\">{format_pct(item.roi_pct)}</div></div>
  </div>
  <div class=\"terms\"><strong>Primary terms:</strong> {terms}</div>
  <div class=\"links-row\">{ebay_chips}{source_chips}</div>
</div>
"""
        )

        ebay = "<br>".join(
            f'<a href="{html.escape(url)}" target="_blank" rel="noopener noreferrer">{html.escape(url)}</a>'
            for url in item.ebay_links
        )
        source = "<br>".join(
            f'<a href="{html.escape(url)}" target="_blank" rel="noopener noreferrer">{html.escape(url)}</a>'
            for url in item.source_links
        )
        link_rows.append(
            f"""
<tr class=\"candidate-row\" data-report=\"{html.escape(item.source_report_path, quote=True)}\">
  <td>{html.escape(item.candidate_id or '-')}</td>
  <td>{html.escape(item.title)}</td>
  <td>{html.escape(item.source_report_label)}</td>
  <td>{ebay}</td>
  <td>{source}</td>
</tr>
"""
        )

    report_rows = []
    for source in report.source_reports:
        report_rows.append(
            "<tr data-report-row=\"1\" data-report=\"{path}\"><td>{label}</td><td class=\"center\">{count}</td><td>{modified}</td><td><a class=\"link-chip\" href=\"{href}\" target=\"_blank\" rel=\"noopener noreferrer\">Open</a><button class=\"action-btn\" data-action=\"toggle-hide\" data-report=\"{path}\">Hide</button><button class=\"action-btn danger\" data-action=\"delete-report\" data-report=\"{path}\" data-label=\"{label}\">Delete</button></td></tr>".format(
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
<html lang=\"en\">
<head>
<meta charset=\"UTF-8\">
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
<title>{html.escape(report.title)} - Dashboard</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
:root {{
  --bg:#0a1014;
  --card:#131c22;
  --card2:#1b2730;
  --accent:#25b7d3;
  --accent2:#57d67f;
  --warn:#f4b63f;
  --danger:#ff5b5b;
  --text:#e8f1f5;
  --text2:#9eb1bc;
  --border:#243643;
}}
body{{background:radial-gradient(circle at top,#12202a 0%,#0a1014 45%,#070b0f 100%);color:var(--text);font-family:'Segoe UI',Roboto,Arial,sans-serif;line-height:1.45}}
.container{{max-width:1400px;margin:0 auto;padding:20px}}
header{{text-align:center;padding:26px 0 18px;border-bottom:1px solid var(--border);margin-bottom:20px}}
header h1{{font-size:28px;font-weight:800;background:linear-gradient(135deg,#25b7d3,#57d67f);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
header p{{color:var(--text2);margin-top:6px;font-size:14px}}
.badge{{display:inline-block;padding:3px 10px;border-radius:12px;font-size:11px;font-weight:700;margin:0 3px}}
.badge-green{{background:#57d67f22;color:#57d67f;border:1px solid #57d67f55}}
.badge-blue{{background:#25b7d322;color:#25b7d3;border:1px solid #25b7d355}}
.badge-yellow{{background:#f4b63f22;color:#f4b63f;border:1px solid #f4b63f55}}
.tabs{{display:flex;gap:4px;margin:18px 0 16px;overflow-x:auto;padding-bottom:4px;border-bottom:1px solid var(--border)}}
.tab{{padding:10px 18px;background:transparent;color:var(--text2);border:none;cursor:pointer;font-size:13px;font-weight:600;border-bottom:2px solid transparent;white-space:nowrap;transition:.2s}}
.tab:hover{{color:var(--text)}}
.tab.active{{color:var(--accent);border-bottom-color:var(--accent)}}
.panel{{display:none}}
.panel.active{{display:block}}
.kpi-row{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:14px;margin-bottom:16px}}
.kpi{{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:16px;text-align:center}}
.kpi .label{{font-size:11px;color:var(--text2);text-transform:uppercase;letter-spacing:.5px}}
.kpi .value{{font-size:25px;font-weight:800;margin-top:3px}}
.kpi .sub{{font-size:12px;color:var(--text2);margin-top:3px}}
.card{{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:18px;margin-bottom:14px}}
.card h3{{font-size:16px;font-weight:700;margin-bottom:10px}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{text-align:left;padding:10px 12px;background:var(--card2);color:var(--text2);font-weight:700;font-size:11px;text-transform:uppercase;letter-spacing:.5px;border-bottom:1px solid var(--border)}}
td{{padding:10px 12px;border-bottom:1px solid var(--border);vertical-align:top}}
tr:hover td{{background:var(--card2)}}
.right{{text-align:right}}
.center{{text-align:center}}
.score-bar{{height:6px;background:var(--card2);border-radius:3px;overflow:hidden;width:90px;display:inline-block;vertical-align:middle;margin-left:6px}}
.score-fill{{height:100%;border-radius:3px;background:linear-gradient(90deg,#25b7d3,#57d67f)}}
.item-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:14px}}
.item-card{{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:16px;transition:.2s}}
.item-card:hover{{border-color:var(--accent);transform:translateY(-2px)}}
.item-header{{display:flex;justify-content:space-between;gap:8px;align-items:flex-start;margin-bottom:8px}}
.item-name{{font-weight:700;font-size:14px;flex:1}}
.meta{{font-size:12px;color:var(--text2);margin-bottom:8px}}
.item-tier{{font-size:11px;font-weight:800;padding:2px 8px;border-radius:8px;white-space:nowrap}}
.tier1{{background:#57d67f22;color:#57d67f}}
.tier2{{background:#25b7d322;color:#25b7d3}}
.tier3{{background:#f4b63f22;color:#f4b63f}}
.item-stats{{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:8px}}
.item-stat{{padding:6px 10px;background:var(--card2);border-radius:8px}}
.item-stat .s-label{{font-size:10px;color:var(--text2);text-transform:uppercase}}
.item-stat .s-value{{font-size:15px;font-weight:700}}
.terms{{font-size:12px;color:var(--text2);margin-bottom:8px}}
.links-row{{display:flex;gap:6px;flex-wrap:wrap}}
.link-chip{{text-decoration:none;background:#25b7d322;border:1px solid #25b7d355;color:#a8e9f6;padding:4px 8px;border-radius:12px;font-size:11px;font-weight:700;cursor:pointer}}
.link-chip:hover{{background:#25b7d344}}
.link-chip.source{{background:#57d67f22;border-color:#57d67f55;color:#c6f6d9}}
.action-btn{{background:#25b7d322;border:1px solid #25b7d355;color:#a8e9f6;padding:4px 8px;border-radius:12px;font-size:11px;font-weight:700;cursor:pointer;margin-left:6px}}
.action-btn:hover{{background:#25b7d344}}
.action-btn.danger{{background:#ff5b5b22;border-color:#ff5b5b55;color:#ffc7c7}}
.action-btn:disabled{{opacity:.55;cursor:not-allowed}}
.status-note{{font-size:12px;color:var(--text2);margin-top:8px}}
.is-hidden-by-report{{display:none !important}}
ul{{margin-left:20px}}
li{{margin:6px 0}}
a{{color:#89e7ff}}
a:hover{{color:#c7f4ff}}
@media(max-width:768px){{
  .item-grid{{grid-template-columns:1fr}}
  .tabs{{flex-wrap:wrap}}
}}
</style>
</head>
<body>
<div class=\"container\">
  <header>
    <h1>{html.escape(report.title or 'eBay Candidate Dashboard')}</h1>
    <p>{html.escape(report.date)} | {html.escape(report.market)} | {html.escape(report.theme)}</p>
    <div style=\"margin-top:10px\">
      <span class=\"badge badge-green\">{greenlights}/{len(candidates)} GREENLIGHT</span>
      <span class=\"badge badge-blue\">Avg Margin {avg_margin:.1f}%</span>
      <span class=\"badge badge-blue\">Avg ROI {avg_roi:.1f}%</span>
    </div>
  </header>

  <div class=\"kpi-row\">
    <div class=\"kpi\"><div class=\"label\">Candidates</div><div class=\"value\">{len(candidates)}</div><div class=\"sub\">All loaded reports</div></div>
    <div class=\"kpi\"><div class=\"label\">Report Files</div><div class=\"value\">{len(report.source_reports)}</div><div class=\"sub\">Markdown files</div></div>
    <div class=\"kpi\"><div class=\"label\">Greenlights</div><div class=\"value\" style=\"color:var(--accent2)\">{greenlights}</div><div class=\"sub\">Decision pass count</div></div>
    <div class=\"kpi\"><div class=\"label\">Avg Landed</div><div class=\"value\">{format_money(avg_landed)}</div><div class=\"sub\">Per unit</div></div>
    <div class=\"kpi\"><div class=\"label\">Avg Sell</div><div class=\"value\">{format_money(avg_sell)}</div><div class=\"sub\">Per unit</div></div>
    <div class=\"kpi\"><div class=\"label\">Avg Margin</div><div class=\"value\" style=\"color:var(--accent2)\">{avg_margin:.1f}%</div><div class=\"sub\">Across all items</div></div>
  </div>

  <div class=\"tabs\">
    <button class=\"tab active\" data-tab=\"overview\">Overview</button>
    <button class=\"tab\" data-tab=\"items\">Candidates</button>
    <button class=\"tab\" data-tab=\"links\">Links</button>
    <button class=\"tab\" data-tab=\"reports\">Reports</button>
    <button class=\"tab\" data-tab=\"team\">Agent Team</button>
  </div>

  <div class=\"panel active\" id=\"overview\">
    <div class=\"card\">
      <h3>Ranked Candidate Table</h3>
      <table>
        <thead><tr><th>Rank</th><th>Candidate</th><th>Report</th><th>Category</th><th>Tier</th><th>Score</th><th class=\"right\">Landed</th><th class=\"right\">Sell</th><th class=\"right\">Margin</th><th class=\"right\">ROI</th><th>Decision</th></tr></thead>
        <tbody>
          {''.join(ranking_rows)}
        </tbody>
      </table>
    </div>
    <div class=\"card\">
      <h3>Category Breakdown</h3>
      <table>
        <thead><tr><th>Category</th><th class=\"center\">Items</th><th class=\"right\">Avg Margin</th><th class=\"right\">Avg ROI</th></tr></thead>
        <tbody>
          {''.join(category_rows)}
        </tbody>
      </table>
    </div>
  </div>

  <div class=\"panel\" id=\"items\">
    <div class=\"item-grid\">
      {''.join(item_cards)}
    </div>
  </div>

  <div class=\"panel\" id=\"links\">
    <div class=\"card\">
      <h3>Clickable Comp + Source Links</h3>
      <table>
        <thead><tr><th>ID</th><th>Candidate</th><th>Report</th><th>eBay Comp Links</th><th>Source Links</th></tr></thead>
        <tbody>
          {''.join(link_rows)}
        </tbody>
      </table>
    </div>
  </div>

  <div class=\"panel\" id=\"reports\">
    <div class=\"card\">
      <h3>Report Files</h3>
      <table>
        <thead><tr><th>Report</th><th class=\"center\">Candidates</th><th>Modified</th><th>Actions</th></tr></thead>
        <tbody>
          {''.join(report_rows)}
        </tbody>
      </table>
      <p class=\"status-note\">Hide only affects this dashboard view (stored in local storage). Delete removes source files when this page is served via <code>scripts/report_dashboard_server.py</code>.</p>
      <p class=\"status-note\" id=\"status\"></p>
    </div>
  </div>

  <div class=\"panel\" id=\"team\">
    <div class=\"card\">
      <h3>Agent Team Used</h3>
      <ul>{team}</ul>
    </div>
    <div class=\"card\">
      <h3>Portfolio Summary</h3>
      <ul>{summary}</ul>
    </div>
    <div class=\"card\">
      <h3>Compliance Scope</h3>
      <p style=\"color:var(--text2)\">{html.escape(report.compliance or '-')}</p>
    </div>
  </div>
</div>

<script>
document.querySelectorAll('.tab').forEach(tab => {{
  tab.addEventListener('click', () => {{
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    tab.classList.add('active');
    const panel = document.getElementById(tab.dataset.tab);
    if (panel) panel.classList.add('active');
  }});
}});

const hiddenKey = 'abx-hidden-reports-v1';
const hiddenReports = new Set(JSON.parse(localStorage.getItem(hiddenKey) || '[]'));
const status = document.getElementById('status');

function saveHidden() {{
  localStorage.setItem(hiddenKey, JSON.stringify(Array.from(hiddenReports)));
}}

function setStatus(message, isError = false) {{
  if (!status) return;
  status.textContent = message;
  status.style.color = isError ? 'var(--danger)' : 'var(--text2)';
}}

function applyHidden() {{
  document.querySelectorAll('[data-report]').forEach(node => {{
    if (node.hasAttribute('data-report-row')) return;
    const key = node.dataset.report || '';
    node.classList.toggle('is-hidden-by-report', hiddenReports.has(key));
  }});

  document.querySelectorAll('button[data-action="toggle-hide"]').forEach(btn => {{
    const key = btn.dataset.report || '';
    btn.textContent = hiddenReports.has(key) ? 'Unhide' : 'Hide';
  }});
}}

function removeNodes(reportKey) {{
  document.querySelectorAll('[data-report]').forEach(node => {{
    if ((node.dataset.report || '') === reportKey) node.remove();
  }});
}}

document.addEventListener('click', async event => {{
  const btn = event.target.closest('button[data-action]');
  if (!btn) return;

  const action = btn.dataset.action;
  const reportKey = btn.dataset.report || '';
  const label = btn.dataset.label || reportKey;
  if (!reportKey) return;

  if (action === 'toggle-hide') {{
    if (hiddenReports.has(reportKey)) hiddenReports.delete(reportKey);
    else hiddenReports.add(reportKey);
    saveHidden();
    applyHidden();
    setStatus('Toggled visibility for ' + label);
    return;
  }}

  if (action === 'delete-report') {{
    if (!window.confirm('Delete ' + label + ' from disk? This cannot be undone.')) return;
    btn.disabled = true;
    try {{
      const res = await fetch('/api/reports?path=' + encodeURIComponent(reportKey), {{ method: 'DELETE' }});
      if (!res.ok) throw new Error();
      hiddenReports.delete(reportKey);
      saveHidden();
      removeNodes(reportKey);
      setStatus('Deleted ' + label);
    }} catch {{
      setStatus('Delete failed. Serve with scripts/report_dashboard_server.py and open via localhost.', true);
    }} finally {{
      btn.disabled = false;
    }}
  }}
}});

applyHidden();
</script>
</body>
</html>"""

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

