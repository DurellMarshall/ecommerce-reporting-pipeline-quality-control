-- Create dashboard-ready dimensions, facts, and monthly KPI summaries from the
-- SQL cleaning views.

DROP TABLE IF EXISTS dim_customer;
CREATE TABLE dim_customer AS
SELECT DISTINCT
    customer_id,
    customer_unique_id,
    customer_zip_code_prefix,
    customer_city,
    customer_state
FROM clean_customers;

DROP TABLE IF EXISTS dim_product;
CREATE TABLE dim_product AS
SELECT DISTINCT
    product_id,
    product_category_name,
    product_category_name_english,
    product_category_label,
    product_name_lenght,
    product_description_lenght,
    product_photos_qty,
    product_weight_g,
    product_length_cm,
    product_height_cm,
    product_width_cm
FROM clean_products;

DROP TABLE IF EXISTS dim_seller;
CREATE TABLE dim_seller AS
SELECT DISTINCT
    seller_id,
    seller_zip_code_prefix,
    seller_city,
    seller_state
FROM clean_sellers;

DROP TABLE IF EXISTS fact_order_items;
CREATE TABLE fact_order_items AS
SELECT
    oi.order_id,
    oi.order_item_id,
    oi.product_id,
    oi.seller_id,
    o.customer_id,
    c.customer_unique_id,
    o.order_status,
    o.order_purchase_timestamp,
    o.purchase_month,
    p.product_category_name,
    p.product_category_name_english,
    p.product_category_label,
    s.seller_state,
    s.seller_city,
    c.customer_state,
    oi.shipping_limit_date,
    oi.price,
    oi.freight_value,
    oi.line_revenue,
    o.is_delivered,
    o.is_late_delivery,
    CASE
        WHEN p.product_category_name IS NULL
             OR p.product_category_name_english IS NULL
             OR p.product_category_name_english = 'unknown'
        THEN 1
        ELSE 0
    END AS missing_product_category_flag
FROM clean_order_items AS oi
LEFT JOIN clean_products AS p
    ON oi.product_id = p.product_id
LEFT JOIN clean_sellers AS s
    ON oi.seller_id = s.seller_id
LEFT JOIN clean_orders AS o
    ON oi.order_id = o.order_id
LEFT JOIN clean_customers AS c
    ON o.customer_id = c.customer_id;

DROP TABLE IF EXISTS fact_payments;
CREATE TABLE fact_payments AS
SELECT
    p.order_id,
    p.payment_sequential,
    p.payment_type,
    p.payment_installments,
    p.payment_value,
    o.order_status,
    o.order_purchase_timestamp,
    o.purchase_month
FROM clean_payments AS p
LEFT JOIN clean_orders AS o
    ON p.order_id = o.order_id;

