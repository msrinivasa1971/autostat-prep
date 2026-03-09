# AutoStat Prep — Normalization Report

**Dataset ID:** f1df3192-9c03-4f4d-8343-4912f042dd8b
**Dataset Hash:** d0bcba47834b5e76c29d6146bf95fa20d92d31d781f000fa02910e79c8bbea1a
**Generated:** 2026-03-09 12:40:10 UTC
**Pipeline version:** Sprint-5

---

## Summary

| Field | Value |
|---|---|
| Row Count | 2 |
| Column Count | 2 |
| Resolvers Applied | 2 |

---

## Column Inventory

| # | Column Name | Inferred Type | Missing Ratio | Unique Values |
|---|---|---|---|---|
| 1 | project_score | TEXT | 0.0000 | 2 |
| 2 | user_id | TEXT | 0.0000 | 2 |

---

## Transformations Applied

| Resolver | Details | Rows | Columns | Affected Columns |
|---|---|---|---|---|
| HeaderNormalizerResolver | Normalized column names to lowercase_with_underscores | 2→2 | 2→2 | N/A |
| NumericTextResolver | Converted numeric text to numeric dtype | 2→2 | 2→2 | project_score |


---

## Notes

- Column types inferred as `TEXT`. Full type inference arrives in Sprint-3.
- Audit trail records pipeline version for reproducibility.
