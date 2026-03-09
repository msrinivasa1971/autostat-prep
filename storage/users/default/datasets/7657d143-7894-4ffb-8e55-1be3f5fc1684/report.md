# AutoStat Prep — Normalization Report

**Dataset ID:** 7657d143-7894-4ffb-8e55-1be3f5fc1684
**Dataset Hash:** 970d3b61363a5a38a6ad53afcd6821ec46f507087e8134b17dd482dbfab26bd6
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
| 2 | age | TEXT | 0.0000 | 3 |
| 3 | score | TEXT | 0.0000 | 3 |
| 4 | category | TEXT | 0.0000 | 2 |

---

## Transformations Applied

| Resolver | Details | Rows | Columns | Affected Columns |
|---|---|---|---|---|
| NumericTextResolver | Converted numeric text to numeric dtype | 3→3 | 4→4 | age, score |


---

## Notes

- Column types inferred as `TEXT`. Full type inference arrives in Sprint-3.
- Audit trail records pipeline version for reproducibility.
