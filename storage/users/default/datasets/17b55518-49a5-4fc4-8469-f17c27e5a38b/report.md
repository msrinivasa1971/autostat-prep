# AutoStat Prep — Normalization Report

**Dataset ID:** 17b55518-49a5-4fc4-8469-f17c27e5a38b
**Dataset Hash:** d0f6b29a66a3467a18e6a78db3648c72f70ec57fa9e26c2989a613a3b95832da
**Generated:** 2026-03-09 12:07:38 UTC
**Pipeline version:** Sprint-5

---

## Summary

| Field | Value |
|---|---|
| Row Count | 2 |
| Column Count | 2 |
| Resolvers Applied | 2 |

---

## Column Inventory

| # | Column Name | Inferred Type | Missing Ratio | Unique Values |
|---|---|---|---|---|
| 1 | id | TEXT | 0.0000 | 2 |
| 2 | score | TEXT | 0.0000 | 2 |

---

## Transformations Applied

| Resolver | Details | Rows | Columns | Affected Columns |
|---|---|---|---|---|
| BlankRowResolver | Removed rows where all values were blank | 3→2 | 2→2 | N/A |
| NumericTextResolver | Converted numeric text to numeric dtype | 2→2 | 2→2 | score |


---

## Notes

- Column types inferred as `TEXT`. Full type inference arrives in Sprint-3.
- Audit trail records pipeline version for reproducibility.
