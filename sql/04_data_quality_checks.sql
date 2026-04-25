-- Data quality output is intentionally row-level where possible so the issue
-- log can be filtered in a dashboard or inspected during reconciliation.

DROP TABLE IF EXISTS data_quality_issues;
CREATE TABLE data_quality_issues AS
WITH duplicate_geolocation AS (
    SELECT
        COUNT(*) - COUNT(DISTINCT
            COALESCE(CAST(geolocation_zip_code_prefix AS TEXT), '<null>') || '|' ||
            COALESCE(CAST(geolocation_lat AS TEXT), '<null>') || '|' ||
            COALESCE(CAST(geolocation_lng AS TEXT), '<null>') || '|' ||
            COALESCE(geolocation_city, '<null>') || '|' ||
            COALESCE(geolocation_state, '<null>')
        ) AS duplicate_count
    FROM clean_geolocation
),
dq_base AS (
    SELECT
        'products' AS source_table,
        product_id AS record_id,
        'product_category_name' AS field_name,
        'Missing Product Category' AS issue_type,
        'Medium' AS severity,
        'Product is missing a source category or English category translation.' AS issue_description
    FROM clean_products
    WHERE product_category_name IS NULL
       OR product_category_name_english = 'unknown'

    UNION ALL

    SELECT
        'orders' AS source_table,
        order_id AS record_id,
        'order_delivered_customer_date' AS field_name,
        'Delivered Order Missing Delivery Date' AS issue_type,
        'High' AS severity,
        'Order status is delivered but customer delivery timestamp is missing.' AS issue_description
    FROM fact_orders
    WHERE order_status = 'delivered'
      AND order_delivered_customer_date IS NULL

    UNION ALL

    SELECT
        'orders' AS source_table,
        order_id AS record_id,
        'delivery_days' AS field_name,
        'Negative Delivery Days' AS issue_type,
        'Critical' AS severity,
        'Customer delivery timestamp occurs before purchase timestamp.' AS issue_description
    FROM fact_orders
    WHERE delivery_days < 0

    UNION ALL

    SELECT
        'orders' AS source_table,
        order_id AS record_id,
        'payment_order_variance' AS field_name,
        'Payment Does Not Reconcile To Order Total' AS issue_type,
        'High' AS severity,
        'Payment total differs from item price plus freight total beyond tolerance.' AS issue_description
    FROM fact_orders
    WHERE has_payment_variance_flag = 1

    UNION ALL

    SELECT
        'orders' AS source_table,
        order_id AS record_id,
        'order_item_count' AS field_name,
        'Order Missing Item Detail' AS issue_type,
        'High' AS severity,
        'Order exists without matching order item rows.' AS issue_description
    FROM fact_orders
    WHERE order_item_count = 0

    UNION ALL

    SELECT
        'geolocation' AS source_table,
        'table_summary' AS record_id,
        'all_columns' AS field_name,
        'Duplicate Geolocation Rows' AS issue_type,
        'Low' AS severity,
        'Geolocation table contains ' || duplicate_count || ' duplicate rows; this table should be aggregated before joins.' AS issue_description
    FROM duplicate_geolocation
    WHERE duplicate_count > 0
),
numbered AS (
    SELECT
        ROW_NUMBER() OVER (
            ORDER BY
                CASE severity
                    WHEN 'Critical' THEN 1
                    WHEN 'High' THEN 2
                    WHEN 'Medium' THEN 3
                    ELSE 4
                END,
                source_table,
                issue_type,
                record_id
        ) AS issue_number,
        *
    FROM dq_base
)
SELECT
    'DQ-SQL-' || PRINTF('%06d', issue_number) AS issue_id,
    source_table,
    record_id,
    field_name,
    issue_type,
    severity,
    issue_description
FROM numbered;
