# AutoStat Prep — Normalization Report

**Dataset ID:** c05d27e2-91df-4a07-93e7-cf4052f09783
**Dataset Hash:** cb91b95cf059ad0b871c01800c128f16c4e812121820e4cad5110aed2dcc1f6e
**Generated:** 2026-03-09 12:07:38 UTC
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
