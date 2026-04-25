# Reconciliation Methodology

This project validates reporting logic by building the same curated outputs through two independent paths:

- Python/Pandas
- SQLite SQL

Both paths start from the same raw Olist CSV files. The comparison layer validates whether the two paths agree on the major business metrics and monthly revenue totals.

## Why Reconcile Two Paths?

BI teams often use more than one tool across a reporting workflow. Python may be used for profiling and data preparation, SQL may be used for production reporting logic, and BI tools may consume the final curated outputs.

This project uses two paths to demonstrate:

- business logic can be implemented consistently across tools;
- metric definitions are explicit enough to reproduce;
- reporting outputs are tested before dashboarding;
- revenue checks are included, not just row counts.

## Validation Tolerance

Metric differences are allowed only within a tolerance of 0.05.

This tolerance accounts for harmless decimal representation differences while still catching meaningful business reporting mismatches.

## Metric Checks

The comparison script validates 14 metrics:

| Metric | Python value | SQL value | Status |
| --- | ---: | ---: | --- |
| Total orders | 99,441 | 99,441 | Pass |
| Delivered orders | 96,478 | 96,478 | Pass |
| Late delivery count | 7,826 | 7,826 | Pass |
| Missing product category count | 1,627 | 1,627 | Pass |
| Unique customers | 96,096 | 96,096 | Pass |
| Unique sellers | 3,095 | 3,095 | Pass |
| Data quality issue count | 2,440 | 2,440 | Pass |
| Payment variance order count | 1,033 | 1,033 | Pass |
| Item price revenue | 13,591,643.70 | 13,591,643.70 | Pass |
| Freight revenue | 2,251,909.54 | 2,251,909.54 | Pass |
| Total revenue | 15,843,553.24 | 15,843,553.24 | Pass |
| Payment revenue | 16,008,872.12 | 16,008,872.12 | Pass |
| Payment/order variance total | 165,318.88 | 165,318.88 | Pass |
| Average order value | 159.33 | 159.33 | Pass |

## Monthly Revenue Checks

The comparison script also validates monthly total revenue for all 25 purchase months in `monthly_kpi_summary`.

Result:

- 25 monthly revenue checks passed.
- 0 monthly revenue checks required review.

Output file:

`data/validation_outputs/monthly_python_sql_revenue_comparison.csv`

## Output Files

| Output | Purpose |
| --- | --- |
| `python_sql_comparison_summary.csv` | Metric-by-metric comparison between Python and SQL |
| `monthly_python_sql_revenue_comparison.csv` | Month-by-month revenue comparison between Python and SQL |
| `reconciliation_summary.csv` | Pass/review totals for metric checks and monthly checks |
| `revenue_validation_checks.svg` | Visual table showing revenue-related metric checks |
| `validation_summary.svg` | Visual summary of pass/review counts |

## Completed Result

The completed run passed:

- 14 of 14 Python-vs-SQL metric checks.
- 25 of 25 monthly revenue checks.

This means Project 4 can use the curated Project 3 outputs with confidence.
