#!/usr/bin/env python3
"""Render candidate markdown into HTML command-center dashboard (v2 mirror baseline)."""
from __future__ import annotations

import argparse
import dataclasses
import html
import json
import os
import pathlib
import re
import statistics
from datetime import datetime

URL_RE = re.compile(r"https?://[^\s)>]+")
CARD_RE = re.compile(r"^##\s+Candidate\s+Card\s*[-\u2014]\s*(.+)$", re.I)
MIRROR_TEMPLATE = pathlib.Path("C:/Users/robku/ebay.search.feb11/ebay-arbitrage-v2-command-center.html")

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
    tier: str = ""
    pinned_ebay_listing: str = ""
    pinned_aliexpress_listing: str = ""
    match_score: float | None = None
    match_label: str = ""
    accepted_differences: str = ""
    image_paths: list[str] = dataclasses.field(default_factory=list)

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
    p = argparse.ArgumentParser(description="Render report markdown to mirrored command-center HTML")
    p.add_argument("input_path", help="Markdown report file or directory")
    p.add_argument("--output", help="Output HTML path")
    p.add_argument("--run-id", help="Run id to locate reports/.evidence/<run-id>/evidence.json")
    p.add_argument("--evidence", help="Explicit evidence JSON path")
    p.add_argument("--mirror-template", default=str(MIRROR_TEMPLATE), help="Mirror reference path")
    return p.parse_args()


