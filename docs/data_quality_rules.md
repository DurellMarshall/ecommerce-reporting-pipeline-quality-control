# Data Quality Rules

The data quality output is designed as a row-level exception log. Each issue includes a source table, record ID, field name, issue type, severity, and description.

Output files:

- Python: `data/curated_python/data_quality_issues.csv`
- SQL: `data/curated_sql/data_quality_issues.csv`

Both outputs produced 2,440 issue records in the completed run.

## Implemented Rules

| Rule | Severity | Logic | Completed count |
| --- | --- | --- | ---: |
| Missing Product Category | Medium | Product source category is missing or English translation is `unknown` | 623 |
| Delivered Order Missing Delivery Date | High | Order status is delivered but customer delivery timestamp is missing | 8 |
| Negative Delivery Days | Critical | Customer delivery timestamp is earlier than purchase timestamp | 0 |
| Payment Does Not Reconcile To Order Total | High | Absolute difference between payment total and item-plus-freight total exceeds 0.05 | 1,033 |
| Order Missing Item Detail | High | Order exists but has no matching order item rows | 775 |
| Duplicate Geolocation Rows | Low | Geolocation table has fully duplicate rows | 1 table-level issue |

## Why These Rules Matter

- Missing product categories affect category revenue and category mix reporting.
- Missing delivery timestamps affect delivery cycle time and late-delivery reporting.
- Negative delivery days would indicate invalid timestamp ordering.
- Payment variance highlights where payment data and item revenue do not reconcile directly.
- Missing item detail prevents complete revenue attribution.
- Duplicate geolocation rows can inflate downstream joins if the geography table is connected directly to facts.

## Dashboard Usage

Project 4 can use the issue log for a delivery risk and data quality monitor page. Recommended dashboard filters:

- Severity
- Issue type
- Source table
- Month
- Seller
- Product category

Payment variance should be explained carefully in the dashboard. It is a reconciliation exception, not automatically an accounting error, because payment rows may reflect operational payment behaviors such as vouchers or split payments.
