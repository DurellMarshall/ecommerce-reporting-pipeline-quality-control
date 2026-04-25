# Python Transition Journal

Status date: April 25, 2026

## Purpose

This journal documents the Python/Pandas path for Project 3. The goal is to show the full transition from raw Olist operational CSV files into validated reporting outputs that can support BI dashboards.

The Python path answers one core question:

> Can raw multi-table e-commerce data be profiled, cleaned, modeled, and converted into a trusted reporting layer using Python?

## Source Data

The Python pipeline starts from the raw Olist CSV files in `data/raw`.

| Source table | Rows | Business role |
| --- | ---: | --- |
| `olist_customers_dataset.csv` | 99,441 | Customer ID, unique customer ID, city, state, zip prefix |
| `olist_orders_dataset.csv` | 99,441 | Order status and purchase, approval, carrier, customer delivery, and estimated delivery timestamps |
| `olist_order_items_dataset.csv` | 112,650 | Order line items, seller, product, item price, freight value |
| `olist_order_payments_dataset.csv` | 103,886 | Payment method, installments, and payment amount |
| `olist_order_reviews_dataset.csv` | 99,224 | Review score and review comment fields |
| `olist_products_dataset.csv` | 32,951 | Product category and product dimensions |
| `olist_sellers_dataset.csv` | 3,095 | Seller location |
| `product_category_name_translation.csv` | 71 | Portuguese-to-English product category lookup |
| `olist_geolocation_dataset.csv` | 1,000,163 | Zip prefix geography reference; used for profiling and duplicate quality checks |

## Step 1: Raw Profiling

Script: `python/01_data_profile.py`

The first Python step profiles the raw files before any cleaning. This makes the project stronger because the transformation logic is based on observed data quality conditions instead of assumptions.

Outputs:

- `data/validation_outputs/raw_file_profile.csv`
- `data/validation_outputs/raw_column_profile.csv`
- `data/validation_outputs/raw_date_profile.csv`
- `data/validation_outputs/raw_numeric_profile.csv`
- `data/validation_outputs/raw_primary_key_checks.csv`
- `data/validation_outputs/raw_relationship_checks.csv`
- `data/validation_outputs/raw_data_profile_summary.md`

Important profiling findings:

- The order grain is stable: `orders` has 99,441 rows and no duplicate `order_id` values.
- The order item grain is stable: `order_items` has 112,650 rows and no duplicate `order_id` plus `order_item_id` combinations.
- The geolocation table has 261,831 fully duplicate rows, so it should not be joined directly into facts without aggregation.
- The products table has missing or untranslated product category values that need to be surfaced as a quality issue.
- Relationship checks provide traceability before facts and dimensions are built.

## Step 2: Cleaning With Pandas

Script: `python/02_clean_with_pandas.py`

The second Python step creates cleaned versions of the raw tables in `data/cleaned_python`.

| Cleaned output | Grain | Main transformations |
| --- | --- | --- |
| `clean_customers.csv` | One row per customer ID | Standardized city to lowercase and state to uppercase |
| `clean_sellers.csv` | One row per seller ID | Standardized city to lowercase and state to uppercase |
| `clean_products.csv` | One row per product ID | Joined English category translation, filled missing translation as `unknown`, created display label |
| `clean_orders.csv` | One row per order ID | Parsed timestamps, created purchase date/month, delivery-day fields, delivered flag, late delivery flag |
| `clean_order_items.csv` | One row per order line | Converted price/freight to numeric, created `line_revenue = price + freight_value` |
| `clean_payments.csv` | One row per payment line | Converted payment amount and installments to numeric values |
| `clean_reviews.csv` | One row per review | Parsed review dates and created `has_review_comment` flag |
| `clean_geolocation.csv` | One row per raw geolocation record | Standardized city/state for quality checks |

Key business logic added in this step:

- `purchase_month`: reporting month from order purchase timestamp.
- `is_delivered`: order status equals delivered.
- `delivery_days`: days from purchase timestamp to customer delivery timestamp.
- `estimated_delivery_days`: days from purchase timestamp to estimated delivery date.
- `days_late`: customer delivery timestamp minus estimated delivery date.
- `is_late_delivery`: delivered order where `days_late > 0`.
- `line_revenue`: order item price plus freight value.

## Step 3: Python Reporting Layer

Script: `python/03_create_python_reporting_tables.py`

The third Python step converts cleaned operational data into BI-ready dimensions, facts, summaries, and issue logs.

### Dimensions

| Output | Rows | Purpose |
| --- | ---: | --- |
| `dim_customer.csv` | 99,441 | Customer geography and unique customer mapping |
| `dim_product.csv` | 32,951 | Product category and product attributes |
| `dim_seller.csv` | 3,095 | Seller geography |

### Facts

| Output | Rows | Purpose |
| --- | ---: | --- |
| `fact_orders.csv` | 99,441 | Order-level metrics, delivery fields, payment totals, item totals, review summary |
| `fact_order_items.csv` | 112,650 | Item-level product, seller, customer state, line revenue, and missing-category flag |
| `fact_payments.csv` | 103,886 | Payment-level facts with order context |
| `fact_delivery_performance.csv` | 99,441 | Order delivery risk status and delivery timing fields |

### Summary and validation outputs

| Output | Rows | Purpose |
| --- | ---: | --- |
| `monthly_kpi_summary.csv` | 25 | Monthly revenue, order, delivery, customer, seller, and payment metrics |
| `data_quality_issues.csv` | 2,440 | Row-level issue log for dashboard and audit review |
| `python_reconciliation_summary.csv` | 14 | Python-side control totals used for SQL comparison |

## Step 4: Python Data Quality Issue Log

The Python issue log intentionally records rows that a reporting or analytics engineering team would want to monitor.

| Issue type | Count | Meaning |
| --- | ---: | --- |
| Payment Does Not Reconcile To Order Total | 1,033 | Payment total differs from item price plus freight beyond the tolerance |
| Order Missing Item Detail | 775 | Order exists but has no matching order item rows |
| Missing Product Category | 623 | Product is missing a source category or English category translation |
| Delivered Order Missing Delivery Date | 8 | Order is marked delivered but has no customer delivery timestamp |
| Duplicate Geolocation Rows | 1 | Table-level issue noting 261,831 duplicate geolocation rows |

## Step 5: Python Reconciliation Control Totals

These Python control totals are used as the left side of the Python-vs-SQL comparison.

| Metric | Python value |
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

## Business Results From Python Outputs

The Python reporting layer supports the following business interpretation:

- The dataset generated 15.84M in item-plus-freight revenue across 99,441 orders.
- Average order value was 159.33.
- Delivered orders represented 96,478 of 99,441 orders.
- 7,826 delivered orders arrived after the estimated delivery date.
- Top revenue categories include Health Beauty, Watches Gifts, Bed Bath Table, Sports Leisure, and Computers Accessories.
- Payment totals exceeded item-plus-freight revenue by 165,318.88 overall, which is expected to require review because payment rows can include behaviors like vouchers, multiple payments, or operational edge cases.

## Python Output Charts

The chart generator creates the following visuals from Python and validation outputs:

- `images/monthly_revenue_trend.svg`
- `images/top_categories_by_revenue.svg`
- `images/validation_summary.svg`
- `images/revenue_validation_checks.svg`
- `images/pipeline_architecture.svg`
- `images/data_model.svg`

## Portfolio Takeaway

The Python path demonstrates that raw operational e-commerce data can be profiled, cleaned, modeled, validated, and exported into a reporting layer. It also creates the baseline control totals used to prove that the separate SQL implementation matches the same business logic.
