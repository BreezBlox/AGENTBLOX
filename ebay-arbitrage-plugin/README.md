# eBay Arbitrage Plugin

Hybrid eBay marketplace operator and China-sourcing arbitrage analyst for Claude Cowork.

## What It Does

Combines deep eBay marketplace fluency with China-side sourcing realities and compliance
awareness. Evaluates product opportunities end-to-end: from supplier vetting and landed cost
calculation through eBay listing optimization and fee-aware margin analysis, with a compliance
layer that keeps your account healthy.

## Components

### Skills (5)

| Skill | Purpose |
|-------|---------|
| **ebay-arbitrage-hub** | Central router that reads your request and pulls in the right specialist skills |
| **listing-optimizer** | eBay SEO, sold comps, title/item specifics optimization, pricing strategy |
| **sourcing-analyst** | AliExpress-only supplier vetting, landed cost, MOQ negotiation, shipping lanes, quality management |
| **arbitrage-calculator** | Full margin calculation, deal scoring, go/no-go decisions, cash flow modeling, portfolio strategy |
| **compliance-guardian** | VeRO/IP enforcement, policy compliance, restricted categories, suspension risk, returns management |
| **meta-improver** | Continuous improvement watcher across workflows |

### Role Agents (Compliance Excluded)

Standalone role-agent copies are available under `agents/` for workflows where compliance
adjudication is intentionally deferred to owner review:

- `agents/ebay-arbitrage-hub-agent/`
- `agents/listing-optimizer-agent/`
- `agents/sourcing-analyst-agent/`
- `agents/arbitrage-calculator-agent/`
- `agents/meta-improver-agent/`

Latest canonical dashboard output:

- `reports/<run-name>.html`

### Commands (3)

| Command | Usage |
|---------|-------|
| `/evaluate-deal` | Full deal evaluation pipeline run with a product description or URL |
| `/margin-check` | Quick margin calc: `/margin-check 29.99 8.50 4.50` |
| `/landed-cost` | Landed cost from China: `/landed-cost 4.20 200 0.5` |

### Reference Documents

- eBay fee structure (FVF by category, promoted listings, international fees)
- Shipping lanes (China->US/EU methods, transit times, cost ranges)
- VeRO quick reference (high-risk brands, enforcement patterns)
- Supplier vetting checklist (scored evaluation framework)
- Landed cost formula (complete methodology with worked examples)

### Utility Scripts

- `skills/ebay-arbitrage-hub/scripts/margin_calculator.py`: full eBay profit margin calculation
- `skills/ebay-arbitrage-hub/scripts/landed_cost.py`: landed cost from China including duties/FX/defects
- `scripts/exact_match_pipeline.py`: native enrichment + HTML dashboard generation
- `scripts/render_candidate_dashboard.py`: v2 command-center dashboard renderer
- `scripts/report_dashboard_server.py`: local server with hide/delete + run/evidence cleanup
- `scripts/prune_evidence_runs.py`: retention utility for `.runs` and `.evidence`
- `scripts/validate_command_center_dashboard.py`: contract/parity checks for generated dashboards

## HTML-First Reporting

The final report output is HTML and presented as a dashboard.

```powershell
python scripts/exact_match_pipeline.py reports/ebay-12-item-candidates-2026-02-12-retro-collectors-replacement.md --output reports/ebay-12-item-candidates-2026-02-12-retro-repair-collectors-batch-2.html
```

This writes:

- `reports/<run-name>.html`
- `reports/.runs/<run-id>/manifest.json`
- `reports/.evidence/<run-id>/evidence.json`

## Setup

No external services or API keys are required by default. The plugin works with built-in
knowledge, web search for market research, and local Python scripts.
