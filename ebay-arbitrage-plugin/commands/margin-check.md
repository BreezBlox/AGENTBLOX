---
description: Quick eBay margin calculation with full fee stack
allowed-tools: Read, Bash
argument-hint: [sale-price] [cogs] [shipping-cost]
---

Calculate eBay profit margins for the given parameters.

Parse the arguments: $ARGUMENTS
- First number = sale price
- Second number = cost of goods sold (landed cost)
- Third number (optional) = shipping cost to buyer (default: 0)

If the user provides additional context (category, promoted listings rate, return rate), incorporate those too.

Read the fee reference at `${CLAUDE_PLUGIN_ROOT}/skills/ebay-arbitrage-hub/references/ebay-fee-structure.md` if you need to look up category-specific FVF rates.

Run the margin calculator:
```
python ${CLAUDE_PLUGIN_ROOT}/skills/ebay-arbitrage-hub/scripts/margin_calculator.py --sale-price <PRICE> --cogs <COGS> --shipping-cost <SHIP>
```

Add any applicable flags based on user context:
- `--category <cat>` if they mention a specific eBay category
- `--promoted-rate <rate>` if they use promoted listings
- `--return-rate <rate>` if they mention a specific return expectation
- `--international` if selling internationally

Present the results clearly, highlighting net profit, net margin percentage, ROI, and the assessment. If margins are thin (under 15%), flag the risk and suggest what would need to change to make the deal work.
