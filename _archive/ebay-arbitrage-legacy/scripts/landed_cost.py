#!/usr/bin/env python3
"""
Landed Cost Calculator

Calculates the true per-unit landed cost of a product sourced from China,
accounting for all cost components that bridge the gap between "supplier listing price"
and "actual cost of goods in hand, ready to ship."

Usage:
    python landed_cost.py --product-cost 4.20 --quantity 200 --weight-kg 0.5
    python landed_cost.py --product-cost 4.20 --quantity 200 --weight-kg 0.5 \
        --shipping-method air_freight --duty-rate 11.4 --defect-rate 4
    python landed_cost.py --help

The script prints a detailed cost breakdown and the final per-unit landed cost.
"""

import argparse
import json
import sys


# Shipping rate estimates per kg by method
# These are rough averages — actual rates vary by route, season, and provider
SHIPPING_RATES = {
    "aliexpress_standard": {
        "name": "AliExpress Standard / ePacket",
        "rate_per_kg": 12.00,  # Approximate average for light parcels
        "base_fee": 2.00,  # Minimum shipping charge
        "max_weight_kg": 5.0,
        "notes": "Best for 1-10 unit test orders from AliExpress",
    },
    "air_parcel": {
        "name": "Air Parcel (small batch)",
        "rate_per_kg": 8.00,
        "base_fee": 15.00,
        "max_weight_kg": 30.0,
        "notes": "Good for 10-50 unit orders via freight forwarder",
    },
    "air_freight": {
        "name": "Air Freight (cargo)",
        "rate_per_kg": 5.50,
        "base_fee": 50.00,  # Handling/documentation
        "max_weight_kg": None,  # No practical limit
        "notes": "Best for 50-500 unit orders — good balance of cost and speed",
    },
    "sea_lcl": {
        "name": "Sea Freight (LCL)",
        "rate_per_kg": 1.50,
        "base_fee": 200.00,  # Minimum charges for LCL
        "max_weight_kg": None,
        "notes": "Less-than-container load. 45-70 days. Good for 200+ units if time allows",
    },
    "sea_fcl": {
        "name": "Sea Freight (FCL - 20ft container)",
        "rate_per_kg": 0.30,
        "base_fee": 2500.00,  # Container booking + handling
        "max_weight_kg": None,
        "notes": "Full container. 40-60 days. Only for large-scale operations",
    },
    "express_dhl": {
        "name": "Express (DHL/FedEx/UPS)",
        "rate_per_kg": 25.00,
        "base_fee": 10.00,
        "max_weight_kg": None,
        "notes": "3-7 days. Expensive but fast. Best for high-value or urgent shipments",
    },
}

# Default fee percentages
DEFAULT_FX_SPREAD = 2.5  # Percentage
DEFAULT_PAYMENT_FEE = 3.0  # Percentage
DEFAULT_INSURANCE_RATE = 1.5  # Percentage of goods value
DEFAULT_CUSTOMS_BROKERAGE = 150.00  # Flat fee per shipment
DEFAULT_DOMESTIC_DELIVERY = 0.0  # Often included in freight forwarder quote
DEFAULT_DEFECT_RATE = 4.0  # Percentage of units


