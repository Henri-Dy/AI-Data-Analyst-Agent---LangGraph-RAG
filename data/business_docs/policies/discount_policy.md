---
title: Discount Policy
---

# Discount Policy

Standard discounts range from 5% to 30% (`order_items.discount_pct`) and
are applied at the discretion of the sales channel:

- **Online** discounts are typically promotional and broad-based (e.g.
  seasonal sales), which is why online revenue can spike sharply on
  specific days (flash sales) — these spikes are expected anomalies, not
  data errors.
- **Retail and phone** discounts are typically negotiated per order and
  more common for `smb` and `enterprise` customers placing larger orders.

Discount rates above 30% require director-level approval and are rare in
the data; when observed, they usually indicate an enterprise deal, a
clearance of discontinued (`is_active = false`) inventory, or a data entry
anomaly worth flagging.
