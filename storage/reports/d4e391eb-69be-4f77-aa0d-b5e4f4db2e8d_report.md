# AutoStat Prep — Normalization Report

**Dataset ID:** d4e391eb-69be-4f77-aa0d-b5e4f4db2e8d
**Dataset Hash:** 4bc0ab412048dbadd69f4e8361fe4dce083aaafcd9dd46918b49f065d76b1775
**Generated:** 2026-03-09 11:32:12 UTC
**Pipeline version:** Sprint-5

---

## Summary

| Field | Value |
|---|---|
| Row Count | 3 |
| Column Count | 2 |
| Resolvers Applied | 1 |

---

## Column Inventory

| # | Column Name | Inferred Type | Missing Ratio | Unique Values |
|---|---|---|---|---|
| 1 | id | TEXT | 0.0000 | 3 |
| 2 | agree | TEXT | 0.0000 | 2 |

---

## Transformations Applied

| Resolver | Details | Rows | Columns | Affected Columns |
|---|---|---|---|---|
| BooleanResolver | Converted boolean text to numeric (1/0) | 3→3 | 2→2 | agree |


---

## Notes

- Column types inferred as `TEXT`. Full type inference arrives in Sprint-3.
- Audit trail records pipeline version for reproducibility.
