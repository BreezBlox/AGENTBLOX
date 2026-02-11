#!/usr/bin/env python3
"""
eBay Arbitrage Margin Calculator

Calculates true net profit and margin for an eBay sale after ALL fees and costs.
This isn't your napkin-math "sale price minus product cost" calculator — it accounts
for the full fee stack that turns a "40% margin" dream into a 12% reality.

Usage:
    python margin_calculator.py --sale-price 29.99 --cogs 8.50 --shipping-cost 4.50
    python margin_calculator.py --sale-price 29.99 --cogs 8.50 --shipping-cost 4.50 \
        --category electronics --promoted-rate 5 --return-rate 10 --international
    python margin_calculator.py --help

The script prints a detailed breakdown and a summary with net profit, net margin, and ROI.
"""

import argparse
import json
import sys


# Default FVF rates by category (percentage of total sale amount)
# These are approximate — always verify current rates on eBay
FVF_RATES = {
    "default": 13.25,
    "books": 14.95,
    "dvds": 14.95,
    "movies": 14.95,
    "music": 14.95,
    "business_industrial": 12.35,
    "clothing": 12.35,
    "shoes": 12.35,
    "accessories": 12.35,
    "collectibles": 13.25,
    "computers": 12.35,
    "tablets": 12.35,
    "electronics": 12.35,
    "cell_phones": 12.35,
    "health_beauty": 13.25,
    "home_garden": 13.25,
    "jewelry": 13.25,
    "watches": 13.25,
    "musical_instruments": 12.35,
    "auto_parts": 12.35,
    "sporting_goods": 12.35,
    "toys": 13.25,
    "video_games": 13.25,
}

PER_ORDER_FEE = 0.30  # Fixed per-transaction fee
INTERNATIONAL_FEE_RATE = 1.65  # Percentage for international sales


