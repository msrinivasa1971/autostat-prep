# AutoStat Prep — Normalization Report

**Dataset ID:** 60faef88-ecdd-46b1-a84f-f5cedac33506
**Generated:** 2026-03-08 18:09:09 UTC
**Pipeline version:** Sprint-2

---

## Summary

| Field | Value |
|---|---|
| Row Count | 3 |
| Column Count | 4 |
| Resolvers Applied | 2 |

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
| LikertScaleResolver | Converted Likert scale to numeric (1–5) | 3→3 | 4→4 | category |
| NumericTextResolver | Converted numeric text to numeric dtype | 3→3 | 4→4 | id, age, score |


---

## Notes

- Column types inferred as `TEXT`. Full type inference arrives in Sprint-3.
- Audit trail records pipeline version for reproducibility.