def calculate_landed_cost(
    product_cost: float,
    quantity: int,
    weight_per_unit_kg: float,
    shipping_method: str = "air_freight",
    duty_rate: float = 0.0,
    section_301_rate: float = 0.0,
    fx_spread: float = DEFAULT_FX_SPREAD,
    payment_fee: float = DEFAULT_PAYMENT_FEE,
    insurance_rate: float = DEFAULT_INSURANCE_RATE,
    customs_brokerage: float = DEFAULT_CUSTOMS_BROKERAGE,
    domestic_delivery: float = DEFAULT_DOMESTIC_DELIVERY,
    defect_rate: float = DEFAULT_DEFECT_RATE,
    shipping_cost_override: float = None,
) -> dict:
    """
    Calculate full landed cost per unit.

    Args:
        product_cost: Per-unit cost from supplier at the given quantity
        quantity: Number of units ordered
        weight_per_unit_kg: Weight per unit in kilograms
        shipping_method: One of the SHIPPING_RATES keys
        duty_rate: Base customs duty rate (percentage)
        section_301_rate: Additional Section 301 tariff rate (percentage)
        fx_spread: Foreign exchange conversion spread (percentage, default 2.5)
        payment_fee: Payment platform fee (percentage, default 3.0)
        insurance_rate: Cargo insurance rate (percentage of goods value, default 1.5)
        customs_brokerage: Flat customs brokerage fee per shipment (default $150)
        domestic_delivery: Domestic delivery cost (default $0 — often included in freight quote)
        defect_rate: Expected defect rate (percentage, default 4)
        shipping_cost_override: Override calculated shipping with actual quote (total, not per unit)

    Returns:
        dict with full cost breakdown
    """
    # Validate shipping method
    if shipping_method not in SHIPPING_RATES and shipping_cost_override is None:
        raise ValueError(f"Unknown shipping method: {shipping_method}. Options: {', '.join(SHIPPING_RATES.keys())}")

    # --- Product Cost ---
    total_product_cost = product_cost * quantity

    # --- FX Spread ---
    fx_cost = total_product_cost * (fx_spread / 100)

    # --- Shipping ---
    total_weight_kg = weight_per_unit_kg * quantity

    if shipping_cost_override is not None:
        total_shipping = shipping_cost_override
        shipping_info = {"method": "custom", "name": "Custom (user-provided)", "notes": "User provided actual shipping quote"}
    else:
        method = SHIPPING_RATES[shipping_method]
        # Check weight limit
        if method["max_weight_kg"] and total_weight_kg > method["max_weight_kg"]:
            print(f"Warning: Total weight ({total_weight_kg:.1f}kg) exceeds {method['name']} "
                  f"limit of {method['max_weight_kg']}kg. Consider a different shipping method.")

        total_shipping = method["base_fee"] + (total_weight_kg * method["rate_per_kg"])
        shipping_info = {
            "method": shipping_method,
            "name": method["name"],
            "total_weight_kg": round(total_weight_kg, 2),
            "rate_per_kg": method["rate_per_kg"],
            "base_fee": method["base_fee"],
            "notes": method["notes"],
        }

    # --- Customs Duties ---
    # Dutiable value = product cost + freight + insurance
    dutiable_value = total_product_cost + total_shipping
    insurance_cost = total_product_cost * (insurance_rate / 100)
    dutiable_value += insurance_cost

    base_duty = dutiable_value * (duty_rate / 100)
    section_301_duty = dutiable_value * (section_301_rate / 100)
    total_duties = base_duty + section_301_duty

    # Check de minimis
    de_minimis = total_product_cost < 800
    if de_minimis and duty_rate > 0:
        print(f"Note: Order value (${total_product_cost:.2f}) is under $800 de minimis threshold. "
              f"Duties may not apply for individual parcels, but will apply for consolidated freight shipments.")

    # --- Payment Fee ---
    payment_cost = total_product_cost * (payment_fee / 100)

    # --- Defect Buffer ---
    defect_cost = total_product_cost * (defect_rate / 100)
    sellable_units = int(quantity * (1 - defect_rate / 100))

    # --- Total Landed Cost ---
    total_landed = (
        total_product_cost
        + fx_cost
        + total_shipping
        + total_duties
        + customs_brokerage
        + domestic_delivery
        + payment_cost
        + insurance_cost
        + defect_cost
    )

    per_unit_landed = total_landed / quantity
    per_unit_landed_adjusted = total_landed / sellable_units if sellable_units > 0 else 0

    # Multiplier from listing price
    multiplier = per_unit_landed / product_cost if product_cost > 0 else 0
    multiplier_adjusted = per_unit_landed_adjusted / product_cost if product_cost > 0 else 0

    result = {
        "input": {
            "product_cost_per_unit": product_cost,
            "quantity": quantity,
            "weight_per_unit_kg": weight_per_unit_kg,
            "total_weight_kg": round(total_weight_kg, 2),
            "shipping_method": shipping_info,
            "duty_rate": duty_rate,
            "section_301_rate": section_301_rate,
            "defect_rate": defect_rate,
        },
        "cost_breakdown": {
            "product_total": round(total_product_cost, 2),
            "fx_spread": round(fx_cost, 2),
            "shipping": round(total_shipping, 2),
            "customs_base_duty": round(base_duty, 2),
            "customs_section_301": round(section_301_duty, 2),
            "customs_total": round(total_duties, 2),
            "customs_brokerage": round(customs_brokerage, 2),
            "domestic_delivery": round(domestic_delivery, 2),
            "payment_fee": round(payment_cost, 2),
            "insurance": round(insurance_cost, 2),
            "defect_buffer": round(defect_cost, 2),
        },
        "summary": {
            "total_landed_cost": round(total_landed, 2),
            "per_unit_landed": round(per_unit_landed, 2),
            "per_unit_landed_defect_adjusted": round(per_unit_landed_adjusted, 2),
            "sellable_units": sellable_units,
            "multiplier_from_listing_price": round(multiplier, 2),
            "multiplier_defect_adjusted": round(multiplier_adjusted, 2),
            "de_minimis_applies": de_minimis,
        },
    }

    return result


