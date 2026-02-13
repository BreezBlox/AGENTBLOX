# Landed Cost Formula

AliExpress-only policy: use AliExpress links and supplier flows for this workflow.
Any Alibaba/1688 mentions in this document are legacy reference context.

This document defines the complete methodology for calculating the true landed cost of a
product sourced from China for eBay resale. "Landed cost" means: the total cost to get one
sellable unit from the supplier's warehouse to your shipping station, ready to be listed
and shipped to a buyer.

The critical insight: **the AliExpress listing price is not your cost.** It's the starting
point of a cost stack that typically adds 40-150% on top of the listing price, depending on
the product, shipping method, and order quantity.

## The Complete Cost Stack

### Formula

```
Landed Cost Per Unit =
    (Product Cost Per Unit × (1 + FX Spread))
  + (Supplier-Side Shipping ÷ Units in Shipment)
  + (International Freight ÷ Units in Shipment)
  + (Customs Duties ÷ Units in Shipment)
  + (Customs Brokerage ÷ Units in Shipment)
  + (Domestic Delivery ÷ Units in Shipment)
  + (Payment Platform Fee as % of Product Cost)
  + (Insurance ÷ Units in Shipment)
  + (Quality Defect Buffer as % of Product Cost)
```

### Component Breakdown

#### 1. Product Cost Per Unit

**What it is:** The price you pay the supplier for one unit at your actual order quantity.

**Common mistake:** Using the 1-piece AliExpress price. This is almost always 30-100% higher
than the price you'd get at even modest wholesale quantities (50-100 units).

**How to get the real number:**
- AliExpress: The listed price IS your price for small orders. Check if there are tiered
  discounts (some listings show "Buy 3+: 10% off")
- Alibaba: Request a quote at your target order quantity. The first quote is negotiable —
  expect to land 10-20% below the initial quote
- 1688: Prices shown are the base. You'll need a sourcing agent to negotiate

#### 2. FX Conversion Spread (1-3%)

**What it is:** The hidden cost of converting USD to CNY (or vice versa) when paying
through PayPal, Alibaba Trade Assurance, or credit card.

**How it works:** The exchange rate you see on Google is the "mid-market rate." Payment
platforms add a 1-3% spread on top. PayPal's spread is typically 2.5-3%. Credit card
foreign transaction fees are typically 1-3%. Alibaba Trade Assurance has its own spread.

**Calculation:** Product Cost × FX Spread % = Additional cost
- Example: $3.50 product × 2.5% = $0.0875 additional cost per unit

#### 3. Supplier-Side Shipping

**What it is:** The cost for the supplier to get the goods from their factory/warehouse to
the shipping origin point (airport, port, or courier pickup).

**For AliExpress orders:** Usually included in the shipping price you see at checkout.
**For Alibaba orders:** Ask explicitly. Sometimes included in the FOB price, sometimes charged
separately. Common terms:
- **EXW (Ex Works):** Supplier's price is at their door. All shipping costs are yours
- **FOB (Free on Board):** Supplier gets it to the port. International freight is yours
- **CIF (Cost, Insurance, Freight):** Supplier pays to your destination port. You handle
  customs and domestic delivery

#### 4. International Freight (Per Unit)

**What it is:** The cost to move goods from China to your country. This is usually the
largest single cost component after the product itself.

**How to calculate per-unit:** Total freight cost ÷ number of units in shipment

**Reference:** See `references/shipping-lanes.md` for detailed method comparison and rates.

**Quick estimates for per-unit freight cost:**
| Shipping Method | Typical Per-Unit Cost (500g product) |
|----------------|-------------------------------------|
| AliExpress Standard (1 unit) | $3-8 |
| Air Parcel (50 units) | $1-3 |
| Air Freight (200 units) | $0.50-1.50 |
| Sea Freight LCL (500 units) | $0.20-0.80 |
| Sea Freight FCL (2000+ units) | $0.10-0.40 |

The per-unit cost drops dramatically with volume. This is why scaling matters for arbitrage economics.

#### 5. Customs Duties

**What it is:** Import taxes based on the product's HTS (Harmonized Tariff Schedule) classification.

**US De Minimis:** Individual shipments valued under $800 are generally duty-free. This is
why small AliExpress orders don't incur duties. But bulk orders above $800 are fully assessed.

**Calculation:**
```
Duty Amount = (Product Value + Freight + Insurance) × Duty Rate
Section 301 = (Product Value + Freight + Insurance) × Additional Tariff Rate
Total Duties = Duty Amount + Section 301
Per-Unit Duty = Total Duties ÷ Units in Shipment
```

**Section 301 Tariffs:** Additional tariffs specifically on Chinese goods, ranging from
7.5-25% depending on the product category. These are ON TOP of regular duty rates.

**How to find your duty rate:**
1. Identify the HTS code for your product at https://hts.usitc.gov/
2. Look up the "General" duty rate
3. Check if Section 301 applies (List 1-4A tariffs)
4. Add them together for total duty rate

