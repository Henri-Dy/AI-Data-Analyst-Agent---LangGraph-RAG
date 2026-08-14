---
title: KPI Definitions
---

# KPI Definitions

Standard formulas for the KPIs the Insight Agent is expected to reference.
Every reported number must be traceable back to one of these definitions.

**Revenue** = `SUM(quantity * unit_price * (1 - discount_pct))` over
`order_items`, restricted to orders with `status = 'completed'`.

**Gross Profit** = `Revenue - SUM(quantity * product.cost)` over the same
completed order items.

**Gross Margin %** = `Gross Profit / Revenue * 100`.

**Average Order Value (AOV)** = `Revenue / COUNT(DISTINCT completed orders)`.

**Units Sold** = `SUM(quantity)` over completed order items.

**Growth Rate (MoM)** = `(Revenue_this_month - Revenue_last_month) /
Revenue_last_month * 100`.

**Growth Rate (YoY)** = `(Revenue_this_period - Revenue_same_period_last_year)
/ Revenue_same_period_last_year * 100`.

**Discount Rate** = the revenue-weighted average of `discount_pct` across
order items — high discount rates can explain revenue softness even when
unit volume is stable.

**Cancellation Rate** = `COUNT(orders WHERE status = 'cancelled') /
COUNT(all orders)` for a given period.

**Refund Rate** = `COUNT(orders WHERE status = 'refunded') /
COUNT(orders WHERE status IN ('completed', 'refunded'))`.
