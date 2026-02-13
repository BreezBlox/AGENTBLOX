# eBay Fee Structure Reference

> **Staleness Warning:** eBay updates fees periodically (typically March and July). These
> figures reflect the general structure as of early 2025. Always verify current rates at
> https://www.ebay.com/help/selling/fees-credits-invoices/selling-fees?id=4364 before
> making final margin calculations. When in doubt, round fees UP by 1-2% to build in buffer.

## Fee Stack Overview

Every eBay sale incurs multiple fees. Most sellers only think about the Final Value Fee,
but the real cost is the sum of all layers:

```
Total eBay Cost = Final Value Fee
               + Payment Processing Fee
               + Promoted Listings Fee (if applicable)
               + International Fee (if applicable)
               + Insertion Fee (if over free allocation)
               + Regulatory Operating Fee (if applicable)
```

## 1. Final Value Fees (FVF)

Charged as a percentage of the total sale amount (item price + shipping). This is the big one.

### Standard Categories
| Category | FVF Rate | Notes |
|----------|---------|-------|
| Most categories (default) | 13.25% | Applied to total sale amount |
| Books, DVDs, Movies, Music | 14.95% | Higher than default |
| Business & Industrial | 12.35% | Slightly lower |
| Clothing, Shoes & Accessories | 12.35% | Lower tier |
| Collectibles | 13.25% | Standard |
| Computers & Tablets | 12.35% | Lower tier |
| Consumer Electronics | 12.35% | Lower tier |
| Cell Phones & Accessories | 12.35% | Lower tier — but accessories may differ |
| Health & Beauty | 13.25% | Standard |
| Home & Garden | 13.25% | Standard |
| Jewelry & Watches | 13.25% up to $7,500, 6.5% above | Tiered |
| Musical Instruments & Gear | 12.35% | Lower tier |
| Parts & Accessories (Auto) | 12.35% | Lower tier |
| Sporting Goods | 12.35% | Lower tier |
| Toys & Hobbies | 13.25% | Standard |
| Video Games & Consoles | 13.25% | Standard |

### Key FVF Details
- FVF applies to the **total amount of the sale** — that includes shipping charges the buyer pays
- For items selling over $7,500, a reduced rate applies to the amount above $7,500 (varies by category)
- Per-order fee of $0.30 applies to each transaction on top of the percentage
- Sellers with an eBay Store may get slightly lower rates depending on store tier

## 2. Payment Processing Fee

eBay Managed Payments processes all transactions. The fee is bundled into the Final Value Fee
structure for most sellers, but be aware:

- Standard payment processing: built into FVF rates shown above
- International payments: additional 1.65% (see International Fees below)
- The $0.30 per-order fee is the fixed payment processing component

## 3. Promoted Listings Fees

Promoted Listings Standard (cost-per-sale model):
- You set an ad rate (percentage of sale price)
- Fee is charged ONLY when a buyer clicks your promoted listing AND purchases
- Suggested rates vary by category (typically 2-12%)
- The fee is on TOP of the FVF — it's an additional cost

| Category | Typical Suggested Rate Range |
|----------|---------------------------|
| Electronics | 2-5% |
| Clothing | 4-8% |
| Home & Garden | 3-6% |
| Collectibles | 3-7% |
| Toys & Hobbies | 4-8% |
| Auto Parts | 2-5% |

Promoted Listings Advanced (cost-per-click model):
- Pay per click, regardless of conversion
- More complex — only for experienced sellers with significant volume
- Budget-based, not commission-based

**Margin Impact:** A 5% promoted listings rate on a 13.25% FVF category means you're paying
~18.55% in combined eBay fees before you count the per-order fee. This changes the math significantly.

## 4. International Fees

If you sell to international buyers:
- **International fee:** 1.65% of total sale amount
- Applied on top of FVF
- Applies whether you ship internationally directly or through eBay's Global Shipping Program

**eBay Global Shipping Program (GSP):**
- You ship to a US hub; eBay handles international shipping
- Buyer pays international shipping + import charges
- You pay domestic shipping to the hub + the 1.65% international fee
- Pro: no customs headaches. Con: buyer sees higher total price, which can reduce international sales

## 5. Insertion Fees

- You get a monthly allocation of free listings (varies by store tier)
- **No Store:** ~250 free listings/month
- **Starter Store:** ~250 free listings/month (but lower FVF rates)
- **Basic Store:** ~1,000 free listings/month
- **Premium Store:** ~10,000 free listings/month
- **Anchor Store:** ~25,000 free listings/month
- Beyond your free allocation: $0.35 per listing
- Auction-style listings may have different insertion fee structures

## 6. Store Subscription Costs

If the user has a store, factor in the monthly cost:

| Store Tier | Monthly (annual billing) | Monthly (month-to-month) |
|-----------|------------------------|-------------------------|
| Starter | ~$4.95/mo | ~$7.95/mo |
| Basic | ~$21.95/mo | ~$27.95/mo |
| Premium | ~$59.95/mo | ~$74.95/mo |
| Anchor | ~$299.95/mo | ~$349.95/mo |
| Enterprise | ~$2,999.95/mo | N/A |

Store subscriptions reduce FVF rates slightly and increase free listing allocations. The
breakeven point for a Basic Store is roughly 50-100 sales/month depending on average sale
price.

## 7. Additional Fees to Remember

- **Regulatory Operating Fee:** Some states/regions add a small regulatory fee (typically 0.25-0.50%)
- **Below Standard seller surcharge:** If your account falls below eBay's minimum performance
  standards, an additional 6% surcharge applies to all FVF. This is devastating to margins.
- **Very High "Item Not Received" surcharge:** Sellers with high INR rates may face additional fees

## Fee Calculation Example

Product sells for $30 with free shipping (seller pays $5 to ship):

```
Sale Price:                    $30.00
Final Value Fee (13.25%):      -$3.98
Per-order fee:                 -$0.30
Promoted Listings (5%):        -$1.50
Total eBay Fees:               -$5.78 (19.3% of sale price)

Seller receives:               $24.22
Minus shipping cost:           -$5.00
Net after fees + shipping:     $19.22

If COGS (landed) = $10:
Net Profit:                    $9.22
Net Margin:                    30.7% (of sale price)
ROI:                           61.5% (on COGS + shipping)
```

But add returns drag (8% return rate):
```
Returns cost (8% × $30):      -$2.40 per unit average
Adjusted Net Profit:           $6.82
Adjusted Net Margin:           22.7%
```

That's the real number. The "$30 sale, $10 cost = $20 profit" fantasy is actually $6.82
after the full fee stack and returns.
