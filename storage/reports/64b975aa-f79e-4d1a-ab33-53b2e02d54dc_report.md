# AutoStat Prep — Normalization Report

**Dataset ID:** 64b975aa-f79e-4d1a-ab33-53b2e02d54dc
**Dataset Hash:** 5a4bab2e81b4bf7a432112b98547464abfa70fc50b51ea16699ccdc9c93bdba7
**Generated:** 2026-03-09 11:42:58 UTC
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
| 2 | satisfaction | TEXT | 0.0000 | 3 |

---

## Transformations Applied

| Resolver | Details | Rows | Columns | Affected Columns |
|---|---|---|---|---|
| LikertScaleResolver | Converted Likert scale to numeric (1–5) | 3→3 | 2→2 | satisfaction |


---

## Notes

- Column types inferred as `TEXT`. Full type inference arrives in Sprint-3.
- Audit trail records pipeline version for reproducibility.
