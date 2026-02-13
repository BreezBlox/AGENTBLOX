---
name: niche-prospector-v2
description: >
  Enhanced niche discovery skill for eBay arbitrage. Systematically identifies
  product opportunities across untapped micro-niches using a structured
  prospecting methodology. Combines eBay demand signal analysis with AliExpress
  source-depth validation. Outputs pre-qualified candidate shortlists for the
  full Gate A-E evaluation pipeline. This is a v2 enhancement that adds
  structured category rotation, demand confidence scoring, and automated
  margin pre-screening to the original sourcing-analyst workflow.
version: 0.2.0
---

# Niche Prospector Skill v2

## Purpose

Systematically discover and pre-qualify eBay product opportunities that
the sourcing-analyst skill can then validate at full depth.

## Category Rotation Strategy

To avoid portfolio concentration risk, rotate across these category verticals:

### Tier 1 — Evergreen High-Volume

- Health & Beauty (unbranded personal care tools)
- Kitchen & Dining (gadgets, utensil sets, organization)
- Office & School Supplies (desk accessories, organization)
- Cell Phones & Accessories (cases, mounts, cables)

### Tier 2 — Evergreen Mid-Volume

- Tools & Workshop (small hand tools, bits, organizers)
- Travel Accessories (packing tools, portable items)
- Baby Essentials (non-safety-critical accessories)
- Craft Supplies (organization, tools)

### Tier 3 — Seasonal/Trending (use with timing awareness)

- Outdoor/Patio (spring-summer ramp)
- Holiday Decor (Q4 spike)
- Back-to-School (July-September)
- Fitness (January peak)

## Candidate Pre-Qualification Checklist

Before a product enters the Gate A-E pipeline, it must pass ALL:

- [ ] Unbranded or generic (no VeRO risk from brand name in title)
- [ ] Lightweight: under 1 lb / 500g shipped weight
- [ ] Compact: fits in poly mailer or small box (under 12x10x4 inches)
- [ ] eBay sold velocity: ≥10 units/week across multiple sellers
- [ ] eBay median sold price: $15-$45 sweet spot
- [ ] AliExpress 1-piece price: ≤40% of eBay median sold price
- [ ] At least 2 AliExpress suppliers with 4.5+ rating
- [ ] Not in restricted/regulated category requiring certifications
- [ ] Not fragile (won't break in standard international shipping)
- [ ] Not a consumable requiring FDA/health compliance

## Margin Pre-Screen Formula

```
Quick Landed Cost = AliExpress Price × 2.2 (standard multiplier)
Quick eBay Fees = eBay Sold Price × 0.165 (13.25% FVF + $0.30 amortized)
Quick Returns Buffer = eBay Sold Price × 0.02
Quick Domestic Shipping = $4.50 (poly mailer average)
Quick Net Profit = eBay Sold Price - Quick Landed Cost - Quick eBay Fees - Quick Returns Buffer - Quick Domestic Shipping
Quick Margin = Quick Net Profit / eBay Sold Price
```

Pass if Quick Margin ≥ 18%. This is intentionally conservative to account
for the precision loss in quick screening.

## Integration with Existing Skills

- Read `../../skills/sourcing-analyst/SKILL.md` for full supplier vetting
- Read `../../skills/arbitrage-calculator/SKILL.md` for full deal scoring
- Read `../../skills/compliance-guardian/SKILL.md` when any VeRO flags arise
- Read `../../skills/listing-optimizer/SKILL.md` for listing build notes
