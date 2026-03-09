# AutoStat Prep — Normalization Report

**Dataset ID:** 8dd67b78-0e48-4fb4-87b2-cba9aa40194a
**Dataset Hash:** 6d5fa923ddbc474cfce45ecdf41b2a6115a674fad19a86bad094ffd174839aa5
**Generated:** 2026-03-09 12:07:38 UTC
**Pipeline version:** Sprint-5

---

## Summary

| Field | Value |
|---|---|
| Row Count | 2 |
| Column Count | 3 |
| Resolvers Applied | 3 |

---

## Column Inventory

| # | Column Name | Inferred Type | Missing Ratio | Unique Values |
|---|---|---|---|---|
| 1 | project_score | TEXT | 0.0000 | 2 |
| 2 | q2 | TEXT | 0.0000 | 2 |
| 3 | project_score_2 | TEXT | 0.0000 | 2 |

---

## Transformations Applied

| Resolver | Details | Rows | Columns | Affected Columns |
|---|---|---|---|---|
| HeaderNormalizerResolver | Normalized column names to lowercase_with_underscores | 2→2 | 3→3 | N/A |
| DuplicateColumnResolver | Renamed duplicate column names with numeric suffixes | 2→2 | 3→3 | N/A |
| NumericTextResolver | Converted numeric text to numeric dtype | 2→2 | 3→3 | project_score, q2, project_score_2 |


---

## Notes

- Column types inferred as `TEXT`. Full type inference arrives in Sprint-3.
- Audit trail records pipeline version for reproducibility.
