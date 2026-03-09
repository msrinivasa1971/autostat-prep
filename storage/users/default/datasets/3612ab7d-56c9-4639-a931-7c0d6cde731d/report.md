# AutoStat Prep — Normalization Report

**Dataset ID:** 3612ab7d-56c9-4639-a931-7c0d6cde731d
**Dataset Hash:** a58b16d1781231866a7f40486f991536b14aea091ffb9c5e49166135ddf92cf9
**Generated:** 2026-03-09 12:07:38 UTC
**Pipeline version:** Sprint-5

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
