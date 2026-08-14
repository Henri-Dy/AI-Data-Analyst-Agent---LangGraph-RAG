---
title: Data Access Policy
---

# Data Access Policy

All analytical access to the operational database is **read-only**. No
agent or automated process is permitted to execute `INSERT`, `UPDATE`,
`DELETE`, `ALTER`, `DROP`, `TRUNCATE`, or `CREATE` statements against the
business schema.

Customer personally identifiable information (PII) is limited to `email`
and, where available, `phone`. These fields must never be included in
aggregate reports or visualizations; only used internally for row-level
lookups when explicitly required. Missing `phone` values are expected for
a portion of the customer base and should not be treated as a data error.

Query results are capped in row count and execution time to protect
database performance; analyses requiring more granular data than the cap
allows should aggregate in SQL rather than pulling raw rows.
