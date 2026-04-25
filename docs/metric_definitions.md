# Metric Definitions

This document defines the metrics used in the Python pipeline, SQL pipeline, validation outputs, and future Tableau dashboard.

## Revenue Metrics

| Metric | Definition | Source grain |
| --- | --- | --- |
| `item_price_revenue` | Sum of item `price` from order item lines | Order item |
| `freight_revenue` | Sum of `freight_value` from order item lines | Order item |
| `line_revenue` | `price + freight_value` for one order item row | Order item |
| `total_revenue` | Sum of `line_revenue`; at order level, sum of all item lines for that order | Order item or order |
| `payment_revenue` | Sum of payment values from the payment table | Payment |
| `payment_order_variance` | `payment_total - total_revenue` at the order level | Order |
| `payment_order_variance_total` | Sum of order-level payment variance | Order |
| `average_order_value` | `total_revenue / total_orders` | Summary |

The main revenue definition for this project is item price plus freight. Payment revenue is tracked separately because payment records can include multiple payments, vouchers, or operational edge cases that may not equal item-plus-freight totals exactly.

## Order Metrics

| Metric | Definition |
| --- | --- |
| `total_orders` | Count of distinct `order_id` values |
| `delivered_orders` | Count of orders where `order_status = delivered` |
| `order_item_count` | Count of order item rows attached to an order |
| `unique_product_count` | Count of distinct products attached to an order |
| `unique_seller_count` | Count of distinct sellers attached to an order |

## Delivery Metrics

| Metric | Definition |
| --- | --- |
| `delivery_days` | Days from `order_purchase_timestamp` to `order_delivered_customer_date` |
| `estimated_delivery_days` | Days from `order_purchase_timestamp` to `order_estimated_delivery_date` |
| `days_late` | Days from estimated delivery date to customer delivery date |
| `is_late_delivery` | Delivered order where `days_late > 0` |
| `late_delivery_count` | Count of delivered orders flagged as late |
| `late_delivery_rate` | `late_delivery_count / delivered_orders` |
| `avg_delivery_days` | Average of `delivery_days` across delivered orders with delivery timestamps |
| `delivery_risk_status` | `Delivered On Time`, `Delivered Late`, or `Not Delivered` |

## Customer, Seller, and Product Metrics

| Metric | Definition |
| --- | --- |
| `unique_customers` | Count of distinct `customer_unique_id` values |
| `unique_sellers` | Count of distinct `seller_id` values |
| `missing_product_category_count` | Count of order item rows where product category is missing or untranslated |
| `top_product_categories_by_revenue` | Product category ranking by `line_revenue` |
| `top_customer_states_by_demand` | Customer state ranking by order count or revenue |
| `top_sellers_by_revenue` | Seller ranking by `line_revenue` |

## Validation Metrics

| Metric | Definition |
| --- | --- |
| `data_quality_issue_count` | Number of rows in the data quality issue log |
| `payment_variance_order_count` | Count of orders where absolute payment/order variance exceeds 0.05 |
| `python_sql_difference` | Python metric value minus SQL metric value |
| `status` | `Pass` when absolute difference is within tolerance; otherwise `Review` |

The metric comparison tolerance is 0.05 to allow harmless decimal representation differences while still catching meaningful reporting mismatches.
