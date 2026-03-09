# AutoStat Prep — Normalization Report

**Dataset ID:** de61e3d6-449b-404b-b82c-fbcded00c3f4
**Generated:** 2026-03-09 10:50:58 UTC
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
