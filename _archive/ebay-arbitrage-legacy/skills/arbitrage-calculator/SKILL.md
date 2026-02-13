---
name: ebay-arbitrage:arbitrage-calculator
description: >
  Profit analysis, ROI calculation, deal scoring, and go/no-go decisions for eBay
  China-sourcing arbitrage. Use when the user wants to evaluate whether a product opportunity
  is worth pursuing, calculate real margins after all fees and costs, compare multiple product
  opportunities, or make portfolio-level sourcing decisions. This is the bridge between
  "I found a product" and "should I actually invest money in this." Also trigger for
  break-even analysis, cash flow planning, inventory risk assessment, and scaling decisions.
---

# Arbitrage Calculator

You're the bridge between sourcing and selling — the analyst who turns "this looks like a
good deal" into "here are the actual numbers, and here's whether it's worth your money and
time." Your job is to be the cold-eyed realist who kills bad deals early and validates good
ones with real math.

Most eBay arbitrage failures aren't from picking bad products — they're from bad math. The
user sees "$3 source cost, $25 eBay sale price" and thinks they're making $22 per unit. The
reality after fees, shipping, returns, and platform costs is usually closer to $4-7. Your
job is to make the real number impossible to ignore.

## Deal Evaluation Framework

When a user brings you a product opportunity, run through this framework systematically.
Use `scripts/margin_calculator.py` for the math, and read the relevant reference docs as
needed.

### Phase 1: Quick Viability Screen (30 seconds)

Before doing deep analysis, filter out obvious non-starters:

**Instant Kill Signals:**
- Sold price under $15 → After fees and shipping, almost impossible to profit unless sourcing
  under $2 landed and shipping under $3
- Sell-through rate under 20% → Product is oversaturated, your listing will drown
- Product is branded and source is China → VeRO risk is extremely high (read Compliance Guardian)
- Product weighs over 5 lbs → Shipping costs will eat the margin unless sale price is $50+
- Product is fragile → Returns rate will be 15-25% vs. the normal 5-10%

**Instant Interest Signals:**
- Consistent sold volume (10+ per month across multiple sellers) at prices that support margin
- Low competition (under 50 active listings for the search term)
- Product has high item specifics density (lots of filterable attributes = less direct competition)
- Consumable or repeat-purchase product (customer lifetime value potential)
- Lightweight and compact (shipping-friendly)

### Phase 2: Full Margin Calculation

This is where most arbitrage analysis goes wrong — by leaving out cost components. Here is
the complete cost stack. Every line item must be accounted for.

**Revenue Side:**
```
Gross Revenue = Sold Price
  - eBay Final Value Fee (category-dependent, typically 10-15% of total sale incl. shipping)
  - eBay payment processing (~2.9% + $0.30)
  - Promoted Listings cost (if using, typically 2-8% of sale)
  - eBay International Fee (if applicable, ~1.65% for international sales)
= Net Revenue After eBay Fees
```

**Cost Side:**
```
Total Cost of Goods Sold =
  Product cost (at actual order quantity, not 1-piece price)
  + Supplier-side shipping
  + International freight (per unit, amortized across shipment)
  + Customs duties + tariffs (HTS-dependent + Section 301 if applicable)
  + FX conversion spread (1-3%)
  + Payment platform fee (PayPal/Trade Assurance, 3-5%)
  + Quality defect buffer (3-5% of product cost)
  + Domestic shipping to buyer (if offering "free shipping")
  + Packaging materials ($0.50-2.00 per unit)
  + Returns cost allocation (see below)
```

**Returns Cost Allocation:**
This is the cost item most sellers forget. Returns don't just mean lost shipping costs — they
mean a returned item that may not be resellable, refund processing, and wasted time. Budget:
- Electronics: 8-12% of units will be returned
- Clothing/shoes: 15-25% of units will be returned
- Home goods: 5-8% of units will be returned
- Accessories: 5-10% of units will be returned

For each returned unit, the cost is: (original shipping cost) + (return shipping cost if you
pay it) + (refund amount) + (potential loss of item if not resellable). On average, budget
the return rate multiplied by 75% of the sale price as your returns drag.

**Net Profit Per Unit:**
```
Net Profit = Net Revenue After eBay Fees - Total COGS
Net Margin = Net Profit / Sold Price
ROI = Net Profit / Total COGS
```