def print_report(result: dict):
    """Print a human-readable landed cost report."""
    inp = result["input"]
    costs = result["cost_breakdown"]
    summary = result["summary"]

    print("\n" + "=" * 60)
    print("  LANDED COST CALCULATOR")
    print("=" * 60)

    print(f"\n  Product Cost/Unit:    ${inp['product_cost_per_unit']:.2f}")
    print(f"  Quantity:             {inp['quantity']} units")
    print(f"  Weight/Unit:          {inp['weight_per_unit_kg']:.2f} kg ({inp['total_weight_kg']:.1f} kg total)")
    print(f"  Shipping Method:      {inp['shipping_method']['name']}")
    if inp["duty_rate"] > 0:
        print(f"  Duty Rate:            {inp['duty_rate']}%")
    if inp["section_301_rate"] > 0:
        print(f"  Section 301 Rate:     {inp['section_301_rate']}%")
    print(f"  Defect Rate:          {inp['defect_rate']}%")

    print(f"\n--- Cost Breakdown ---")
    print(f"  Product Cost:         ${costs['product_total']:.2f}")
    print(f"  FX Spread:            ${costs['fx_spread']:.2f}")
    print(f"  Shipping:             ${costs['shipping']:.2f}")
    if costs["customs_total"] > 0:
        print(f"  Customs (base):       ${costs['customs_base_duty']:.2f}")
        if costs["customs_section_301"] > 0:
            print(f"  Customs (Sec 301):    ${costs['customs_section_301']:.2f}")
        print(f"  Customs (total):      ${costs['customs_total']:.2f}")
    print(f"  Customs Brokerage:    ${costs['customs_brokerage']:.2f}")
    if costs["domestic_delivery"] > 0:
        print(f"  Domestic Delivery:    ${costs['domestic_delivery']:.2f}")
    print(f"  Payment Fee:          ${costs['payment_fee']:.2f}")
    print(f"  Insurance:            ${costs['insurance']:.2f}")
    print(f"  Defect Buffer:        ${costs['defect_buffer']:.2f}")

    print(f"\n--- Summary ---")
    print(f"  Total Landed Cost:    ${summary['total_landed_cost']:.2f}")
    print(f"  Per Unit:             ${summary['per_unit_landed']:.2f}")
    print(f"  Per Unit (adj):       ${summary['per_unit_landed_defect_adjusted']:.2f} (based on {summary['sellable_units']} sellable units)")
    print(f"  Multiplier:           {summary['multiplier_from_listing_price']:.2f}x listing price")
    print(f"  Multiplier (adj):     {summary['multiplier_defect_adjusted']:.2f}x listing price")
    if summary["de_minimis_applies"]:
        print(f"\n  Note: Order value under $800 — de minimis may apply (no duties on individual parcels)")

    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Calculate true landed cost for China-sourced products",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Basic calculation (200 units, air freight):
    %(prog)s --product-cost 4.20 --quantity 200 --weight-kg 0.5

  With customs duties and Section 301 tariffs:
    %(prog)s --product-cost 4.20 --quantity 200 --weight-kg 0.5 \\
        --duty-rate 3.9 --section-301 7.5

  Small AliExpress test order:
    %(prog)s --product-cost 2.50 --quantity 10 --weight-kg 0.1 \\
        --shipping-method aliexpress_standard --duty-rate 0

  With actual shipping quote:
    %(prog)s --product-cost 4.20 --quantity 200 --weight-kg 0.5 \\
        --shipping-override 580.00

  JSON output:
    %(prog)s --product-cost 4.20 --quantity 200 --weight-kg 0.5 --json

