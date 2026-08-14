---
title: Sales KPIs
---

# Sales KPIs

KPIs specific to sales performance analysis, used when a question is about
regions, segments, or products rather than overall company revenue.

**Revenue by Region** — Revenue attributed to the `region_id` of the
*order* (not the customer's home region, though in this business the two
coincide for the vast majority of orders since customers are served by
their local sales team).

**Revenue by Segment** — Revenue grouped by the ordering customer's
`segment` (`consumer`, `smb`, `enterprise`). Enterprise orders are fewer in
number but typically carry a higher average order value.

**Top Products by Revenue** — Products ranked by total revenue
contribution; in practice, revenue in this business is concentrated in a
small number of high-performing SKUs (a long-tail distribution), so "top 10
products" analyses typically explain a disproportionate share of total
revenue.

**Declining Products** — Products whose trailing revenue (e.g. last 3
months) is meaningfully lower than their prior trailing period, independent
of overall seasonality. A single slow month is not sufficient evidence of
decline; look for a sustained downward trend.

**Channel Mix** — The split of revenue across `online`, `retail`, and
`phone` channels. Online is the largest channel by volume.

**Sales Rep Attribution** — Every order is credited to the employee
(`Sales Rep`, `Account Manager`, or `Sales Director`) who owns the region it
was placed in; this is used for regional performance analysis, not
individual commission calculations.
