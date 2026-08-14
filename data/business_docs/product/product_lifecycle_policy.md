---
title: Product Lifecycle Policy
---

# Product Lifecycle Policy

Every product moves through the following lifecycle stages:

1. **Launch** — recorded as `launch_date`. New products typically ramp up
   in sales volume over their first 1–2 quarters as awareness grows.
2. **Active** — `is_active = true`. The product is sellable and appears in
   the current catalog.
3. **Declining** — sustained multi-month revenue decline for an otherwise
   active product. This is a normal part of the lifecycle and is the kind
   of pattern the "which products have declining sales?" analysis is meant
   to surface. A declining product is not automatically discontinued.
4. **Discontinued** — `is_active = false`. The product is removed from the
   active catalog but its historical order history is retained permanently
   for reporting and revenue reconciliation purposes.

Pricing changes over a product's lifetime are not retroactively applied to
historical orders: `order_items.unit_price` always reflects the price at
the time of sale, while `products.unit_price` reflects the current price.