def calculate_margin(
    sale_price: float,
    cogs: float,
    shipping_cost: float = 0.0,
    category: str = "default",
    fvf_override: float = None,
    promoted_rate: float = 0.0,
    return_rate: float = 8.0,
    international: bool = False,
    packaging_cost: float = 1.00,
    return_shipping_cost: float = None,
) -> dict:
    """
    Calculate full eBay margin with all fees.

    Args:
        sale_price: The price the item sells for on eBay
        cogs: Cost of goods sold (landed cost — use landed_cost.py to calculate this)
        shipping_cost: Cost to ship to the buyer (if offering free shipping, this is your cost)
        category: eBay category for FVF rate lookup
        fvf_override: Override the FVF rate directly (percentage)
        promoted_rate: Promoted Listings ad rate (percentage, 0 if not using)
        return_rate: Expected return rate (percentage of units, default 8%)
        international: Whether this is an international sale (adds 1.65% fee)
        packaging_cost: Cost of packaging materials per unit (default $1.00)
        return_shipping_cost: Cost of return shipping per returned unit (default: same as shipping_cost)

    Returns:
        dict with full breakdown and summary
    """
    # Determine FVF rate
    if fvf_override is not None:
        fvf_rate = fvf_override
    else:
        fvf_rate = FVF_RATES.get(category.lower().replace(" ", "_"), FVF_RATES["default"])

    # Default return shipping to outbound shipping cost
    if return_shipping_cost is None:
        return_shipping_cost = shipping_cost

    # --- Revenue Side ---
    gross_revenue = sale_price

    # eBay Final Value Fee (on total sale amount including any shipping buyer pays)
    fvf_amount = sale_price * (fvf_rate / 100)

    # Per-order fee
    per_order = PER_ORDER_FEE

    # Promoted Listings fee (on sale price, only if using)
    promoted_amount = sale_price * (promoted_rate / 100) if promoted_rate > 0 else 0.0

    # International fee
    international_amount = sale_price * (INTERNATIONAL_FEE_RATE / 100) if international else 0.0

    total_ebay_fees = fvf_amount + per_order + promoted_amount + international_amount
    ebay_fee_percentage = (total_ebay_fees / sale_price) * 100

    net_revenue = gross_revenue - total_ebay_fees

    # --- Cost Side ---
    total_cogs = cogs + shipping_cost + packaging_cost

    # --- Returns Drag ---
    # For each returned unit: you lose the sale revenue, pay return shipping,
    # and the item may not be resellable. Model as: return_rate% of units incur
    # (return_shipping_cost + 25% chance item is unsellable)
    return_fraction = return_rate / 100
    # Cost per return: return shipping + 25% chance of total loss
    cost_per_return = return_shipping_cost + (0.25 * cogs)
    # Average returns cost spread across all units
    returns_drag_per_unit = return_fraction * (cost_per_return + sale_price * (fvf_rate / 100))
    # More accurate: the return refund means you lose the sale but get FVF credit
    # eBay credits FVF on returns (for free returns). Simplify to:
    returns_drag_per_unit = return_fraction * (return_shipping_cost + (0.25 * cogs))

    # --- Net Profit ---
    net_profit = net_revenue - total_cogs - returns_drag_per_unit

    # --- Ratios ---
    net_margin = (net_profit / sale_price) * 100 if sale_price > 0 else 0
    roi = (net_profit / total_cogs) * 100 if total_cogs > 0 else 0

    # --- Breakeven ---
    # What's the minimum sale price to break even?
    # net_revenue - total_cogs - returns_drag = 0
    # sale_price - (sale_price * total_fee_rate) - per_order - total_cogs - returns_drag = 0
    total_fee_rate_decimal = (fvf_rate + promoted_rate + (INTERNATIONAL_FEE_RATE if international else 0)) / 100
    # Approximate breakeven (ignoring the returns drag dependency on sale price)
    breakeven_price = (total_cogs + per_order + returns_drag_per_unit) / (1 - total_fee_rate_decimal)

    result = {
        "input": {
            "sale_price": sale_price,
            "cogs_landed": cogs,
            "shipping_to_buyer": shipping_cost,
            "packaging": packaging_cost,
            "category": category,
            "fvf_rate": fvf_rate,
            "promoted_rate": promoted_rate,
            "return_rate": return_rate,
            "international": international,
        },
        "fees": {
            "final_value_fee": round(fvf_amount, 2),
            "per_order_fee": per_order,
            "promoted_listings_fee": round(promoted_amount, 2),
            "international_fee": round(international_amount, 2),
            "total_ebay_fees": round(total_ebay_fees, 2),
            "ebay_fee_percentage": round(ebay_fee_percentage, 1),
        },
        "costs": {
            "cogs_landed": cogs,
            "shipping_to_buyer": shipping_cost,
            "packaging": packaging_cost,
            "total_cogs": round(total_cogs, 2),
            "returns_drag_per_unit": round(returns_drag_per_unit, 2),
        },
        "summary": {
            "gross_revenue": round(gross_revenue, 2),
            "net_revenue_after_fees": round(net_revenue, 2),
            "total_costs": round(total_cogs + returns_drag_per_unit, 2),
            "net_profit": round(net_profit, 2),
            "net_margin_pct": round(net_margin, 1),
            "roi_pct": round(roi, 1),
            "breakeven_price": round(breakeven_price, 2),
        },
        "assessment": get_assessment(net_margin, roi),
    }

    return result


def get_assessment(net_margin: float, roi: float) -> str:
    """Return a plain-English assessment of the deal quality."""
    if net_margin >= 25 and roi >= 80:
        return "Strong opportunity. Healthy margins with good ROI. Proceed with confidence."
    elif net_margin >= 15 and roi >= 50:
        return "Good opportunity. Solid margins. Standard arbitrage territory."
    elif net_margin >= 10 and roi >= 30:
        return "Marginal. Thin margins leave little room for error. Proceed only with tight cost control."
    elif net_margin >= 5:
        return "Weak. Margins are too thin — returns, shipping variance, or fee changes could wipe profit. Consider passing."
    else:
        return "Not viable. The numbers don't work after real costs. Pass on this deal."


