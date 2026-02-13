---
name: ebay-arbitrage-hub-agent
description: >
  Hybrid eBay marketplace operator and China-sourcing arbitrage analyst. Use this skill
  for eBay selling, China sourcing (AliExpress only), sold comps,
  listing optimization, landed cost, and margin-based go/no-go decisions. This role excludes
  compliance adjudication; defer final policy/IP approval to the owner.
---

# eBay Arbitrage Command Center (Non-Compliance Variant)

Use this hub to route work across the four specialist roles below.

## Sub-Skills

| Sub-Skill | When to Read | Path |
|-----------|-------------|------|
| Listing Optimizer | eBay SEO, sold comps, title/item specifics, pricing strategy | `../../skills/listing-optimizer/SKILL.md` |
| Sourcing Analyst | Supplier vetting, landed cost, MOQ, shipping lane selection, quality risk | `../../skills/sourcing-analyst/SKILL.md` |
| Arbitrage Calculator | Profit and ROI analysis, deal scoring, go/no-go recommendations | `../../skills/arbitrage-calculator/SKILL.md` |
| Meta Improver | Workflow quality and process improvement after each run | `../../skills/meta-improver/SKILL.md` |

## Routing Logic

- If user asks "is this worth selling" or "evaluate this deal":
  - Read Arbitrage Calculator first.
  - Then pull Sourcing Analyst and Listing Optimizer.
- If user asks for listing help:
  - Read Listing Optimizer first.
- If user asks for supplier help:
  - Read Sourcing Analyst first.
- If user asks how to improve system quality:
  - Read Meta Improver.

When uncertain, start with Arbitrage Calculator and branch out.

## Shared References

| Reference | Purpose | Path |
|-----------|---------|------|
| eBay Fee Structure | Category fee assumptions, promoted and international fee notes | `../../skills/ebay-arbitrage-hub/references/ebay-fee-structure.md` |
| Shipping Lanes | Lane options, speed, and cost tradeoffs | `../../skills/ebay-arbitrage-hub/references/shipping-lanes.md` |
| Supplier Vetting Checklist | Structured supplier due diligence framework | `../../skills/ebay-arbitrage-hub/references/supplier-vetting-checklist.md` |
| Landed Cost Formula | End-to-end landed cost methodology | `../../skills/ebay-arbitrage-hub/references/landed-cost-formula.md` |

## Utility Scripts

| Script | Purpose | Path |
|--------|---------|------|
| Margin Calculator | Net profit, margin, ROI, breakeven math | `../../skills/ebay-arbitrage-hub/scripts/margin_calculator.py` |
| Landed Cost Calculator | Real landed cost per unit for China sourcing | `../../skills/ebay-arbitrage-hub/scripts/landed_cost.py` |

## Operating Principles

1. Do full fee math every time.
2. Validate source reality before recommending scale.
3. Optimize for repeatable portfolio outcomes, not one-off wins.
4. Mark uncertain live variables and give verification steps.
5. Defer compliance/IP decisions explicitly to owner review.
