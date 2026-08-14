---
title: Financial Definitions
---

# Financial Definitions

**Gross Revenue** — Total order-item revenue before any adjustment,
computed only from `completed` orders: `SUM(quantity * unit_price *
(1 - discount_pct))`.

**COGS (Cost of Goods Sold)** — `SUM(quantity * product.cost)` across the
same completed order items used for gross revenue.

**Gross Profit** — `Gross Revenue - COGS`.

**Discount Impact** — The revenue foregone due to discounting, computed as
`SUM(quantity * unit_price * discount_pct)`. This is useful when explaining
a revenue shortfall: a lower headline revenue can come from lower volume,
lower average price, or higher discounting — these are distinct root
causes and should not be conflated.

**Cancelled and Refunded Orders** — Orders with status `cancelled` or
`refunded` are excluded from all revenue and profit calculations. They are
tracked separately as `Cancellation Rate` and `Refund Rate` (see
`sales_kpis.md` / `kpi_definitions.md`) and can themselves be a symptom
worth investigating during a root-cause analysis.

**Pending Orders** — Orders with status `pending` represent revenue not
yet recognized; they should never be included in historical revenue
figures, only optionally surfaced as a forward-looking pipeline indicator.
