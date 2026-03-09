# AutoStat Prep — Normalization Report

**Dataset ID:** 50532203-90a6-48ee-8125-19b5a5c5748b
**Dataset Hash:** 3b296115ed2ccf797c9bf8d683ef44227d90ef7466ce9c81e47d4c62ea66d547
**Generated:** 2026-03-09 12:07:38 UTC
**Pipeline version:** Sprint-5

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
| 2 | score | TEXT | 0.0000 | 3 |

---

## Transformations Applied

| Resolver | Details | Rows | Columns | Affected Columns |
|---|---|---|---|---|
| BlankColumnResolver | Removed columns where all values were blank | 3→3 | 3→2 | N/A |
| NumericTextResolver | Converted numeric text to numeric dtype | 3→3 | 2→2 | score |


---

## Notes

- Column types inferred as `TEXT`. Full type inference arrives in Sprint-3.
- Audit trail records pipeline version for reproducibility.
