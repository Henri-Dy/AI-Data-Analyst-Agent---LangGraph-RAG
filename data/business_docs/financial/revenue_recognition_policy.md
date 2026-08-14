---
title: Revenue Recognition Policy
---

# Revenue Recognition Policy

Revenue is recognized at the order level, not the shipment or payment
level, and only for orders in the `completed` status. This means:

- A `pending` order contributes nothing to reported revenue until it
  transitions to `completed`.
- A `cancelled` order never contributes to revenue, even if it was briefly
  `pending` beforehand.
- A `refunded` order is excluded from revenue entirely (it is not treated
  as revenue minus a refund line item) — this keeps historical revenue
  figures for a given month stable once the month closes, rather than
  fluctuating as refunds trickle in.

Discounts (`discount_pct` on `order_items`) are applied before revenue is
recognized — reported revenue is always net of discount, never gross list
price.

Any analysis that reports a revenue figure should state which order
statuses were included, so results remain auditable and reproducible.
