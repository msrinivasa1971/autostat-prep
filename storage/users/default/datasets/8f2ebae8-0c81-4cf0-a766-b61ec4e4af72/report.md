# AutoStat Prep — Normalization Report

**Dataset ID:** 8f2ebae8-0c81-4cf0-a766-b61ec4e4af72
**Dataset Hash:** b2457403642282bb9cdc7a672276a0c58ac34ddfe2375c3d4f4ec10709fefc73
**Generated:** 2026-03-09 12:07:38 UTC
**Pipeline version:** Sprint-5

---

## Summary

| Field | Value |
|---|---|
| Row Count | 2 |
| Column Count | 3 |
| Resolvers Applied | 2 |

---

## Column Inventory

| # | Column Name | Inferred Type | Missing Ratio | Unique Values |
|---|---|---|---|---|
| 1 | project_score | TEXT | 0.0000 | 2 |
| 2 | user_id | TEXT | 0.0000 | 2 |
| 3 | q1_answer | TEXT | 0.0000 | 2 |

---

## Transformations Applied

| Resolver | Details | Rows | Columns | Affected Columns |
|---|---|---|---|---|
| HeaderNormalizerResolver | Normalized column names to lowercase_with_underscores | 2→2 | 3→3 | N/A |
| NumericTextResolver | Converted numeric text to numeric dtype | 2→2 | 3→3 | project_score, q1_answer |


---

## Notes

- Column types inferred as `TEXT`. Full type inference arrives in Sprint-3.
- Audit trail records pipeline version for reproducibility.
