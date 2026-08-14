---
title: Data Dictionary
---

# Data Dictionary

A plain-language description of the tables available for analysis. This
complements the live database schema inspection performed by the Schema
Agent — use it to understand *what the data means*, not just its column
types.

**regions** — The six sales regions the company operates in. Every
customer, employee, and order references one region.

**employees** — Sales staff. Each employee has a `role`
(`Sales Rep`, `Account Manager`, or `Sales Director`) and belongs to one
region. Employees are the ones "credited" with an order via `employee_id`
on the `orders` table.

**customers** — End customers. Each customer has a `segment`
(`consumer`, `smb`, or `enterprise`) and a home `region`. Some customers
have no `phone` on file — this is expected, real-world missing data, not
a data quality bug.

**products** — The product catalog. Each product belongs to a `category`
and `subcategory`, has a `unit_price` and internal `cost`, and an
`is_active` flag — inactive products are discontinued and should generally
be excluded from "current catalog" analyses, though their historical sales
remain in `order_items`.

**orders** — One row per customer order. Key fields: `order_date`,
`status` (`completed`, `pending`, `cancelled`, `refunded`), `channel`
(`online`, `retail`, `phone`), and the `customer_id` / `employee_id` /
`region_id` it belongs to.

**order_items** — Line items within an order (an order can contain
multiple products). Revenue must always be computed from `order_items`
(joined to `orders`), never from `orders` alone, since `orders` has no
price information of its own.

**rag_documents** — Internal table backing the retrieval-augmented
generation system; it stores chunked business documentation and its vector
embeddings and is not itself a business dataset.
