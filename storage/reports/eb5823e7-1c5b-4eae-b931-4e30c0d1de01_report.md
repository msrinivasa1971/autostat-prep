# AutoStat Prep — Normalization Report

**Dataset ID:** eb5823e7-1c5b-4eae-b931-4e30c0d1de01
**Generated:** 2026-03-08 17:53:49 UTC
**Pipeline version:** Sprint-2

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
| 2 | score | TEXT | 0.0000 | 2 |

---

## Transformations Applied

| Resolver | Details | Rows | Columns |
|---|---|---|---|
| BlankRowResolver | Removed rows where all values were blank | 3→2 | 2→2 |


---

## Notes

- Column types inferred as `TEXT`. Full type inference arrives in Sprint-3.
- Audit trail records pipeline version for reproducibility.
