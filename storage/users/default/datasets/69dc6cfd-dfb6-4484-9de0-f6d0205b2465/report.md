# AutoStat Prep — Normalization Report

**Dataset ID:** 69dc6cfd-dfb6-4484-9de0-f6d0205b2465
**Dataset Hash:** cb91b95cf059ad0b871c01800c128f16c4e812121820e4cad5110aed2dcc1f6e
**Generated:** 2026-03-09 12:40:10 UTC
**Pipeline version:** Sprint-5

---

## Summary

| Field | Value |
|---|---|
| Row Count | 2 |
| Column Count | 2 |
| Resolvers Applied | 1 |

---

## Column Inventory

| # | Column Name | Inferred Type | Missing Ratio | Unique Values |
|---|---|---|---|---|
| 1 | id | TEXT | 0.0000 | 2 |
| 2 | rate | TEXT | 0.0000 | 2 |

---

## Transformations Applied

| Resolver | Details | Rows | Columns | Affected Columns |
|---|---|---|---|---|
| PercentResolver | Converted percent strings to decimal values | 2→2 | 2→2 | rate |


---

## Notes

- Column types inferred as `TEXT`. Full type inference arrives in Sprint-3.
- Audit trail records pipeline version for reproducibility.
