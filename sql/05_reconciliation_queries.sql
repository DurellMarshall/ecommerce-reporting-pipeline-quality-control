-- SQL-side reconciliation metrics. The Python comparison script reads this
-- table and validates it against the Python-generated reconciliation summary.

DROP TABLE IF EXISTS sql_reconciliation_summary;
CREATE TABLE sql_reconciliation_summary AS
WITH metrics AS (
    SELECT
        COUNT(DISTINCT order_id) AS total_orders,
        SUM(is_delivered) AS delivered_orders,
        SUM(is_late_delivery) AS late_delivery_count,
        COUNT(DISTINCT customer_unique_id) AS unique_customers,
        SUM(item_price_total) AS item_price_revenue,
        SUM(freight_total) AS freight_revenue,
        SUM(total_revenue) AS total_revenue,
        SUM(payment_total) AS payment_revenue,
        SUM(payment_order_variance) AS payment_order_variance_total,
        SUM(has_payment_variance_flag) AS payment_variance_order_count,
        SUM(total_revenue) / NULLIF(COUNT(DISTINCT order_id), 0) AS average_order_value
    FROM fact_orders
),
item_metrics AS (
    SELECT
        SUM(missing_product_category_flag) AS missing_product_category_count,
        COUNT(DISTINCT seller_id) AS unique_sellers
    FROM fact_order_items
),
dq_metrics AS (
    SELECT COUNT(*) AS data_quality_issue_count
    FROM data_quality_issues
)
SELECT 'total_orders' AS metric, CAST(total_orders AS REAL) AS sql_value FROM metrics
UNION ALL
SELECT 'delivered_orders', CAST(delivered_orders AS REAL) FROM metrics
UNION ALL
SELECT 'late_delivery_count', CAST(late_delivery_count AS REAL) FROM metrics
UNION ALL
SELECT 'missing_product_category_count', CAST(missing_product_category_count AS REAL) FROM item_metrics
UNION ALL
SELECT 'unique_customers', CAST(unique_customers AS REAL) FROM metrics
UNION ALL
SELECT 'unique_sellers', CAST(unique_sellers AS REAL) FROM item_metrics
UNION ALL
SELECT 'data_quality_issue_count', CAST(data_quality_issue_count AS REAL) FROM dq_metrics
UNION ALL
SELECT 'payment_variance_order_count', CAST(payment_variance_order_count AS REAL) FROM metrics
UNION ALL
SELECT 'item_price_revenue', ROUND(item_price_revenue, 2) FROM metrics
UNION ALL
SELECT 'freight_revenue', ROUND(freight_revenue, 2) FROM metrics
UNION ALL
SELECT 'total_revenue', ROUND(total_revenue, 2) FROM metrics
UNION ALL
SELECT 'payment_revenue', ROUND(payment_revenue, 2) FROM metrics
UNION ALL
SELECT 'payment_order_variance_total', ROUND(payment_order_variance_total, 2) FROM metrics
UNION ALL
SELECT 'average_order_value', ROUND(average_order_value, 2) FROM metrics;
