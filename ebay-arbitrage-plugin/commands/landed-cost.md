---
description: Calculate true landed cost from China to your door
allowed-tools: Read, Bash
argument-hint: [product-cost] [quantity] [weight-kg]
---

Calculate the full landed cost for a China-sourced product.

Parse the arguments: $ARGUMENTS
- First number = per-unit product cost from supplier
- Second number = quantity ordered
- Third number = weight per unit in kilograms

If any values are missing, ask the user for them — all three are required for an accurate calculation.

Read the landed cost reference at `${CLAUDE_PLUGIN_ROOT}/skills/ebay-arbitrage-hub/references/landed-cost-formula.md` if you need to explain any cost components to the user.

Run the calculator:
```
python ${CLAUDE_PLUGIN_ROOT}/skills/ebay-arbitrage-hub/scripts/landed_cost.py --product-cost <COST> --quantity <QTY> --weight-kg <WEIGHT>
```

Add applicable flags based on user context:
- `--shipping-method <method>` (aliexpress_standard, air_parcel, air_freight, sea_lcl, sea_fcl, express_dhl)
- `--duty-rate <rate>` if they know their HTS duty rate
- `--section-301 <rate>` if Section 301 tariffs apply
- `--shipping-override <total>` if they have an actual freight quote
- `--defect-rate <rate>` if they have quality data from this supplier

Present the results, emphasizing:
- The per-unit landed cost vs. the supplier listing price
- The multiplier (how much higher the real cost is than the listing price)
- Which cost components are the biggest contributors
- Whether the de minimis threshold applies

If the multiplier is over 2x, flag this explicitly — many new sellers don't expect the real cost to be double the listing price.
