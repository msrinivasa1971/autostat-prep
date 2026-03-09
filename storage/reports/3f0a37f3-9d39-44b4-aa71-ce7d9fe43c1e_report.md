# AutoStat Prep — Normalization Report

**Dataset ID:** 3f0a37f3-9d39-44b4-aa71-ce7d9fe43c1e
**Dataset Hash:** 78d5c8e2fe453c2cbc40c9b6f3fdb12b27f35a04cdeeced0c4bf0baf8a8b7a4f
**Generated:** 2026-03-09 11:16:32 UTC
**Pipeline version:** Sprint-5

---

## Summary

| Field | Value |
|---|---|
| Row Count | 3 |
| Column Count | 3 |
| Resolvers Applied | 2 |

---

## Column Inventory

| # | Column Name | Inferred Type | Missing Ratio | Unique Values |
|---|---|---|---|---|
| 1 | id | TEXT | 0.0000 | 3 |
| 2 | q1 | TEXT | 0.3333 | 2 |
| 3 | q2 | TEXT | 0.3333 | 1 |

---

## Transformations Applied

| Resolver | Details | Rows | Columns | Affected Columns |
|---|---|---|---|---|
| HeaderNormalizerResolver | Normalized column names to lowercase_with_underscores | 3→3 | 3→3 | N/A |
| CarryForwardResolver | Converted survey routing artifacts to NaN | 3→3 | 3→3 | q1, q2 |


---

## Notes

- Column types inferred as `TEXT`. Full type inference arrives in Sprint-3.
- Audit trail records pipeline version for reproducibility.