#### 6. Customs Brokerage

**What it is:** Professional fees for handling customs clearance paperwork.

**When it applies:** For any shipment that requires formal customs entry (generally above
the $800 de minimis threshold or any freight shipment).

**Typical cost:** $50-200 per shipment (not per unit). Your freight forwarder often includes
this in their quote, but verify.

**Per-unit calculation:** Brokerage fee ÷ number of units. For a $150 brokerage fee on 200
units = $0.75 per unit.

#### 7. Domestic Delivery (Last Mile)

**What it is:** Getting the goods from the port/airport/customs to your location.

**For AliExpress/express orders:** Included in the shipping price — delivered to your door.
**For freight shipments:** A separate cost. Options:
- Pickup at port/warehouse: cheapest but requires transportation
- Drayage + domestic carrier: $100-500 depending on distance and weight
- Freight forwarder door delivery: usually included in their quote if you specified DDP
  (Delivered Duty Paid)

#### 8. Payment Platform Fee

**What it is:** The fee your payment platform charges for the transaction.

**Typical rates:**
- PayPal (goods & services): 2.9% + $0.30
- PayPal (friends & family): technically free but no buyer protection — risky for sourcing
- Alibaba Trade Assurance: ~3%
- Credit card: foreign transaction fee of 1-3% (on top of the FX spread)
- Wire transfer: $15-50 flat fee (cheaper for large orders, expensive for small ones)

**Calculation:** Payment fee = (Order total × Fee %) + Fixed fee, divided by number of units.

#### 9. Insurance

**What it is:** Coverage against loss or damage during transit.

**When it's worth it:** Orders over $500. The cost is typically 1-3% of the goods value.
**For small orders:** Usually not worth the cost. AliExpress buyer protection and PayPal
claims serve as informal insurance.

#### 10. Quality Defect Buffer

**What it is:** An allowance for the percentage of units that will be defective, damaged in
transit, or otherwise unsellable.

**Recommended buffer:** 3-5% of product cost, depending on product category and supplier reliability.

**Calculation:** If you order 100 units and expect 5% defects, your cost base is 100 units
but your sellable inventory is 95 units. The per-unit landed cost should be calculated
against 95 sellable units, not 100 ordered units.

**Alternative calculation:** Add 3-5% to the per-unit product cost upfront as a defect buffer.

## Worked Examples

### Example 1: AliExpress Small Order (10 units, phone case)

```
Product cost: $2.50 × 10 = $25.00
FX spread (2.5%): $0.63
AliExpress shipping: $3.00 per unit × 10 = $30.00
Customs duties: $0 (under $800 de minimis)
Payment fee (PayPal 2.9% + $0.30): $0.30 + $1.03 = $1.33

Total order cost: $56.96
Per-unit landed cost: $5.70
Markup from listing price: 2.28x the $2.50 listing price
```

### Example 2: Alibaba MOQ Order (200 units, LED light)

```
Product cost: $4.20 × 200 = $840.00 (negotiated from $5.00 list)
FX spread (2%): $16.80
Air freight (200 units, 100kg): $600.00
Customs duties (HTS duty 3.9% + Section 301 7.5% = 11.4%): $164.16
  Dutiable value: ($840 + $600) × 11.4%
Customs brokerage: $150.00
Domestic delivery (included in freight forwarder quote): $0
Payment fee (Trade Assurance 3%): $25.20
Insurance (1.5% of goods): $12.60
Quality defect buffer (4% of product cost): $33.60

Total order cost: $1,842.36
Per-unit landed cost: $9.21 (based on 200 units)
Per-unit landed cost adjusted for 4% defects: $9.59 (based on 192 sellable units)
Markup from listing price: 1.92x the $5.00 Alibaba listing price
```

### Example 3: Quick Multiplier Check

Don't have time for a full calculation? Use these rough multipliers:

| Source | Order Size | Rough Multiplier on Listing Price |
|--------|-----------|----------------------------------|
| AliExpress | 1-10 units | 2.0-2.5x |
| AliExpress | 10-50 units | 1.8-2.2x |
| Alibaba | MOQ (50-200) | 1.4-1.8x |
| Alibaba | 2-5x MOQ | 1.3-1.5x |
| 1688 | Via sourcing agent | 1.5-2.0x (agent fees offset lower base price) |

These are rough estimates. Always run the full calculation for any deal you're seriously
considering.

## Using the Landed Cost Calculator Script

For automated calculation, use `scripts/landed_cost.py`:

```bash
python scripts/landed_cost.py \
  --product-cost 4.20 \
  --quantity 200 \
  --weight-kg 0.5 \
  --shipping-method air_freight \
  --duty-rate 11.4 \
  --defect-rate 4
```

The script handles all the math including FX spread, platform fees, and defect-adjusted
per-unit costs. See the script's help output for all parameters.
