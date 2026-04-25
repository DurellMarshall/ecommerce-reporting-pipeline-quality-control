-- Cleaned SQL views preserve source grains while normalizing the fields used
-- by the reporting layer.

DROP VIEW IF EXISTS clean_customers;
CREATE VIEW clean_customers AS
SELECT
    customer_id,
    customer_unique_id,
    customer_zip_code_prefix,
    LOWER(TRIM(customer_city)) AS customer_city,
    UPPER(TRIM(customer_state)) AS customer_state
FROM raw_customers;

DROP VIEW IF EXISTS clean_sellers;
CREATE VIEW clean_sellers AS
SELECT
    seller_id,
    seller_zip_code_prefix,
    LOWER(TRIM(seller_city)) AS seller_city,
    UPPER(TRIM(seller_state)) AS seller_state
FROM raw_sellers;

DROP VIEW IF EXISTS clean_products;
CREATE VIEW clean_products AS
SELECT
    p.product_id,
    p.product_category_name,
    COALESCE(t.product_category_name_english, 'unknown') AS product_category_name_english,
    REPLACE(COALESCE(t.product_category_name_english, 'unknown'), '_', ' ') AS product_category_label,
    CAST(p.product_name_lenght AS REAL) AS product_name_lenght,
    CAST(p.product_description_lenght AS REAL) AS product_description_lenght,
    CAST(p.product_photos_qty AS REAL) AS product_photos_qty,
    CAST(p.product_weight_g AS REAL) AS product_weight_g,
    CAST(p.product_length_cm AS REAL) AS product_length_cm,
    CAST(p.product_height_cm AS REAL) AS product_height_cm,
    CAST(p.product_width_cm AS REAL) AS product_width_cm
FROM raw_products AS p
LEFT JOIN raw_category_translation AS t
    ON p.product_category_name = t.product_category_name;

DROP VIEW IF EXISTS clean_orders;
CREATE VIEW clean_orders AS
SELECT
    order_id,
    customer_id,
    order_status,
    order_purchase_timestamp,
    DATE(order_purchase_timestamp) AS purchase_date,
    STRFTIME('%Y-%m', order_purchase_timestamp) AS purchase_month,
    order_approved_at,
    order_delivered_carrier_date,
    order_delivered_customer_date,
    order_estimated_delivery_date,
    CASE WHEN order_status = 'delivered' THEN 1 ELSE 0 END AS is_delivered,
    (JULIANDAY(order_delivered_customer_date) - JULIANDAY(order_purchase_timestamp)) AS delivery_days,
    (JULIANDAY(order_estimated_delivery_date) - JULIANDAY(order_purchase_timestamp)) AS estimated_delivery_days,
    (JULIANDAY(order_delivered_customer_date) - JULIANDAY(order_estimated_delivery_date)) AS days_late,
    CASE
        WHEN order_status = 'delivered'
             AND (JULIANDAY(order_delivered_customer_date) - JULIANDAY(order_estimated_delivery_date)) > 0
        THEN 1
        ELSE 0
    END AS is_late_delivery
FROM raw_orders;

DROP VIEW IF EXISTS clean_order_items;
CREATE VIEW clean_order_items AS
SELECT
    order_id,
    CAST(order_item_id AS INTEGER) AS order_item_id,
    product_id,
    seller_id,
    shipping_limit_date,
    COALESCE(CAST(price AS REAL), 0) AS price,
    COALESCE(CAST(freight_value AS REAL), 0) AS freight_value,
    COALESCE(CAST(price AS REAL), 0) + COALESCE(CAST(freight_value AS REAL), 0) AS line_revenue
FROM raw_order_items;

DROP VIEW IF EXISTS clean_payments;
CREATE VIEW clean_payments AS
SELECT
    order_id,
    CAST(payment_sequential AS INTEGER) AS payment_sequential,
    payment_type,
    CAST(payment_installments AS INTEGER) AS payment_installments,
    COALESCE(CAST(payment_value AS REAL), 0) AS payment_value
FROM raw_payments;

DROP VIEW IF EXISTS clean_reviews;
CREATE VIEW clean_reviews AS
SELECT
    review_id,
    order_id,
    CAST(review_score AS REAL) AS review_score,
    review_comment_title,
    review_comment_message,
    review_creation_date,
    review_answer_timestamp,
    CASE WHEN review_comment_message IS NOT NULL AND TRIM(review_comment_message) <> '' THEN 1 ELSE 0 END AS has_review_comment
FROM raw_reviews;

DROP VIEW IF EXISTS clean_geolocation;
CREATE VIEW clean_geolocation AS
SELECT
    geolocation_zip_code_prefix,
    CAST(geolocation_lat AS REAL) AS geolocation_lat,
    CAST(geolocation_lng AS REAL) AS geolocation_lng,
    LOWER(TRIM(geolocation_city)) AS geolocation_city,
    UPPER(TRIM(geolocation_state)) AS geolocation_state
FROM raw_geolocation;