def display_path(path: pathlib.Path) -> str:
    try:
        return path.resolve().relative_to(pathlib.Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def resolve_inputs(input_path: pathlib.Path) -> list[pathlib.Path]:
    if input_path.is_file():
        if input_path.suffix.lower() != ".md":
            raise ValueError(f"input file must be .md: {input_path}")
        return [input_path.resolve()]
    if input_path.is_dir():
        paths = sorted(p.resolve() for p in input_path.glob("*.md") if p.is_file())
        if not paths:
            raise ValueError(f"no markdown reports in: {input_path}")
        return paths
    raise ValueError(f"input path not found: {input_path}")


def parse_float(text: str) -> float | None:
    m = re.search(r"(\d+(?:\.\d+)?)", text)
    return float(m.group(1)) if m else None


def parse_money(line: str, key: str) -> float | None:
    m = re.search(rf"{re.escape(key)}\s*~\s*\$(\d+(?:\.\d+)?)", line, re.I)
    return float(m.group(1)) if m else None


def parse_pct(line: str, key: str) -> float | None:
    m = re.search(rf"{re.escape(key)}\s*~\s*(\d+(?:\.\d+)?)%", line, re.I)
    return float(m.group(1)) if m else None


def urls(line: str) -> list[str]:
    return [u.strip().strip("<>[](),.;") for u in URL_RE.findall(line)]


def terms(line: str) -> list[str]:
    found = [v.strip() for v in re.findall(r"`([^`]+)`", line)]
    if found:
        return found
    if ":" not in line:
        return []
    return [c.strip("` ") for c in line.split(":", 1)[1].split(",") if c.strip()]


def parse_report(text: str, src_path: str, src_label: str) -> ParsedReport:
    rep = ParsedReport()
    cur: Candidate | None = None
    link_block: str | None = None
    in_team = False
    in_sum = False
    for raw in text.splitlines():
        line = raw.strip()
        m_card = CARD_RE.match(line)
        if m_card:
            in_team = False
            in_sum = False
            if cur:
                rep.candidates.append(cur)
            cur = Candidate(title=m_card.group(1).strip(), source_report_path=src_path, source_report_label=src_label)
            link_block = None
            continue
        if line.startswith("# ") and not rep.title:
            rep.title = line[2:].strip(); continue
        if line.startswith("Date:"):
            rep.date = line.split(":", 1)[1].strip(); continue
        if line.startswith("Market:"):
            rep.market = line.split(":", 1)[1].strip(); continue
        if line.startswith("Theme:"):
            rep.theme = line.split(":", 1)[1].strip(); continue
        if line.startswith("Scope:") and not rep.theme:
            rep.theme = line.split(":", 1)[1].strip(); continue
        if line.startswith("Compliance:"):
            rep.compliance = line.split(":", 1)[1].strip(); continue
        if line.startswith("## Agent Team"):
            in_team = True; in_sum = False; continue
        if line.startswith("## Portfolio Summary"):
            in_sum = True; in_team = False; continue
        if in_team and line.startswith("- "):
            rep.agent_team.append(line[2:].strip()); continue
        if in_sum and line.startswith("- "):
            rep.summary_lines.append(line[2:].strip()); continue
        if not cur:
            continue
        if line.startswith("- Candidate ID:"):
            cur.candidate_id = line.split(":", 1)[1].strip(); continue
        if line.startswith("- Category:"):
            cur.category = line.split(":", 1)[1].strip(); continue
        if line.startswith("- Primary search terms"):
            cur.primary_terms = terms(line); continue
        if line.lower().startswith("- ebay comp links"):
            link_block = "ebay"; continue
        if line.lower().startswith("- source links"):
            link_block = "source"; continue
        if line.startswith("- Gate D quick economics:"):
            cur.sell_price = parse_money(line, "sell")
            cur.landed_cost = parse_money(line, "landed")
            cur.margin_pct = parse_pct(line, "margin")
            cur.roi_pct = parse_pct(line, "ROI")
            continue
        if line.startswith("- Expected sell price"):
            cur.sell_price = parse_float(line); continue
        if line.startswith("- Landed cost"):
            cur.landed_cost = parse_float(line); continue
        if line.startswith("- Estimated margin"):
            cur.margin_pct = parse_float(line); continue
        if line.startswith("- Notes") and cur.roi_pct is None:
            m_roi = re.search(r"ROI\s*(\d+(?:\.\d+)?)%", line, re.I)
            if m_roi: cur.roi_pct = float(m_roi.group(1))
            continue
        if line.startswith("- Decision:"):
            cur.decision = line.split(":", 1)[1].strip(); continue
        if line.startswith("- Pinned eBay listing:"):
            us = urls(line); cur.pinned_ebay_listing = us[0] if us else ""; continue
        if line.startswith("- Pinned AliExpress listing:"):
            us = urls(line); cur.pinned_aliexpress_listing = us[0] if us else ""; continue
        if line.startswith("- Match confidence:"):
            cur.match_score = parse_float(line); continue
        if line.startswith("- Exact match status:"):
            cur.match_label = line.split(":", 1)[1].strip().upper(); continue
        if line.startswith("- Accepted differences:"):
            cur.accepted_differences = line.split(":", 1)[1].strip(); continue
        us = urls(line)
        if us and link_block in {"ebay", "source"}:
            for u in us:
                (cur.ebay_links if link_block == "ebay" else cur.source_links).append(u)
            continue
        if line.startswith("- "):
            link_block = None
    if cur:
        rep.candidates.append(cur)
    return rep

def safe(v: float | None, d: float = 0.0) -> float:
    return d if v is None else v


def money(v: float | None) -> str:
    return "-" if v is None else f"${v:,.2f}"


def pct(v: float | None) -> str:
    return "-" if v is None else f"{v:.1f}%"


def norm_key(v: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", v.lower())


def resolve_reports_root(md_paths: list[pathlib.Path]) -> pathlib.Path:
    for p in md_paths:
        if p.parent.name.lower() == "reports":
            return p.parent
    return md_paths[0].parent


def resolve_out(input_path: pathlib.Path, output: str | None) -> pathlib.Path:
    if output:
        return pathlib.Path(output).resolve()
    if input_path.is_file():
        return input_path.with_suffix(".html").resolve()
    return (input_path / "ebay-arbitrage-command-center.html").resolve()


def href(out_path: pathlib.Path, target: str) -> str:
    if not target:
        return ""
    if re.match(r"^https?://", target, re.I):
        return target
    p = pathlib.Path(target)
    if not p.is_absolute():
        p = (pathlib.Path.cwd() / p).resolve()
    try:
        rel = os.path.relpath(p, start=out_path.parent.resolve())
    except ValueError:
        rel = str(p)
    return rel.replace("\\", "/")


def load_evidence(path: pathlib.Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    rows = raw if isinstance(raw, list) else raw.get("records", [])
    result: dict[str, dict] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        cid = str(row.get("candidate_id", "")).strip()
        title = str(row.get("title", "")).strip()
        if cid:
            result["id:" + norm_key(cid)] = row
        if title:
            result["title:" + norm_key(title)] = row
    return result


def apply_evidence(cands: list[Candidate], evidence: dict[str, dict]) -> None:
    for c in cands:
        row = evidence.get("id:" + norm_key(c.candidate_id)) or evidence.get("title:" + norm_key(c.title))
        if not row:
            continue
        if row.get("ebay_listing_url"):
            c.pinned_ebay_listing = str(row.get("ebay_listing_url"))
        if row.get("aliexpress_listing_url"):
            c.pinned_aliexpress_listing = str(row.get("aliexpress_listing_url"))
        if row.get("match_score") is not None:
            c.match_score = float(row.get("match_score"))
        if row.get("match_label"):
            c.match_label = str(row.get("match_label")).upper()
        if row.get("accepted_differences"):
            c.accepted_differences = str(row.get("accepted_differences"))
        imgs = [str(i) for i in row.get("image_paths", []) if str(i).strip()]
        if imgs:
            c.image_paths = imgs


def decorate(cands: list[Candidate]) -> None:
    for c in cands:
        roi = min(safe(c.roi_pct), 200.0)
        c.score = safe(c.margin_pct) * 0.6 + (roi / 200.0) * 40.0
    ranked = sorted(cands, key=lambda v: v.score, reverse=True)
    total = len(ranked)
    cut1 = max(1, total // 3) if total else 0
    cut2 = max(cut1 + 1, (2 * total) // 3) if total > 1 else cut1
    for i, c in enumerate(ranked, 1):
        c.rank = i
        c.tier = "TIER 1" if i <= cut1 else ("TIER 2" if i <= cut2 else "TIER 3")
        if not c.pinned_ebay_listing and c.ebay_links:
            c.pinned_ebay_listing = c.ebay_links[0]
        if not c.pinned_aliexpress_listing and c.source_links:
            c.pinned_aliexpress_listing = c.source_links[0]


def combine(reports: list[ParsedReport], sources: list[SourceReport]) -> ParsedReport:
    if len(reports) == 1:
        reports[0].source_reports = sources
        return reports[0]
    out = ParsedReport(
        title=f"eBay Arbitrage Command Center ({len(reports)} reports)",
        theme=f"Aggregated across {len(reports)} report files",
        compliance="Mixed by source report. Review each report before launch.",
        source_reports=sources,
    )
    ds = [r.date for r in reports if r.date]
    out.date = max(ds) if ds else datetime.now().strftime("%Y-%m-%d")
    markets = sorted({r.market for r in reports if r.market})
    out.market = ", ".join(markets) if markets else "US (ebay.com)"
    for r in reports:
        out.candidates.extend(r.candidates)
        for a in r.agent_team:
            if a not in out.agent_team:
                out.agent_team.append(a)
    out.summary_lines = [
        f"Report files loaded: {len(sources)}",
        f"Total candidates loaded: {len(out.candidates)}",
        "HTML dashboard is the canonical output artifact for this run.",
        "Listings tab includes pinned eBay and AliExpress evidence with match scoring.",
    ]
    return out


def risk(c: Candidate) -> tuple[str, str]:
    if c.match_score is None:
        return "MEDIUM", "yellow"
    if c.match_score >= 0.80:
        return "LOW", "green"
    if c.match_score >= 0.65:
        return "MEDIUM", "yellow"
    return "HIGH", "red"


def mirror_tabs(path: pathlib.Path) -> list[str]:
    if not path.exists():
        return []
    return re.findall(r'data-tab="([a-z0-9_-]+)"', path.read_text(encoding="utf-8", errors="replace"))


def build_html(rep: ParsedReport, out_path: pathlib.Path, run_id: str, mirror_ids: list[str]) -> str:
    cands = sorted(rep.candidates, key=lambda v: v.rank)
    avg_margin = statistics.mean([safe(c.margin_pct) for c in cands if c.margin_pct is not None]) if cands else 0.0
    avg_roi = statistics.mean([safe(c.roi_pct) for c in cands if c.roi_pct is not None]) if cands else 0.0
    avg_landed = statistics.mean([safe(c.landed_cost) for c in cands if c.landed_cost is not None]) if cands else 0.0
    avg_sell = statistics.mean([safe(c.sell_price) for c in cands if c.sell_price is not None]) if cands else 0.0
    green = sum(1 for c in cands if c.decision.upper().startswith("GREEN"))
    total_inv = sum(safe(c.landed_cost) for c in cands)
    avg_spread = statistics.mean([max(0.0, safe(c.sell_price) - safe(c.landed_cost)) for c in cands]) if cands else 0.0
    est_profit = avg_spread * len(cands) * 2.5

    rank_rows: list[str] = []
    item_cards: list[str] = []
    list_rows: list[str] = []
    comp_rows: list[str] = []
    cat_map: dict[str, list[Candidate]] = {}

    for c in cands:
        cat_map.setdefault(c.category or "Uncategorized", []).append(c)
        tier_badge = "badge-green" if c.tier == "TIER 1" else ("badge-blue" if c.tier == "TIER 2" else "badge-yellow")
        sc = "#22c55e" if c.tier == "TIER 1" else ("#4f8cff" if c.tier == "TIER 2" else "#f59e0b")
        decision = c.decision.upper() if c.decision else "REVIEW"
        dec_badge = "badge-green" if decision.startswith("GREEN") or "GO" in decision else "badge-yellow"
        mscore = c.match_score if c.match_score is not None else 0.0
        mlabel = c.match_label or ("SIMILAR" if mscore >= 0.65 else "WEAK")
        rtxt, rclr = risk(c)
        ebay = c.pinned_ebay_listing or (c.ebay_links[0] if c.ebay_links else "")
        src = c.pinned_aliexpress_listing or (c.source_links[0] if c.source_links else "")
        width = max(5.0, min(100.0, c.score))
        rank_rows.append(
            f'<tr class="candidate-row" data-report="{html.escape(c.source_report_path, quote=True)}"><td>{c.rank}</td><td>{html.escape(c.title)}</td><td>{html.escape(c.category or "-")}</td><td><span class="badge {tier_badge}">{c.tier}</span></td><td>{c.score:.2f} <span class="score-bar"><span class="score-fill" style="width:{width:.1f}%;background:{sc}"></span></span></td><td class="right">{money(c.landed_cost)}</td><td class="right">{money(c.sell_price)}</td><td class="right">{pct(c.margin_pct)}</td><td class="right">{pct(c.roi_pct)}</td><td><span class="badge {dec_badge}">{html.escape(decision)}</span></td></tr>'
        )
        imgs = []
        for p in c.image_paths[:2]:
            h = href(out_path, p)
            imgs.append(f'<a href="{html.escape(h)}" target="_blank" rel="noopener noreferrer"><img src="{html.escape(h)}" class="evidence-thumb" alt="evidence"></a>')
        img_html = "".join(imgs) or '<div class="evidence-missing">No cached image evidence</div>'
        list_rows.append(
            f'<tr class="candidate-row" data-report="{html.escape(c.source_report_path, quote=True)}"><td>{html.escape(c.candidate_id or "-")}</td><td>{html.escape(c.title)}</td><td><a href="{html.escape(ebay)}" target="_blank" rel="noopener noreferrer">Pinned eBay</a></td><td><a href="{html.escape(src)}" target="_blank" rel="noopener noreferrer">Pinned AliExpress</a></td><td><span class="badge badge-blue">{mlabel}</span> {mscore:.2f}</td><td>{rtxt}</td><td>{img_html}</td></tr>'
        )
        hexc = "#22c55e" if rclr == "green" else ("#f59e0b" if rclr == "yellow" else "#ef4444")
        tier_cls = "tier1" if c.tier == "TIER 1" else ("tier2" if c.tier == "TIER 2" else "tier3")
        item_cards.append(
            f'<div class="item-card candidate-row" data-report="{html.escape(c.source_report_path, quote=True)}"><div class="item-header"><div class="item-name">#{c.rank} {html.escape(c.title)}</div><span class="item-tier {tier_cls}">{c.tier}</span></div><div style="font-size:12px;color:var(--text2)">{html.escape(c.category or "-")} &middot; {html.escape(c.candidate_id or "-")} &middot; Score {c.score:.2f}</div><div class="item-stats"><div class="item-stat"><div class="s-label">Landed Cost</div><div class="s-value">{money(c.landed_cost)}</div></div><div class="item-stat"><div class="s-label">eBay Price</div><div class="s-value">{money(c.sell_price)}</div></div><div class="item-stat"><div class="s-label">Margin</div><div class="s-value">{pct(c.margin_pct)}</div></div><div class="item-stat"><div class="s-label">ROI</div><div class="s-value">{pct(c.roi_pct)}</div></div></div><div style="margin-top:10px;font-size:12px;color:var(--text2)">Match: <strong>{mlabel}</strong> ({mscore:.2f}) &bull; Risk: <span style="color:{hexc}">{rtxt}</span></div><div style="margin-top:10px;font-size:12px;color:var(--text2)">{html.escape(c.accepted_differences or "Accepted differences not specified.")}</div><div class="evidence-row">{img_html}</div><div class="links-row"><a class="link-chip" href="{html.escape(ebay)}" target="_blank" rel="noopener noreferrer">Pinned eBay</a><a class="link-chip source" href="{html.escape(src)}" target="_blank" rel="noopener noreferrer">Pinned AliExpress</a></div></div>'
        )
        dots = '<span class="risk-dot filled-green"></span><span class="risk-dot"></span><span class="risk-dot"></span>' if rclr == "green" else ('<span class="risk-dot filled-yellow"></span><span class="risk-dot filled-yellow"></span><span class="risk-dot"></span>' if rclr == "yellow" else '<span class="risk-dot filled-red"></span><span class="risk-dot filled-red"></span><span class="risk-dot filled-red"></span>')
        comp_rows.append(f'<tr class="candidate-row" data-report="{html.escape(c.source_report_path, quote=True)}"><td>{html.escape(c.candidate_id or "-")}</td><td>{html.escape(c.title)}</td><td>{dots}</td><td>{rtxt}</td><td>{html.escape(c.accepted_differences or "No extra notes")}</td></tr>')

    cat_rows: list[str] = []
    bundle_cards: list[str] = []
    for name, items in sorted(cat_map.items(), key=lambda kv: len(kv[1]), reverse=True):
        cm = statistics.mean([safe(c.margin_pct) for c in items if c.margin_pct is not None]) if items else 0.0
        cr = statistics.mean([safe(c.roi_pct) for c in items if c.roi_pct is not None]) if items else 0.0
        cl = statistics.mean([safe(c.landed_cost) for c in items if c.landed_cost is not None]) if items else 0.0
        cs = statistics.mean([safe(c.sell_price) for c in items if c.sell_price is not None]) if items else 0.0
        cat_rows.append(f'<tr><td>{html.escape(name)}</td><td class="center">{len(items)}</td><td class="right">{money(cl)}</td><td class="right">{money(cs)}</td><td class="right">{cm:.1f}%</td><td class="right">{cr:.1f}%</td></tr>')
        chips = "".join(f'<span class="bundle-chip">{html.escape(c.title)}</span>' for c in items)
        bundle_cards.append(f'<div class="bundle-card"><h3>{html.escape(name)} Bundle</h3><div class="bundle-items">{chips}</div><div style="font-size:12px;color:var(--text2)">Avg margin {cm:.1f}% &bull; Avg ROI {cr:.1f}%</div></div>')

    expected = ["overview", "items", "listings", "bundles", "compliance", "cashflow", "scaling", "meta"]
    parity = "PASS" if mirror_ids and mirror_ids[:len(expected)] == expected else ("N/A" if not mirror_ids else "CHECK")
    imp = [
        '<div class="improve-card high"><div class="imp-title">HTML-first reporting enforced</div><div class="imp-detail">This run is generated as an HTML command center dashboard and is the canonical deliverable.</div></div>',
        '<div class="improve-card"><div class="imp-title">Pinned listing evidence added</div><div class="imp-detail">Listings tab includes pinned eBay and AliExpress links with match scores and local image artifacts.</div></div>',
        f'<div class="improve-card {"high" if parity != "PASS" else ""}"><div class="imp-title">Mirror parity status: {parity}</div><div class="imp-detail">Reference tabs: {html.escape(", ".join(mirror_ids) if mirror_ids else "not found")}</div></div>',
    ]

    report_rows = [
        "<tr data-report-row=\"1\" data-report=\"{p}\"><td>{l}</td><td class=\"center\">{c}</td><td>{m}</td><td><a class=\"link-chip\" href=\"{h}\" target=\"_blank\" rel=\"noopener noreferrer\">Open</a><button class=\"action-btn\" data-action=\"toggle-hide\" data-report=\"{p}\">Hide</button><button class=\"action-btn danger\" data-action=\"delete-report\" data-report=\"{p}\" data-label=\"{l}\">Delete</button></td></tr>".format(
            p=html.escape(s.path, quote=True), l=html.escape(s.label), c=s.candidate_count, m=html.escape(s.modified_at), h=html.escape(s.path)
        )
        for s in rep.source_reports
    ]

    summary_html = "".join(f"<li>{html.escape(s)}</li>" for s in rep.summary_lines) or "<li>No portfolio summary lines found.</li>"
    team_html = "".join(f"<li>{html.escape(t)}</li>" for t in rep.agent_team) or "<li>No explicit agent team captured.</li>"

    css = "*{margin:0;padding:0;box-sizing:border-box}:root{--bg:#0f1117;--card:#1a1d27;--card2:#242836;--accent:#4f8cff;--accent2:#22c55e;--warn:#f59e0b;--danger:#ef4444;--text:#e2e8f0;--text2:#94a3b8;--border:#2d3348}body{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;line-height:1.5}.container{max-width:1400px;margin:0 auto;padding:20px}header{text-align:center;padding:30px 0 20px;border-bottom:1px solid var(--border);margin-bottom:24px}header h1{font-size:28px;font-weight:700;background:linear-gradient(135deg,#4f8cff,#22c55e);-webkit-background-clip:text;-webkit-text-fill-color:transparent}header p{color:var(--text2);margin-top:6px;font-size:14px}.badge{display:inline-block;padding:3px 10px;border-radius:12px;font-size:11px;font-weight:600;margin:0 3px}.badge-green{background:#22c55e22;color:#22c55e;border:1px solid #22c55e44}.badge-blue{background:#4f8cff22;color:#4f8cff;border:1px solid #4f8cff44}.badge-yellow{background:#f59e0b22;color:#f59e0b;border:1px solid #f59e0b44}.tabs{display:flex;gap:4px;margin-bottom:20px;overflow-x:auto;padding-bottom:4px;border-bottom:1px solid var(--border)}.tab{padding:10px 18px;background:transparent;color:var(--text2);border:none;cursor:pointer;font-size:13px;font-weight:500;border-bottom:2px solid transparent;white-space:nowrap}.tab.active{color:var(--accent);border-bottom-color:var(--accent)}.panel{display:none}.panel.active{display:block}.kpi-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;margin-bottom:24px}.kpi{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:18px;text-align:center}.kpi .label{font-size:11px;color:var(--text2);text-transform:uppercase;letter-spacing:.5px}.kpi .value{font-size:28px;font-weight:700;margin-top:4px}.kpi .sub{font-size:12px;color:var(--text2);margin-top:2px}.card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:20px;margin-bottom:16px}.card h3{font-size:16px;font-weight:600;margin-bottom:12px}.card h4{font-size:14px;font-weight:600;margin:16px 0 8px;color:var(--accent)}table{width:100%;border-collapse:collapse;font-size:13px}th{text-align:left;padding:10px 12px;background:var(--card2);color:var(--text2);font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.5px;border-bottom:1px solid var(--border)}td{padding:10px 12px;border-bottom:1px solid var(--border);vertical-align:top}tr:hover td{background:var(--card2)}.right{text-align:right}.center{text-align:center}.score-bar{height:6px;background:var(--card2);border-radius:3px;overflow:hidden;width:100px;display:inline-block;vertical-align:middle;margin-left:6px}.score-fill{height:100%;border-radius:3px}.item-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:16px}.item-card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:18px}.item-header{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px}.item-name{font-weight:600;font-size:14px;flex:1}.item-tier{font-size:11px;font-weight:700;padding:2px 8px;border-radius:8px}.tier1{background:#22c55e22;color:#22c55e}.tier2{background:#4f8cff22;color:#4f8cff}.tier3{background:#f59e0b22;color:#f59e0b}.item-stats{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px}.item-stat{padding:6px 10px;background:var(--card2);border-radius:8px}.item-stat .s-label{font-size:10px;color:var(--text2);text-transform:uppercase}.item-stat .s-value{font-size:15px;font-weight:600}.bundle-card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:20px;margin-bottom:16px}.bundle-items{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0}.bundle-chip{background:var(--card2);padding:4px 10px;border-radius:16px;font-size:12px}.risk-dot{width:18px;height:6px;border-radius:3px;background:var(--card2);display:inline-block;margin-right:2px}.risk-dot.filled-green{background:#22c55e}.risk-dot.filled-yellow{background:#f59e0b}.risk-dot.filled-red{background:#ef4444}.improve-card{border-left:3px solid var(--accent);padding-left:14px;margin-bottom:16px}.improve-card.high{border-left-color:var(--warn)}.improve-card .imp-title{font-weight:600;font-size:14px}.improve-card .imp-detail{font-size:12px;color:var(--text2);margin-top:4px}.links-row{display:flex;gap:6px;flex-wrap:wrap;margin-top:10px}.link-chip{text-decoration:none;background:#4f8cff22;border:1px solid #4f8cff55;color:#c6dcff;padding:4px 8px;border-radius:12px;font-size:11px;font-weight:700}.link-chip.source{background:#22c55e22;border-color:#22c55e55;color:#c9f7d8}.action-btn{background:#4f8cff22;border:1px solid #4f8cff55;color:#c6dcff;padding:4px 8px;border-radius:12px;font-size:11px;font-weight:700;cursor:pointer;margin-left:6px}.action-btn.danger{background:#ef444422;border-color:#ef444455;color:#fecaca}.action-btn:disabled{opacity:.55;cursor:not-allowed}.evidence-row{display:flex;gap:8px;margin-top:10px;flex-wrap:wrap}.evidence-thumb{width:128px;height:88px;object-fit:cover;border:1px solid var(--border);border-radius:6px;background:var(--card2)}.evidence-missing{font-size:12px;color:var(--text2);padding:8px;border:1px dashed var(--border);border-radius:8px}.status-note{font-size:12px;color:var(--text2);margin-top:8px}.is-hidden-by-report{display:none!important}a{color:#8ab9ff}a:hover{color:#c6dcff}ul{margin-left:20px}li{margin:6px 0}@media(max-width:768px){.kpi-row{grid-template-columns:1fr 1fr}.item-grid{grid-template-columns:1fr}.tabs{flex-wrap:wrap}}"

    return f"""<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"UTF-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\"><title>{html.escape(rep.title or 'eBay Arbitrage Command Center')} - Command Center</title><style>{css}</style></head><body><div class=\"container\"><header><h1>{html.escape(rep.title or 'eBay Arbitrage Command Center')}</h1><p>{html.escape(rep.theme or 'Candidate portfolio')} &middot; {html.escape(rep.market or 'US (ebay.com)')} &middot; {html.escape(rep.date or datetime.now().strftime('%Y-%m-%d'))}</p><div style=\"margin-top:10px\"><span class=\"badge badge-green\">{green}/{len(cands)} Greenlight</span><span class=\"badge badge-blue\">Avg Margin {avg_margin:.1f}%</span><span class=\"badge badge-blue\">Avg ROI {avg_roi:.1f}%</span><span class=\"badge badge-yellow\">Run {html.escape(run_id)}</span></div></header><div class=\"kpi-row\"><div class=\"kpi\"><div class=\"label\">Total Investment</div><div class=\"value\" style=\"color:#4f8cff\">{money(total_inv)}</div><div class=\"sub\">{len(cands)} candidates</div></div><div class=\"kpi\"><div class=\"label\">Avg Net Margin</div><div class=\"value\" style=\"color:#22c55e\">{avg_margin:.1f}%</div><div class=\"sub\">Across all items</div></div><div class=\"kpi\"><div class=\"label\">Avg ROI</div><div class=\"value\" style=\"color:#22c55e\">{avg_roi:.1f}%</div><div class=\"sub\">Portfolio average</div></div><div class=\"kpi\"><div class=\"label\">90-Day Profit</div><div class=\"value\" style=\"color:#22c55e\">{money(est_profit)}</div><div class=\"sub\">Modeled estimate</div></div><div class=\"kpi\"><div class=\"label\">Tier 1 Items</div><div class=\"value\">{sum(1 for c in cands if c.tier == 'TIER 1')}</div><div class=\"sub\">Highest score tier</div></div><div class=\"kpi\"><div class=\"label\">Avg Landed Cost</div><div class=\"value\">{money(avg_landed)}</div><div class=\"sub\">Avg sell {money(avg_sell)}</div></div></div><div class=\"tabs\" id=\"tabs\"><button class=\"tab active\" data-tab=\"overview\">Overview</button><button class=\"tab\" data-tab=\"items\">Items</button><button class=\"tab\" data-tab=\"listings\">Listings</button><button class=\"tab\" data-tab=\"bundles\">Bundles</button><button class=\"tab\" data-tab=\"compliance\">Compliance</button><button class=\"tab\" data-tab=\"cashflow\">Cash Flow</button><button class=\"tab\" data-tab=\"scaling\">Scaling</button><button class=\"tab\" data-tab=\"meta\">Improvements</button></div><div class=\"panel active\" id=\"overview\"><div class=\"card\"><h3>Portfolio Tier Rankings</h3><table><thead><tr><th>Rank</th><th>Item</th><th>Category</th><th>Tier</th><th>Score</th><th class=\"right\">Landed</th><th class=\"right\">eBay Price</th><th class=\"right\">Margin</th><th class=\"right\">ROI</th><th>Decision</th></tr></thead><tbody>{''.join(rank_rows)}</tbody></table></div><div style=\"display:grid;grid-template-columns:1fr 1fr;gap:16px\"><div class=\"card\"><h3>Category Breakdown</h3><table><thead><tr><th>Category</th><th class=\"center\">Items</th><th class=\"right\">Avg Landed</th><th class=\"right\">Avg Price</th><th class=\"right\">Avg Margin</th><th class=\"right\">Avg ROI</th></tr></thead><tbody>{''.join(cat_rows)}</tbody></table></div><div class=\"card\"><h3>Workflow Summary</h3><ul>{summary_html}</ul><h4>Agent Team</h4><ul>{team_html}</ul></div></div></div><div class=\"panel\" id=\"items\"><div class=\"item-grid\">{''.join(item_cards)}</div></div><div class=\"panel\" id=\"listings\"><div class=\"card\"><h3>Pinned Listings and Evidence</h3><table><thead><tr><th>ID</th><th>Candidate</th><th>eBay Listing</th><th>AliExpress Listing</th><th>Match</th><th>Risk</th><th>Image Evidence</th></tr></thead><tbody>{''.join(list_rows)}</tbody></table></div></div><div class=\"panel\" id=\"bundles\">{''.join(bundle_cards)}</div><div class=\"panel\" id=\"compliance\"><div class=\"card\"><h3>Risk and Similarity Review</h3><table><thead><tr><th>ID</th><th>Candidate</th><th>Risk Meter</th><th>Level</th><th>Notes</th></tr></thead><tbody>{''.join(comp_rows)}</tbody></table></div></div><div class=\"panel\" id=\"cashflow\"><div class=\"card\"><h3>Cash Flow Timeline</h3><ul><li>Day 0: candidates validated and ranked in dashboard.</li><li>Day 1-3: source listing evidence pinned with similarity scoring.</li><li>Day 4-14: sample and quality checks on top tiers.</li><li>Day 15-90: scale winners and prune weak variants.</li></ul></div><div class=\"card\"><h3>Modeled Run Metrics</h3><table><tbody><tr><td>Total candidates</td><td class=\"right\">{len(cands)}</td></tr><tr><td>Total landed cost exposure</td><td class=\"right\">{money(total_inv)}</td></tr><tr><td>Average unit spread (sell - landed)</td><td class=\"right\">{money(avg_spread)}</td></tr><tr><td>Estimated 90-day contribution</td><td class=\"right\">{money(est_profit)}</td></tr></tbody></table></div></div><div class=\"panel\" id=\"scaling\"><div class=\"card\"><h3>Scaling Strategy</h3><ul><li>Prioritize Tier 1 candidates for larger test batches after QA pass.</li><li>Keep SIMILAR score items under tighter return monitoring until refined.</li><li>Track price stability weekly and refresh pinned listings when supplier drift appears.</li><li>Use this dashboard as the canonical artifact for run-to-run decisions.</li></ul></div></div><div class=\"panel\" id=\"meta\"><div class=\"card\"><h3>Improvement Notes</h3>{''.join(imp)}</div><div class=\"card\"><h3>Admin - Report Files</h3><table><thead><tr><th>Report</th><th class=\"center\">Candidates</th><th>Modified</th><th>Actions</th></tr></thead><tbody>{''.join(report_rows)}</tbody></table><p class=\"status-note\">Hide only affects this dashboard view (local storage). Delete removes source reports and linked run/evidence artifacts when served through report_dashboard_server.py.</p><p class=\"status-note\" id=\"status\"></p></div><div class=\"card\"><h3>Compliance Scope</h3><p style=\"color:var(--text2)\">{html.escape(rep.compliance or 'Owner review required for compliance sign-off.')}</p></div></div></div><script>document.querySelectorAll('.tab').forEach(tab=>{{tab.addEventListener('click',()=>{{document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));document.querySelectorAll('.panel').forEach(p=>p.classList.remove('active'));tab.classList.add('active');const panel=document.getElementById(tab.dataset.tab);if(panel)panel.classList.add('active');}});}});const hiddenKey='abx-hidden-reports-v2';const hiddenReports=new Set(JSON.parse(localStorage.getItem(hiddenKey)||'[]'));const status=document.getElementById('status');function saveHidden(){{localStorage.setItem(hiddenKey,JSON.stringify(Array.from(hiddenReports)));}}function setStatus(message,isError=false){{if(!status)return;status.textContent=message;status.style.color=isError?'var(--danger)':'var(--text2)';}}function applyHidden(){{document.querySelectorAll('[data-report]').forEach(node=>{{if(node.hasAttribute('data-report-row'))return;const key=node.dataset.report||'';node.classList.toggle('is-hidden-by-report',hiddenReports.has(key));}});document.querySelectorAll('button[data-action=\"toggle-hide\"]').forEach(btn=>{{const key=btn.dataset.report||'';btn.textContent=hiddenReports.has(key)?'Unhide':'Hide';}});}}function removeNodes(reportKey){{document.querySelectorAll('[data-report]').forEach(node=>{{if((node.dataset.report||'')===reportKey)node.remove();}});}}document.addEventListener('click',async event=>{{const btn=event.target.closest('button[data-action]');if(!btn)return;const action=btn.dataset.action;const reportKey=btn.dataset.report||'';const label=btn.dataset.label||reportKey;if(!reportKey)return;if(action==='toggle-hide'){{if(hiddenReports.has(reportKey))hiddenReports.delete(reportKey);else hiddenReports.add(reportKey);saveHidden();applyHidden();setStatus('Toggled visibility for '+label);return;}}if(action==='delete-report'){{if(!window.confirm('Delete '+label+' from disk? This cannot be undone.'))return;btn.disabled=true;try{{const res=await fetch('/api/reports?path='+encodeURIComponent(reportKey),{{method:'DELETE'}});if(!res.ok)throw new Error();hiddenReports.delete(reportKey);saveHidden();removeNodes(reportKey);setStatus('Deleted '+label+' and associated artifacts');}}catch{{setStatus('Delete failed. Serve with scripts/report_dashboard_server.py and open via localhost.',true);}}finally{{btn.disabled=false;}}}}}});applyHidden();</script></body></html>"""

def main() -> int:
    args = parse_args()
    input_path = pathlib.Path(args.input_path)
    try:
        md_paths = resolve_inputs(input_path)
    except ValueError as exc:
        print(str(exc))
        return 1

    out_path = resolve_out(input_path, args.output)
    reports_root = resolve_reports_root(md_paths)

    parsed: list[ParsedReport] = []
    sources: list[SourceReport] = []
    for md in md_paths:
        src = display_path(md)
        rep = parse_report(md.read_text(encoding="utf-8"), src, md.name)
        parsed.append(rep)
        sources.append(
            SourceReport(
                path=src,
                label=md.name,
                candidate_count=len(rep.candidates),
                modified_at=datetime.fromtimestamp(md.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
            )
        )

    report = combine(parsed, sources)
    decorate(report.candidates)

    evidence_path: pathlib.Path | None = None
    if args.evidence:
        evidence_path = pathlib.Path(args.evidence).resolve()
    elif args.run_id:
        evidence_path = (reports_root / ".evidence" / args.run_id / "evidence.json").resolve()
    if evidence_path:
        apply_evidence(report.candidates, load_evidence(evidence_path))

    run_id = args.run_id or datetime.now().strftime("%Y%m%d-%H%M%S")
    html_text = build_html(report, out_path, run_id, mirror_tabs(pathlib.Path(args.mirror_template)))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html_text, encoding="utf-8")
    print(f"wrote dashboard: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