DROP TABLE IF EXISTS fact_orders;
CREATE TABLE fact_orders AS
WITH item_agg AS (
    SELECT
        order_id,
        SUM(price) AS item_price_total,
        SUM(freight_value) AS freight_total,
        SUM(line_revenue) AS total_revenue,
        COUNT(order_item_id) AS order_item_count,
        COUNT(DISTINCT product_id) AS unique_product_count,
        COUNT(DISTINCT seller_id) AS unique_seller_count,
        SUM(CASE WHEN missing_product_category_flag = 1 THEN 1 ELSE 0 END) AS missing_product_category_count
    FROM fact_order_items
    GROUP BY order_id
),
payment_agg AS (
    SELECT
        order_id,
        SUM(payment_value) AS payment_total,
        COUNT(payment_sequential) AS payment_count,
        MAX(payment_installments) AS max_payment_installments,
        GROUP_CONCAT(DISTINCT payment_type) AS payment_methods
    FROM fact_payments
    GROUP BY order_id
),
review_agg AS (
    SELECT
        order_id,
        AVG(review_score) AS avg_review_score,
        COUNT(review_id) AS review_count,
        MAX(has_review_comment) AS has_review_comment
    FROM clean_reviews
    GROUP BY order_id
)
SELECT
    o.order_id,
    o.customer_id,
    c.customer_unique_id,
    c.customer_city,
    c.customer_state,
    o.order_status,
    o.order_purchase_timestamp,
    o.purchase_date,
    o.purchase_month,
    o.order_approved_at,
    o.order_delivered_carrier_date,
    o.order_delivered_customer_date,
    o.order_estimated_delivery_date,
    o.is_delivered,
    o.delivery_days,
    o.estimated_delivery_days,
    o.days_late,
    o.is_late_delivery,
    COALESCE(i.item_price_total, 0) AS item_price_total,
    COALESCE(i.freight_total, 0) AS freight_total,
    COALESCE(i.total_revenue, 0) AS total_revenue,
    COALESCE(p.payment_total, 0) AS payment_total,
    COALESCE(p.payment_total, 0) - COALESCE(i.total_revenue, 0) AS payment_order_variance,
    ABS(COALESCE(p.payment_total, 0) - COALESCE(i.total_revenue, 0)) AS payment_variance_abs,
    CASE
        WHEN ABS(COALESCE(p.payment_total, 0) - COALESCE(i.total_revenue, 0)) > 0.05
        THEN 1
        ELSE 0
    END AS has_payment_variance_flag,
    COALESCE(i.order_item_count, 0) AS order_item_count,
    COALESCE(i.unique_product_count, 0) AS unique_product_count,
    COALESCE(i.unique_seller_count, 0) AS unique_seller_count,
    COALESCE(i.missing_product_category_count, 0) AS missing_product_category_count,
    COALESCE(p.payment_count, 0) AS payment_count,
    p.payment_methods,
    COALESCE(p.max_payment_installments, 0) AS max_payment_installments,
    r.avg_review_score,
    COALESCE(r.review_count, 0) AS review_count,
    COALESCE(r.has_review_comment, 0) AS has_review_comment,
    COALESCE(i.total_revenue, 0) AS average_order_value
FROM clean_orders AS o
LEFT JOIN clean_customers AS c
    ON o.customer_id = c.customer_id
LEFT JOIN item_agg AS i
    ON o.order_id = i.order_id
LEFT JOIN payment_agg AS p
    ON o.order_id = p.order_id
LEFT JOIN review_agg AS r
    ON o.order_id = r.order_id;

DROP TABLE IF EXISTS fact_delivery_performance;
CREATE TABLE fact_delivery_performance AS
SELECT
    order_id,
    customer_id,
    customer_state,
    order_status,
    purchase_month,
    order_purchase_timestamp,
    order_delivered_customer_date,
    order_estimated_delivery_date,
    is_delivered,
    delivery_days,
    estimated_delivery_days,
    days_late,
    is_late_delivery,
    total_revenue,
    CASE
        WHEN is_late_delivery = 1 THEN 'Delivered Late'
        WHEN is_delivered = 1 THEN 'Delivered On Time'
        ELSE 'Not Delivered'
    END AS delivery_risk_status
FROM fact_orders;

DROP TABLE IF EXISTS monthly_kpi_summary;
CREATE TABLE monthly_kpi_summary AS
WITH seller_month AS (
    SELECT
        purchase_month,
        COUNT(DISTINCT seller_id) AS unique_sellers
    FROM fact_order_items
    GROUP BY purchase_month
)
SELECT
    fo.purchase_month,
    SUM(fo.total_revenue) AS total_revenue,
    SUM(fo.item_price_total) AS item_price_revenue,
    SUM(fo.freight_total) AS freight_revenue,
    SUM(fo.payment_total) AS payment_revenue,
    SUM(fo.payment_order_variance) AS payment_order_variance,
    COUNT(DISTINCT fo.order_id) AS total_orders,
    SUM(fo.is_delivered) AS delivered_orders,
    SUM(fo.is_late_delivery) AS late_delivery_count,
    AVG(fo.delivery_days) AS avg_delivery_days,
    COUNT(DISTINCT fo.customer_unique_id) AS unique_customers,
    COALESCE(sm.unique_sellers, 0) AS unique_sellers,
    SUM(fo.total_revenue) / NULLIF(COUNT(DISTINCT fo.order_id), 0) AS average_order_value,
    CAST(SUM(fo.is_late_delivery) AS REAL) / NULLIF(SUM(fo.is_delivered), 0) AS late_delivery_rate
FROM fact_orders AS fo
LEFT JOIN seller_month AS sm
    ON fo.purchase_month = sm.purchase_month
GROUP BY
    fo.purchase_month,
    sm.unique_sellers
ORDER BY fo.purchase_month;
