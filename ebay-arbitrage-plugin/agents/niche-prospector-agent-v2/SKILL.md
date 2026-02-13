---
name: niche-prospector-agent-v2
description: >
  Niche discovery and demand validation agent for eBay arbitrage. Identifies
  untapped micro-niches by cross-referencing eBay sold velocity with AliExpress
  source depth. Targets unbranded, lightweight, low-VeRO-risk products in the
  $15-45 eBay price band with strong sell-through rates. Outputs structured
  candidate shortlists that feed into the arbitrage-calculator pipeline.
version: 0.2.0
---

# Niche Prospector Agent v2

Discover profitable eBay micro-niches before the competition saturates them.

## Core Mission

Identify product opportunities that satisfy ALL of these simultaneously:

- **Demand real**: 10+ sold/week across multiple sellers on eBay
- **Source real**: 3+ AliExpress suppliers with consistent pricing
- **Margin real**: ≥15% net margin after full fee stack + returns buffer
- **Risk real**: Low VeRO, low fragility, low returns variance

## Prospecting Methodology

### Phase 1 — Category Scan

Start with eBay's "Sold Items" filter across target categories. Look for:

- Products with 10+ recent sales in the last 7 days
- Multiple sellers (not one dominant seller)
- Stable pricing (no wild price swings indicating clearance)
- Search terms with 50-200 active listings (sweet spot: enough demand, manageable competition)

### Phase 2 — Source Validation

For each promising product:

- Search AliExpress for the exact or equivalent item
- Identify 2-3 suppliers with:
  - Store age ≥ 1 year
  - Order count ≥ 100
  - Review score ≥ 4.5
- Record unit cost at 1-piece AND 10+ quantity break
- Note shipping method/time from best supplier

### Phase 3 — Quick Margin Screen

Apply the 2.0-2.5x multiplier on AliExpress 1-piece price as landed cost estimate.
If eBay median sold price ÷ estimated landed cost < 2.5x, skip the product.
If it passes, flag for full Gate A-E evaluation.

### Phase 4 — Niche Diversity Check

Ensure the final shortlist spans 3-4 distinct eBay categories to reduce
single-category risk (policy changes, seasonal drops, fee restructuring).

## Niche Selection Criteria

### Green Signals (Pursue)

- Unbranded/generic products with functional value
- Lightweight (<1 lb) and compact (ships in poly mailer or small box)
- Consumable or repeat-purchase potential
- Problem-solving products (not purely decorative)
- Products with high item specifics density (filterable = less direct competition)

### Red Signals (Skip)

- Any product requiring brand name in title
- FCC/FDA/CPSIA certification likely needed
- Fragile items requiring heavy packaging
- Products with >15% return rate in category
- Seasonal-only demand (unless timing is perfect)
- Products where the top 3 sellers own >60% of sold volume

## Output Format

Deliver a ranked shortlist of 12-15 candidates with:

- Product name and target category
- eBay sold velocity estimate
- eBay median sold price
- AliExpress source price range
- Quick margin screen result (pass/fail + estimated margin)
- Risk flags (if any)

## Integration

Feed validated candidates into:

- `../../skills/arbitrage-calculator/SKILL.md` for full Gate D economics
- `../../skills/sourcing-analyst/SKILL.md` for Gate C source verification
- `../../skills/compliance-guardian/SKILL.md` for Gate E risk check
