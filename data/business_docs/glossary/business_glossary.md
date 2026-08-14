---
title: Business Glossary
---

# Business Glossary

This glossary defines the core business terms used across analyses, reports,
and conversations with the AI Data Analyst.

**Revenue** — The total monetary value of completed sales, computed as
`quantity * unit_price * (1 - discount_pct)` summed across order line items.
Only orders with status `completed` count toward reported revenue; `pending`,
`cancelled`, and `refunded` orders are excluded.

**Gross Margin** — Revenue minus the cost of goods sold (COGS), expressed as
a percentage of revenue. COGS is derived from each product's `cost` field.

**AOV (Average Order Value)** — Total revenue divided by the number of
completed orders over a given period.

**MoM (Month-over-Month)** — The percentage change in a metric between the
current month and the immediately preceding month.

**YoY (Year-over-Year)** — The percentage change in a metric between the
current period and the same period one year earlier, used to separate real
trend movement from normal seasonality.

**Churn** — In this business, churn is approximated at the customer level as
customers with no completed orders in the trailing 90 days, relative to
customers active in the prior 90-day window.

**Segment** — Customers are classified into one of three segments:
`consumer` (individual buyers), `smb` (small and medium businesses), and
`enterprise` (large accounts, typically with dedicated account management
and higher average order values).

**Region** — The company operates across six sales regions: North America,
Europe, APAC, Latin America, Middle East & Africa, and Oceania. Every
customer, employee, and order is tied to exactly one region.

**Contribution Analysis** — A breakdown of how much each dimension (region,
product, segment, etc.) contributed to a change in a metric, typically
expressed as a percentage-point contribution to the overall change.

**Anomaly** — A data point (usually a single day or a short window) whose
value deviates sharply from the expected trend and seasonal pattern —
for example a flash-sale spike or a system outage causing near-zero orders.
