# AutoStat Prep — Normalization Report

**Dataset ID:** cbbf2cc1-15da-4577-9f21-b1eb1a6aa5a8
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
| 2 | tools_asana | TEXT | 0.0000 | 2 |
| 3 | tools_jira | TEXT | 0.0000 | 2 |
| 4 | tools_trello | TEXT | 0.0000 | 2 |

---

## Transformations Applied

| Resolver | Details | Rows | Columns | Affected Columns |
|---|---|---|---|---|
| MultiSelectResolver | Expanded multi-select columns into binary indicator columns | 3→3 | 2→4 | tools |


---

## Notes

- Column types inferred as `TEXT`. Full type inference arrives in Sprint-3.
- Audit trail records pipeline version for reproducibility.
