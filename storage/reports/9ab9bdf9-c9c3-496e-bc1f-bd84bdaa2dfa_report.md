# AutoStat Prep — Normalization Report

**Dataset ID:** 9ab9bdf9-c9c3-496e-bc1f-bd84bdaa2dfa
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
| 2 | score | TEXT | 0.6667 | 1 |

---

## Transformations Applied

| Resolver | Details | Rows | Columns | Affected Columns |
|---|---|---|---|---|
| NumericTextResolver | Converted numeric text to numeric dtype | 3→3 | 2→2 | id |
| MissingValueResolver | Normalized missing value indicators to NaN | 3→3 | 2→2 | score |


---

## Notes

- Column types inferred as `TEXT`. Full type inference arrives in Sprint-3.
- Audit trail records pipeline version for reproducibility.
