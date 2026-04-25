# SQL Transition Journal

Status date: April 25, 2026

## Purpose

This journal documents the SQL path for Project 3. The goal is to show the same reporting logic implemented in SQL after the Python path has already produced its own curated outputs.

The SQL path answers one core question:

> Can the same business metrics and reporting tables be reproduced in SQL from the same raw operational data?

The answer from the completed validation run is yes: the SQL pipeline matched the Python pipeline on all 14 metric checks and all 25 monthly revenue checks.

## SQL Engine

The project uses SQLite through `python/05_run_sql_pipeline.py`.

This was chosen for portability:

- No local database server is required.
- Raw CSV files can be loaded directly into a local `.sqlite` file.
- SQL scripts can be reviewed independently in the `sql` folder.
- The project remains easy for a recruiter, hiring manager, or reviewer to reproduce.

The generated SQLite database is written locally to:

`data/validation_outputs/olist_reporting_pipeline.sqlite`

This database is a reproducible local artifact and should not be committed to GitHub because it is large.

## Step 1: Load Raw CSVs Into SQLite

Script: `python/05_run_sql_pipeline.py`

The runner loads each raw Olist file into a SQLite raw table.

| Raw SQLite table | Source CSV | Rows |
| --- | --- | ---: |
| `raw_customers` | `olist_customers_dataset.csv` | 99,441 |
| `raw_geolocation` | `olist_geolocation_dataset.csv` | 1,000,163 |
| `raw_order_items` | `olist_order_items_dataset.csv` | 112,650 |
| `raw_payments` | `olist_order_payments_dataset.csv` | 103,886 |
| `raw_reviews` | `olist_order_reviews_dataset.csv` | 99,224 |
| `raw_orders` | `olist_orders_dataset.csv` | 99,441 |
| `raw_products` | `olist_products_dataset.csv` | 32,951 |
| `raw_sellers` | `olist_sellers_dataset.csv` | 3,095 |
| `raw_category_translation` | `product_category_name_translation.csv` | 71 |

## Step 2: Raw Table Indexes

SQL file: `sql/01_create_tables.sql`

The raw tables are created by the Python runner, then the first SQL file adds indexes for the main join keys:

- `customer_id`
- `customer_unique_id`
- `order_id`
- `product_id`
- `seller_id`
- `product_category_name`

The point of this step is to make the SQL path more realistic. Even for a portfolio project, reporting pipelines should be designed around repeatable joins and key relationships.

## Step 3: Cleaning Views

SQL file: `sql/02_cleaning_views.sql`

The second SQL file creates cleaning views that mirror the Pandas cleaning logic.

| SQL view | Purpose |
| --- | --- |
| `clean_customers` | Standardizes customer city and state |
| `clean_sellers` | Standardizes seller city and state |
| `clean_products` | Joins category translation and fills missing English categories as `unknown` |
| `clean_orders` | Creates purchase date/month, delivered flag, delivery-day fields, and late-delivery flag |
| `clean_order_items` | Converts price/freight to numeric values and creates `line_revenue` |
| `clean_payments` | Converts payment sequence, installments, and value fields |
| `clean_reviews` | Converts review score and creates `has_review_comment` |
| `clean_geolocation` | Standardizes city/state and supports duplicate-quality checks |

Key SQL logic:

- `line_revenue = price + freight_value`
- `purchase_month = STRFTIME('%Y-%m', order_purchase_timestamp)`
- `delivery_days = JULIANDAY(order_delivered_customer_date) - JULIANDAY(order_purchase_timestamp)`
- `days_late = JULIANDAY(order_delivered_customer_date) - JULIANDAY(order_estimated_delivery_date)`
- `is_late_delivery = 1` when delivered and `days_late > 0`

## Step 4: SQL Reporting Layer

SQL file: `sql/03_reporting_layer.sql`

The third SQL file creates the curated SQL outputs in the same structure as the Python outputs.

| Output | Rows | Role |
| --- | ---: | --- |
| `dim_customer.csv` | 99,441 | Customer dimension |
| `dim_product.csv` | 32,951 | Product dimension |
| `dim_seller.csv` | 3,095 | Seller dimension |
| `fact_orders.csv` | 99,441 | Order-level reporting fact |
| `fact_order_items.csv` | 112,650 | Item-level reporting fact |
| `fact_payments.csv` | 103,886 | Payment-level reporting fact |
| `fact_delivery_performance.csv` | 99,441 | Delivery performance fact |
| `monthly_kpi_summary.csv` | 25 | Monthly dashboard summary table |

The SQL reporting layer uses common reporting patterns:

- Build dimensions at stable entity grains.
- Build facts at order, item, payment, and delivery grains.
- Aggregate item totals to the order grain before calculating reconciliation metrics.
- Aggregate payment totals to the order grain before calculating variance.
- Use the monthly KPI table as the Tableau-ready business summary.

## Step 5: SQL Data Quality Checks

SQL file: `sql/04_data_quality_checks.sql`

The fourth SQL file creates `data_quality_issues`, matching the Python issue logic.

| Issue type | Count |
| --- | ---: |
| Payment Does Not Reconcile To Order Total | 1,033 |
| Order Missing Item Detail | 775 |
| Missing Product Category | 623 |
| Delivered Order Missing Delivery Date | 8 |
| Duplicate Geolocation Rows | 1 |

The SQL issue table is designed to work like an operational exception report. It includes:

- `issue_id`
- `source_table`
- `record_id`
- `field_name`
- `issue_type`
- `severity`
- `issue_description`

## Step 6: SQL Reconciliation Summary

SQL file: `sql/05_reconciliation_queries.sql`

The fifth SQL file creates SQL-side control totals in `sql_reconciliation_summary.csv`.

| Metric | SQL value |
| --- | ---: |
| Total orders | 99,441 |
| Delivered orders | 96,478 |
| Late delivery count | 7,826 |
| Missing product category count | 1,627 |
| Unique customers | 96,096 |
| Unique sellers | 3,095 |
| Data quality issue count | 2,440 |
| Payment variance order count | 1,033 |
| Item price revenue | 13,591,643.70 |
| Freight revenue | 2,251,909.54 |
| Total revenue | 15,843,553.24 |
| Payment revenue | 16,008,872.12 |
| Payment/order variance total | 165,318.88 |
| Average order value | 159.33 |

## Step 7: Python-vs-SQL Comparison

Script: `python/04_compare_python_sql_outputs.py`

The comparison script reads:

- `data/curated_python/python_reconciliation_summary.csv`
- `data/curated_sql/sql_reconciliation_summary.csv`
- `data/curated_python/monthly_kpi_summary.csv`
- `data/curated_sql/monthly_kpi_summary.csv`

It writes:

- `data/validation_outputs/python_sql_comparison_summary.csv`
- `data/validation_outputs/monthly_python_sql_revenue_comparison.csv`
- `data/validation_outputs/reconciliation_summary.csv`

Validation result:

| Check group | Pass | Review |
| --- | ---: | ---: |
| Python vs SQL metric checks | 14 | 0 |
| Monthly revenue checks | 25 | 0 |

Revenue-specific checks included:

- Item price revenue
- Freight revenue
- Total revenue
- Payment revenue
- Payment/order variance total
- Average order value
- Monthly total revenue for all 25 purchase months

## Portfolio Takeaway

The SQL path proves that the reporting logic is not locked inside one tool. The same business definitions were reproduced in SQL, exported into curated outputs, and reconciled against Python with no review items. That makes the project stronger for analytics engineering, BI development, and business systems analyst roles because it demonstrates both transformation skill and validation discipline.
