# Raw Data Profile Summary

This profile records the starting condition of the Olist raw CSV files before transformation.

## File Inventory

| table_name | file_name | row_count | column_count | duplicate_rows |
| --- | --- | --- | --- | --- |
| customers | olist_customers_dataset.csv | 99441 | 5 | 0 |
| geolocation | olist_geolocation_dataset.csv | 1000163 | 5 | 261831 |
| order_items | olist_order_items_dataset.csv | 112650 | 7 | 0 |
| payments | olist_order_payments_dataset.csv | 103886 | 5 | 0 |
| reviews | olist_order_reviews_dataset.csv | 99224 | 7 | 0 |
| orders | olist_orders_dataset.csv | 99441 | 8 | 0 |
| products | olist_products_dataset.csv | 32951 | 9 | 0 |
| sellers | olist_sellers_dataset.csv | 3095 | 4 | 0 |
| category_translation | product_category_name_translation.csv | 71 | 2 | 0 |

## Primary Key Checks

| table_name | key_columns | row_count | distinct_key_count | duplicate_key_count | missing_key_rows | status |
| --- | --- | --- | --- | --- | --- | --- |
| customers | customer_id | 99441 | 99441 | 0 | 0 | Pass |
| order_items | order_id, order_item_id | 112650 | 112650 | 0 | 0 | Pass |
| payments | order_id, payment_sequential | 103886 | 103886 | 0 | 0 | Pass |
| reviews | review_id | 99224 | 98410 | 814 | 0 | Review |
| orders | order_id | 99441 | 99441 | 0 | 0 | Pass |
| products | product_id | 32951 | 32951 | 0 | 0 | Pass |
| sellers | seller_id | 3095 | 3095 | 0 | 0 | Pass |
| category_translation | product_category_name | 71 | 71 | 0 | 0 | Pass |

## Relationship Checks

| child_table | child_key | parent_table | parent_key | child_non_null_keys | orphan_key_count | status |
| --- | --- | --- | --- | --- | --- | --- |
| orders | customer_id | customers | customer_id | 99441 | 0 | Pass |
| order_items | order_id | orders | order_id | 112650 | 0 | Pass |
| payments | order_id | orders | order_id | 103886 | 0 | Pass |
| reviews | order_id | orders | order_id | 99224 | 0 | Pass |
| order_items | product_id | products | product_id | 112650 | 0 | Pass |
| order_items | seller_id | sellers | seller_id | 112650 | 0 | Pass |
| products | product_category_name | category_translation | product_category_name | 32341 | 13 | Review |