Shipping methods:
  aliexpress_standard  AliExpress Standard / ePacket (1-10 units)
  air_parcel           Air Parcel small batch (10-50 units)
  air_freight          Air Freight cargo (50-500 units, default)
  sea_lcl              Sea Freight LCL (200+ units, slow)
  sea_fcl              Sea Freight FCL 20ft (2000+ units, slowest)
  express_dhl          Express DHL/FedEx/UPS (urgent/high-value)
        """,
    )

    parser.add_argument("--product-cost", type=float, required=True, help="Per-unit cost from supplier")
    parser.add_argument("--quantity", type=int, required=True, help="Number of units ordered")
    parser.add_argument("--weight-kg", type=float, required=True, help="Weight per unit in kilograms")
    parser.add_argument("--shipping-method", type=str, default="air_freight",
                       choices=list(SHIPPING_RATES.keys()),
                       help="Shipping method (default: air_freight)")
    parser.add_argument("--shipping-override", type=float, default=None,
                       help="Override with actual shipping quote (total, not per unit)")
    parser.add_argument("--duty-rate", type=float, default=0.0, help="Base customs duty rate (%%, default: 0)")
    parser.add_argument("--section-301", type=float, default=0.0, help="Section 301 tariff rate (%%, default: 0)")
    parser.add_argument("--fx-spread", type=float, default=DEFAULT_FX_SPREAD,
                       help=f"FX conversion spread (%%, default: {DEFAULT_FX_SPREAD})")
    parser.add_argument("--payment-fee", type=float, default=DEFAULT_PAYMENT_FEE,
                       help=f"Payment platform fee (%%, default: {DEFAULT_PAYMENT_FEE})")
    parser.add_argument("--defect-rate", type=float, default=DEFAULT_DEFECT_RATE,
                       help=f"Expected defect rate (%%, default: {DEFAULT_DEFECT_RATE})")
    parser.add_argument("--customs-brokerage", type=float, default=DEFAULT_CUSTOMS_BROKERAGE,
                       help=f"Customs brokerage fee (flat, default: ${DEFAULT_CUSTOMS_BROKERAGE})")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    result = calculate_landed_cost(
        product_cost=args.product_cost,
        quantity=args.quantity,
        weight_per_unit_kg=args.weight_kg,
        shipping_method=args.shipping_method,
        duty_rate=args.duty_rate,
        section_301_rate=args.section_301,
        fx_spread=args.fx_spread,
        payment_fee=args.payment_fee,
        defect_rate=args.defect_rate,
        customs_brokerage=args.customs_brokerage,
        shipping_cost_override=args.shipping_override,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_report(result)


if __name__ == "__main__":
    main()
