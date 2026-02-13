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
| **ebay-arbitrage-hub** | Central router â€” reads your request and pulls in the right specialist skills |
| **listing-optimizer** | eBay SEO, Cassini ranking factors, sold comps, title/item specifics optimization, pricing strategy |
| **sourcing-analyst** | AliExpress/Alibaba/1688 supplier vetting, landed cost, MOQ negotiation, shipping lanes, quality management |
| **arbitrage-calculator** | Full margin calculation, deal scoring, go/no-go decisions, cash flow modeling, portfolio strategy |
| **compliance-guardian** | VeRO/IP enforcement, policy compliance, restricted categories, suspension risk, returns management |
| **meta-improver** | Continuous improvement watcher â€” monitors all workflows for process and output improvements |

### Role Agents (Compliance Excluded)

Standalone role-agent copies are available under `agents/` for workflows where compliance
adjudication is intentionally deferred to owner review:

- `agents/ebay-arbitrage-hub-agent/`
- `agents/listing-optimizer-agent/`
- `agents/sourcing-analyst-agent/`
- `agents/arbitrage-calculator-agent/`
- `agents/meta-improver-agent/`

Latest 12-item candidate card report:

- `reports/ebay-12-item-candidate-cards-2026-02-11.md`

### Commands (3)

| Command | Usage |
|---------|-------|
| `/evaluate-deal` | Full deal evaluation pipeline â€” run with a product description or URL |
| `/margin-check` | Quick margin calc â€” `/margin-check 29.99 8.50 4.50` |
| `/landed-cost` | Landed cost from China â€” `/landed-cost 4.20 200 0.5` |

### Reference Documents

- eBay fee structure (FVF by category, promoted listings, international fees)
- Shipping lanes (Chinaâ†’US/EU methods, transit times, cost ranges)
- VeRO quick reference (high-risk brands, enforcement patterns)
- Supplier vetting checklist (scored evaluation framework)
- Landed cost formula (complete methodology with worked examples)

### Utility Scripts

- `margin_calculator.py` â€” Full eBay profit margin calculation with all fees
- `landed_cost.py` â€” True landed cost from China including duties, FX, defects

## Usage

Just talk naturally. The skills trigger on phrases like:

- "Is this product worth selling?"
- "Evaluate this deal"
- "Help me optimize my listing"
- "Is this supplier legit?"
- "Can I sell [brand] on eBay?"
- "What's my real margin on this?"

Or use the slash commands for quick calculations.

## Setup

No external services or API keys required. The plugin works entirely with built-in
knowledge, web search for market research, and local Python scripts for calculations.
