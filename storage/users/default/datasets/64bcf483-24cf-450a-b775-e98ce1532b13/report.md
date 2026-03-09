# AutoStat Prep — Normalization Report

**Dataset ID:** 64bcf483-24cf-450a-b775-e98ce1532b13
**Dataset Hash:** da92843f77f1e002dce1ad6df8733e4eb46180d349fa68f840f52d24565fc9c5
**Generated:** 2026-03-09 12:40:10 UTC
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
| 2 | score | TEXT | 0.6667 | 1 |

---

## Transformations Applied

| Resolver | Details | Rows | Columns | Affected Columns |
|---|---|---|---|---|
| MissingValueResolver | Normalized missing value indicators to NaN | 3→3 | 2→2 | score |


---

## Notes

- Column types inferred as `TEXT`. Full type inference arrives in Sprint-3.
- Audit trail records pipeline version for reproducibility.
