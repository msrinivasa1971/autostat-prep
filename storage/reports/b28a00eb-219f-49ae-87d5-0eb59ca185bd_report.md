# AutoStat Prep — Normalization Report

**Dataset ID:** b28a00eb-219f-49ae-87d5-0eb59ca185bd
**Generated:** 2026-03-08 18:08:39 UTC
**Pipeline version:** Sprint-2

---

## Summary

| Field | Value |
|---|---|
| Row Count | 3 |
| Column Count | 2 |
| Resolvers Applied | 2 |

---

## Column Inventory

| # | Column Name | Inferred Type | Missing Ratio | Unique Values |
|---|---|---|---|---|
| 1 | id | TEXT | 0.0000 | 3 |
| 2 | score | TEXT | 0.0000 | 3 |

---

## Transformations Applied

| Resolver | Details | Rows | Columns | Affected Columns |
|---|---|---|---|---|
| BlankColumnResolver | Removed columns where all values were blank | 3→3 | 3→2 | N/A |
| NumericTextResolver | Converted numeric text to numeric dtype | 3→3 | 2→2 | id, score |


---

## Notes

- Column types inferred as `TEXT`. Full type inference arrives in Sprint-3.
- Audit trail records pipeline version for reproducibility.