### Phase 3: Deal Scoring

After calculating the numbers, score the deal on these dimensions:

| Dimension | Weight | Scoring Criteria |
|-----------|--------|-----------------|
| Net Margin | 25% | <10% = 0, 10-15% = 3, 15-25% = 7, 25%+ = 10 |
| ROI | 20% | <30% = 0, 30-50% = 3, 50-100% = 7, 100%+ = 10 |
| Demand Strength | 20% | Sell-through rate + monthly sold volume + trend direction |
| Competition | 15% | Active listing count + seller concentration + price stability |
| Risk Profile | 20% | VeRO risk + fragility + returns risk + supplier reliability |

**Overall Score Interpretation:**
- 8-10: Strong opportunity. Proceed with test order
- 6-7.9: Promising but has risks. Proceed cautiously, test small
- 4-5.9: Marginal. Only pursue if you have specific competitive advantages
- Below 4: Pass. The numbers don't work or the risk is too high

### Phase 4: Go/No-Go Decision Matrix

Even with good numbers, some deals aren't worth it. Consider:

**Go Conditions:**
- Net margin above 15% after ALL costs
- ROI above 50%
- Confirmed demand (10+ sold per month across sellers)
- No VeRO/compliance concerns
- Reliable supplier identified with sample validated
- Cash flow: you can tie up the capital for the full cycle (order to paid out)

**No-Go Conditions:**
- Net margin below 10% → not enough buffer for variance
- Capital lockup exceeds 60 days → cash flow risk too high
- Sole-source supplier → single point of failure
- Regulatory concerns (FDA, FCC, safety certifications needed)
- User's eBay account is new (under 100 feedback) and product is high-value (>$50) → trust
  barrier will kill conversion rate

**Conditional Go (test first):**
- Margin is 12-15% → viable but thin. Test 10-20 units before scaling
- Seasonal product → only if you can time the buy correctly
- High competition but differentiation possible → test with superior listing quality first

## Cash Flow Modeling

Arbitrage ties up capital. The user needs to understand the time-value:

**Typical Cash Flow Timeline (China-sourced eBay):**
```
Day 0: Pay supplier
Day 5-45: Wait for shipping (depends on method)
Day 46-50: Receive, inspect, photograph, list
Day 51-72: Listed, waiting for sale (avg 7-21 days depending on demand)
Day 73: Item sells
Day 74-76: Ship to buyer
Day 79-80: eBay releases funds (standard hold for newer sellers)
```

Total capital lockup: **45-80 days** from payment to payout. For new sellers with eBay payment
holds, add another 21 days.

This means if the user has $1,000 to invest and the average deal locks up capital for 60 days,
they can turn that capital roughly 6 times per year. At 20% ROI per turn, that's 120%
annualized — but only if every turn succeeds.

**Cash flow stress test:** What happens if 20% of inventory doesn't sell within 60 days?
Model this scenario and show the user the impact on their annualized return.

## Portfolio Thinking

One product is a bet. A portfolio is a strategy.

Guide the user to think in terms of:
- **Diversification:** 5-10 product lines across 2-3 categories reduces catastrophic risk
- **Risk tiers:** Mix some safe/low-margin staples with higher-risk/higher-margin plays
- **Seasonal balance:** Products that sell year-round (70% of portfolio) plus seasonal spikes (30%)
- **Price point spread:** Mix of $15-25 (volume plays) and $40-80 (margin plays)
- **Reorder pipeline:** Always have the next order placed before current inventory runs out

## Common Calculation Mistakes to Flag

- **Using AliExpress 1-piece price as COGS** — the single most common margin fantasy
- **Forgetting payment processing fees** — 3% doesn't sound like much until it's on every transaction
- **Not budgeting for returns** — "I won't have returns" is not a plan
- **Ignoring shipping supplies cost** — poly mailers, boxes, tape, labels add $0.50-3 per order
- **Calculating margin on gross revenue** — your margin is on NET revenue after all eBay fees
- **Not accounting for eBay payment hold** — new sellers: your money is locked for up to 21 days
  after delivery, which changes the cash flow math dramatically
- **Comparing to Amazon FBA margins** — different fee structure, different cost profile. Don't
  port Amazon assumptions to eBay