def print_report(result: dict):
    """Print a human-readable margin report."""
    inp = result["input"]
    fees = result["fees"]
    costs = result["costs"]
    summary = result["summary"]

    print("\n" + "=" * 60)
    print("  eBay ARBITRAGE MARGIN CALCULATOR")
    print("=" * 60)

    print(f"\n  Sale Price:           ${inp['sale_price']:.2f}")
    print(f"  Category:             {inp['category']} (FVF: {inp['fvf_rate']}%)")
    if inp["promoted_rate"] > 0:
        print(f"  Promoted Listings:    {inp['promoted_rate']}%")
    if inp["international"]:
        print(f"  International:        Yes (+{INTERNATIONAL_FEE_RATE}%)")
    print(f"  Expected Return Rate: {inp['return_rate']}%")

    print(f"\n--- eBay Fees ---")
    print(f"  Final Value Fee:      -${fees['final_value_fee']:.2f}")
    print(f"  Per-Order Fee:        -${fees['per_order_fee']:.2f}")
    if fees["promoted_listings_fee"] > 0:
        print(f"  Promoted Listings:    -${fees['promoted_listings_fee']:.2f}")
    if fees["international_fee"] > 0:
        print(f"  International Fee:    -${fees['international_fee']:.2f}")
    print(f"  Total eBay Fees:      -${fees['total_ebay_fees']:.2f} ({fees['ebay_fee_percentage']}%)")

    print(f"\n--- Costs ---")
    print(f"  COGS (Landed):        -${costs['cogs_landed']:.2f}")
    print(f"  Shipping to Buyer:    -${costs['shipping_to_buyer']:.2f}")
    print(f"  Packaging:            -${costs['packaging']:.2f}")
    print(f"  Returns Drag:         -${costs['returns_drag_per_unit']:.2f}")
    print(f"  Total Costs:          -${summary['total_costs']:.2f}")

    print(f"\n--- Summary ---")
    print(f"  Gross Revenue:        ${summary['gross_revenue']:.2f}")
    print(f"  Net After Fees:       ${summary['net_revenue_after_fees']:.2f}")
    print(f"  Net Profit:           ${summary['net_profit']:.2f}")
    print(f"  Net Margin:           {summary['net_margin_pct']}%")
    print(f"  ROI on Costs:         {summary['roi_pct']}%")
    print(f"  Breakeven Price:      ${summary['breakeven_price']:.2f}")

    print(f"\n  Assessment: {result['assessment']}")
    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Calculate eBay arbitrage margins with full fee stack",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Basic calculation:
    %(prog)s --sale-price 29.99 --cogs 8.50 --shipping-cost 4.50

  Electronics with promoted listings:
    %(prog)s --sale-price 49.99 --cogs 15.00 --shipping-cost 6.00 \\
        --category electronics --promoted-rate 4

  International sale with high return rate:
    %(prog)s --sale-price 35.00 --cogs 10.00 --shipping-cost 5.00 \\
        --international --return-rate 15

  JSON output for programmatic use:
    %(prog)s --sale-price 29.99 --cogs 8.50 --shipping-cost 4.50 --json
        """,
    )

    parser.add_argument("--sale-price", type=float, required=True, help="eBay sale price")
    parser.add_argument("--cogs", type=float, required=True, help="Landed cost of goods (use landed_cost.py)")
    parser.add_argument("--shipping-cost", type=float, default=0.0, help="Shipping cost to buyer (default: 0)")
    parser.add_argument("--category", type=str, default="default", help=f"eBay category. Options: {', '.join(FVF_RATES.keys())}")
    parser.add_argument("--fvf-override", type=float, default=None, help="Override FVF rate directly (percentage)")
    parser.add_argument("--promoted-rate", type=float, default=0.0, help="Promoted Listings ad rate (percentage)")
    parser.add_argument("--return-rate", type=float, default=8.0, help="Expected return rate (percentage, default: 8)")
    parser.add_argument("--international", action="store_true", help="International sale (adds 1.65%% fee)")
    parser.add_argument("--packaging-cost", type=float, default=1.00, help="Packaging materials cost (default: $1.00)")
    parser.add_argument("--json", action="store_true", help="Output as JSON instead of formatted report")

    args = parser.parse_args()

    result = calculate_margin(
        sale_price=args.sale_price,
        cogs=args.cogs,
        shipping_cost=args.shipping_cost,
        category=args.category,
        fvf_override=args.fvf_override,
        promoted_rate=args.promoted_rate,
        return_rate=args.return_rate,
        international=args.international,
        packaging_cost=args.packaging_cost,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_report(result)


if __name__ == "__main__":
    main()
