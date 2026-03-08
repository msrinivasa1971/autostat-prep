# AutoStat Prep — Normalization Report

**Dataset ID:** 0d3b7a4d-adf8-484b-9038-beba51749aef
**Generated:** 2026-03-08 17:54:11 UTC
**Pipeline version:** Sprint-2

---

## Summary

| Field | Value |
|---|---|
| Row Count | 2 |
| Column Count | 3 |
| Resolvers Applied | 2 |

---

## Column Inventory

| # | Column Name | Inferred Type | Missing Ratio | Unique Values |
|---|---|---|---|---|
| 1 | project_score | TEXT | 0.0000 | 2 |
| 2 | q2 | TEXT | 0.0000 | 2 |
| 3 | project_score_2 | TEXT | 0.0000 | 2 |

---

## Transformations Applied

| Resolver | Details | Rows | Columns |
|---|---|---|---|
| HeaderNormalizerResolver | Normalized column names to lowercase_with_underscores | 2→2 | 3→3 |
| DuplicateColumnResolver | Renamed duplicate column names with numeric suffixes | 2→2 | 3→3 |


---

## Notes

- Column types inferred as `TEXT`. Full type inference arrives in Sprint-3.
- Audit trail records pipeline version for reproducibility.
