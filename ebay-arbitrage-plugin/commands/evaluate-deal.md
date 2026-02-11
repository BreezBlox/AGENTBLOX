---
description: Full eBay arbitrage deal evaluation pipeline
allowed-tools: Read, Bash, WebSearch
argument-hint: [product-description or URL]
---

Run a complete deal evaluation for: $ARGUMENTS

Follow this pipeline in order:

1. **Read the arbitrage calculator skill** at `${CLAUDE_PLUGIN_ROOT}/skills/arbitrage-calculator/SKILL.md` and the compliance guardian at `${CLAUDE_PLUGIN_ROOT}/skills/compliance-guardian/SKILL.md`.

2. **Research the product** — if a URL was provided, fetch product details. If a description was given, search eBay sold listings for comparable items to establish demand signals (sold price range, sell-through rate, monthly volume).

3. **Quick Compliance Screen** — read `${CLAUDE_PLUGIN_ROOT}/skills/ebay-arbitrage-hub/references/vero-quick-ref.md` and check for VeRO risk, restricted category issues, or certification requirements. If compliance is a dealbreaker, stop here and explain why.

4. **Estimate Landed Cost** — if the user provides a source price and product weight, run the landed cost calculator:
   ```
   python ${CLAUDE_PLUGIN_ROOT}/skills/ebay-arbitrage-hub/scripts/landed_cost.py --product-cost <COST> --quantity <QTY> --weight-kg <WEIGHT>
   ```
   If they don't provide these details, estimate based on the product type and note the assumptions.

5. **Calculate Margins** — run the margin calculator with the estimated sale price and landed cost:
   ```
   python ${CLAUDE_PLUGIN_ROOT}/skills/ebay-arbitrage-hub/scripts/margin_calculator.py --sale-price <PRICE> --cogs <LANDED_COST> --shipping-cost <SHIP>
   ```

6. **Score the Deal** — using the deal scoring framework from the arbitrage calculator skill, rate the opportunity across: net margin, ROI, demand strength, competition, and risk profile.

7. **Present a Go/No-Go Recommendation** with:
   - Deal score and rating
   - Key numbers (net margin %, ROI %, breakeven price)
   - Top risk factors
   - Recommended next step (test order quantity, pass, or needs more research)
