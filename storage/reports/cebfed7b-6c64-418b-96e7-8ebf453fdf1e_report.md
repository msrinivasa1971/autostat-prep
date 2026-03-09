# AutoStat Prep — Normalization Report

**Dataset ID:** cebfed7b-6c64-418b-96e7-8ebf453fdf1e
**Generated:** 2026-03-08 18:58:19 UTC
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
| 2 | tags_alpha | TEXT | 0.0000 | 2 |
| 3 | tags_beta | TEXT | 0.0000 | 2 |
| 4 | tags_gamma | TEXT | 0.0000 | 2 |

---

## Transformations Applied

| Resolver | Details | Rows | Columns | Affected Columns |
|---|---|---|---|---|
| DelimitedListResolver | Expanded comma-delimited list columns into binary indicator columns | 3→3 | 2→4 | tags |


---

## Notes

- Column types inferred as `TEXT`. Full type inference arrives in Sprint-3.
- Audit trail records pipeline version for reproducibility.
