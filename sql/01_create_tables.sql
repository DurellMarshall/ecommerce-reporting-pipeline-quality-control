-- Raw Olist source tables are loaded from CSV by python/05_run_sql_pipeline.py.
-- This script adds indexes so the SQL reporting layer is reproducible and fast
-- without requiring a local database server.

CREATE INDEX IF NOT EXISTS idx_raw_customers_customer_id
ON raw_customers (customer_id);

CREATE INDEX IF NOT EXISTS idx_raw_customers_unique_customer
ON raw_customers (customer_unique_id);

CREATE INDEX IF NOT EXISTS idx_raw_orders_order_id
ON raw_orders (order_id);

CREATE INDEX IF NOT EXISTS idx_raw_orders_customer_id
ON raw_orders (customer_id);

CREATE INDEX IF NOT EXISTS idx_raw_order_items_order_id
ON raw_order_items (order_id);

CREATE INDEX IF NOT EXISTS idx_raw_order_items_product_id
ON raw_order_items (product_id);

CREATE INDEX IF NOT EXISTS idx_raw_order_items_seller_id
ON raw_order_items (seller_id);

CREATE INDEX IF NOT EXISTS idx_raw_payments_order_id
ON raw_payments (order_id);

CREATE INDEX IF NOT EXISTS idx_raw_reviews_order_id
ON raw_reviews (order_id);

CREATE INDEX IF NOT EXISTS idx_raw_products_product_id
ON raw_products (product_id);

CREATE INDEX IF NOT EXISTS idx_raw_sellers_seller_id
ON raw_sellers (seller_id);

CREATE INDEX IF NOT EXISTS idx_raw_category_translation_category
ON raw_category_translation (product_category_name);
