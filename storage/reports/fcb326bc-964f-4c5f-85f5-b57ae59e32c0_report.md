# AutoStat Prep — Normalization Report

**Dataset ID:** fcb326bc-964f-4c5f-85f5-b57ae59e32c0
**Generated:** 2026-03-08 18:34:41 UTC
**Pipeline version:** Sprint-2

---

## Summary

| Field | Value |
|---|---|
| Row Count | 3 |
| Column Count | 4 |
| Resolvers Applied | 1 |

---

## Column Inventory

| # | Column Name | Inferred Type | Missing Ratio | Unique Values |
|---|---|---|---|---|
| 1 | id | TEXT | 0.0000 | 3 |
| 2 | age | TEXT | 0.0000 | 3 |
| 3 | score | TEXT | 0.0000 | 3 |
| 4 | category | TEXT | 0.0000 | 2 |

---

## Transformations Applied

| Resolver | Details | Rows | Columns | Affected Columns |
|---|---|---|---|---|
| NumericTextResolver | Converted numeric text to numeric dtype | 3→3 | 4→4 | age, score |


---

## Notes

- Column types inferred as `TEXT`. Full type inference arrives in Sprint-3.
- Audit trail records pipeline version for reproducibility.
