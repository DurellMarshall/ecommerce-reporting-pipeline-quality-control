"""Create curated reporting tables with Pandas.

Outputs are written to data/curated_python and serve as the Python side of the
Python-vs-SQL reconciliation.
"""

from __future__ import annotations

import pandas as pd

from common import CLEANED_DIR, CURATED_PYTHON_DIR, ensure_output_dirs, write_csv


PAYMENT_VARIANCE_TOLERANCE = 0.05


def load_cleaned(name: str) -> pd.DataFrame:
    return pd.read_csv(CLEANED_DIR / f"{name}.csv", low_memory=False)


def build_dimensions(customers: pd.DataFrame, products: pd.DataFrame, sellers: pd.DataFrame) -> dict[str, pd.DataFrame]:
    dim_customer = customers[
        [
            "customer_id",
            "customer_unique_id",
            "customer_zip_code_prefix",
            "customer_city",
            "customer_state",
        ]
    ].drop_duplicates()

    dim_product = products[
        [
            "product_id",
            "product_category_name",
            "product_category_name_english",
            "product_category_label",
            "product_name_lenght",
            "product_description_lenght",
            "product_photos_qty",
            "product_weight_g",
            "product_length_cm",
            "product_height_cm",
            "product_width_cm",
        ]
    ].drop_duplicates()

    dim_seller = sellers[
        ["seller_id", "seller_zip_code_prefix", "seller_city", "seller_state"]
    ].drop_duplicates()

    return {"dim_customer": dim_customer, "dim_product": dim_product, "dim_seller": dim_seller}


def build_fact_order_items(
    order_items: pd.DataFrame,
    orders: pd.DataFrame,
    customers: pd.DataFrame,
    products: pd.DataFrame,
    sellers: pd.DataFrame,
) -> pd.DataFrame:
    order_context = orders[
        ["order_id", "customer_id", "order_status", "order_purchase_timestamp", "purchase_month", "is_delivered", "is_late_delivery"]
    ].merge(customers[["customer_id", "customer_state", "customer_unique_id"]], on="customer_id", how="left")

    fact = order_items.merge(
        products[["product_id", "product_category_name", "product_category_name_english", "product_category_label"]],
        on="product_id",
        how="left",
    ).merge(
        sellers[["seller_id", "seller_state", "seller_city"]],
        on="seller_id",
        how="left",
    ).merge(order_context, on="order_id", how="left")

    fact["missing_product_category_flag"] = fact["product_category_name"].isna() | fact["product_category_name_english"].isna() | fact["product_category_name_english"].eq("unknown")
    return fact[
        [
            "order_id",
            "order_item_id",
            "product_id",
            "seller_id",
            "customer_id",
            "customer_unique_id",
            "order_status",
            "order_purchase_timestamp",
            "purchase_month",
            "product_category_name",
            "product_category_name_english",
            "product_category_label",
            "seller_state",
            "seller_city",
            "customer_state",
            "shipping_limit_date",
            "price",
            "freight_value",
            "line_revenue",
            "is_delivered",
            "is_late_delivery",
            "missing_product_category_flag",
        ]
    ]


def build_fact_payments(payments: pd.DataFrame, orders: pd.DataFrame) -> pd.DataFrame:
    fact = payments.merge(
        orders[["order_id", "order_status", "order_purchase_timestamp", "purchase_month"]],
        on="order_id",
        how="left",
    )
    return fact[
        [
            "order_id",
            "payment_sequential",
            "payment_type",
            "payment_installments",
            "payment_value",
            "order_status",
            "order_purchase_timestamp",
            "purchase_month",
        ]
    ]


def build_fact_orders(
    orders: pd.DataFrame,
    customers: pd.DataFrame,
    order_items: pd.DataFrame,
    payments: pd.DataFrame,
    reviews: pd.DataFrame,
) -> pd.DataFrame:
    item_agg = order_items.groupby("order_id", as_index=False).agg(
        item_price_total=("price", "sum"),
        freight_total=("freight_value", "sum"),
        total_revenue=("line_revenue", "sum"),
        order_item_count=("order_item_id", "count"),
        unique_product_count=("product_id", "nunique"),
        unique_seller_count=("seller_id", "nunique"),
        missing_product_category_count=("missing_product_category_flag", "sum"),
    )

    payment_agg = payments.groupby("order_id", as_index=False).agg(
        payment_total=("payment_value", "sum"),
        payment_count=("payment_sequential", "count"),
        max_payment_installments=("payment_installments", "max"),
    )
    payment_methods = (
        payments.groupby("order_id")["payment_type"]
        .apply(lambda values: ", ".join(sorted(set(str(value) for value in values))))
        .reset_index(name="payment_methods")
    )
    payment_agg = payment_agg.merge(payment_methods, on="order_id", how="left")

    review_agg = reviews.groupby("order_id", as_index=False).agg(
        avg_review_score=("review_score", "mean"),
        review_count=("review_id", "count"),
        has_review_comment=("has_review_comment", "max"),
    )

    fact = (
        orders.merge(customers, on="customer_id", how="left")
        .merge(item_agg, on="order_id", how="left")
        .merge(payment_agg, on="order_id", how="left")
        .merge(review_agg, on="order_id", how="left")
    )

    numeric_fill = [
        "item_price_total",
        "freight_total",
        "total_revenue",
        "order_item_count",
        "unique_product_count",
        "unique_seller_count",
        "missing_product_category_count",
        "payment_total",
        "payment_count",
        "max_payment_installments",
        "review_count",
    ]
    for column in numeric_fill:
        fact[column] = fact[column].fillna(0)

    fact["payment_order_variance"] = fact["payment_total"] - fact["total_revenue"]
    fact["payment_variance_abs"] = fact["payment_order_variance"].abs()
    fact["has_payment_variance_flag"] = fact["payment_variance_abs"].gt(PAYMENT_VARIANCE_TOLERANCE)
    fact["average_order_value"] = fact["total_revenue"]

    return fact[
        [
            "order_id",
            "customer_id",
            "customer_unique_id",
            "customer_city",
            "customer_state",
            "order_status",
            "order_purchase_timestamp",
            "purchase_date",
            "purchase_month",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
            "is_delivered",
            "delivery_days",
            "estimated_delivery_days",
            "days_late",
            "is_late_delivery",
            "item_price_total",
            "freight_total",
            "total_revenue",
            "payment_total",
            "payment_order_variance",
            "payment_variance_abs",
            "has_payment_variance_flag",
            "order_item_count",
            "unique_product_count",
            "unique_seller_count",
            "missing_product_category_count",
            "payment_count",
            "payment_methods",
            "max_payment_installments",
            "avg_review_score",
            "review_count",
            "has_review_comment",
        ]
    ]


def build_fact_delivery_performance(fact_orders: pd.DataFrame) -> pd.DataFrame:
    fact = fact_orders[
        [
            "order_id",
            "customer_id",
            "customer_state",
            "order_status",
            "purchase_month",
            "order_purchase_timestamp",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
            "is_delivered",
            "delivery_days",
            "estimated_delivery_days",
            "days_late",
            "is_late_delivery",
            "total_revenue",
        ]
    ].copy()
    fact["delivery_risk_status"] = "Not Delivered"
    fact.loc[fact["is_delivered"] & ~fact["is_late_delivery"], "delivery_risk_status"] = "Delivered On Time"
    fact.loc[fact["is_late_delivery"], "delivery_risk_status"] = "Delivered Late"
    return fact


def build_monthly_kpis(fact_orders: pd.DataFrame, fact_order_items: pd.DataFrame) -> pd.DataFrame:
    order_month = fact_orders.groupby("purchase_month", as_index=False).agg(
        total_revenue=("total_revenue", "sum"),
        item_price_revenue=("item_price_total", "sum"),
        freight_revenue=("freight_total", "sum"),
        payment_revenue=("payment_total", "sum"),
        payment_order_variance=("payment_order_variance", "sum"),
        total_orders=("order_id", "nunique"),
        delivered_orders=("is_delivered", "sum"),
        late_delivery_count=("is_late_delivery", "sum"),
        avg_delivery_days=("delivery_days", "mean"),
        unique_customers=("customer_unique_id", "nunique"),
    )
    seller_month = fact_order_items.groupby("purchase_month", as_index=False).agg(unique_sellers=("seller_id", "nunique"))
    kpi = order_month.merge(seller_month, on="purchase_month", how="left")
    kpi["average_order_value"] = kpi["total_revenue"] / kpi["total_orders"]
    kpi["late_delivery_rate"] = kpi["late_delivery_count"] / kpi["delivered_orders"].replace({0: pd.NA})
    return kpi.sort_values("purchase_month")


def build_data_quality_issues(
    fact_orders: pd.DataFrame,
    fact_order_items: pd.DataFrame,
    products: pd.DataFrame,
    geolocation: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    def add_issue(source_table: str, record_id: object, field_name: str, issue_type: str, severity: str, description: str) -> None:
        rows.append(
            {
                "issue_id": f"DQ-{len(rows) + 1:06d}",
                "source_table": source_table,
                "record_id": record_id,
                "field_name": field_name,
                "issue_type": issue_type,
                "severity": severity,
                "issue_description": description,
            }
        )

    missing_category_products = products[
        products["product_category_name"].isna() | products["product_category_name_english"].eq("unknown")
    ]
    for row in missing_category_products.itertuples(index=False):
        add_issue(
            "products",
            row.product_id,
            "product_category_name",
            "Missing Product Category",
            "Medium",
            "Product is missing a source category or English category translation.",
        )

    delivered_missing_date = fact_orders[fact_orders["order_status"].eq("delivered") & fact_orders["order_delivered_customer_date"].isna()]
    for row in delivered_missing_date.itertuples(index=False):
        add_issue(
            "orders",
            row.order_id,
            "order_delivered_customer_date",
            "Delivered Order Missing Delivery Date",
            "High",
            "Order status is delivered but customer delivery timestamp is missing.",
        )

    negative_delivery = fact_orders[fact_orders["delivery_days"].lt(0)]
    for row in negative_delivery.itertuples(index=False):
        add_issue(
            "orders",
            row.order_id,
            "delivery_days",
            "Negative Delivery Days",
            "Critical",
            "Customer delivery timestamp occurs before purchase timestamp.",
        )

    payment_variance = fact_orders[fact_orders["has_payment_variance_flag"]]
    for row in payment_variance.itertuples(index=False):
        add_issue(
            "orders",
            row.order_id,
            "payment_order_variance",
            "Payment Does Not Reconcile To Order Total",
            "High",
            "Payment total differs from item price plus freight total beyond tolerance.",
        )

    missing_item_totals = fact_orders[fact_orders["order_item_count"].eq(0)]
    for row in missing_item_totals.itertuples(index=False):
        add_issue(
            "orders",
            row.order_id,
            "order_item_count",
            "Order Missing Item Detail",
            "High",
            "Order exists without matching order item rows.",
        )

    duplicate_geo = int(geolocation.duplicated().sum())
    if duplicate_geo:
        add_issue(
            "geolocation",
            "table_summary",
            "all_columns",
            "Duplicate Geolocation Rows",
            "Low",
            f"Geolocation table contains {duplicate_geo:,} duplicate rows; this table should be aggregated before joins.",
        )

    return pd.DataFrame(rows)


def build_reconciliation_summary(
    fact_orders: pd.DataFrame,
    fact_order_items: pd.DataFrame,
    fact_delivery: pd.DataFrame,
    data_quality_issues: pd.DataFrame,
) -> pd.DataFrame:
    metrics = [
        ("total_orders", fact_orders["order_id"].nunique()),
        ("delivered_orders", int(fact_orders["is_delivered"].sum())),
        ("late_delivery_count", int(fact_orders["is_late_delivery"].sum())),
        ("missing_product_category_count", int(fact_order_items["missing_product_category_flag"].sum())),
        ("unique_customers", fact_orders["customer_unique_id"].nunique()),
        ("unique_sellers", fact_order_items["seller_id"].nunique()),
        ("data_quality_issue_count", len(data_quality_issues)),
        ("payment_variance_order_count", int(fact_orders["has_payment_variance_flag"].sum())),
        ("item_price_revenue", round(float(fact_orders["item_price_total"].sum()), 2)),
        ("freight_revenue", round(float(fact_orders["freight_total"].sum()), 2)),
        ("total_revenue", round(float(fact_orders["total_revenue"].sum()), 2)),
        ("payment_revenue", round(float(fact_orders["payment_total"].sum()), 2)),
        ("payment_order_variance_total", round(float(fact_orders["payment_order_variance"].sum()), 2)),
        ("average_order_value", round(float(fact_orders["total_revenue"].sum() / fact_orders["order_id"].nunique()), 2)),
    ]
    return pd.DataFrame(metrics, columns=["metric", "python_value"])


def main() -> None:
    ensure_output_dirs()
    customers = load_cleaned("clean_customers")
    sellers = load_cleaned("clean_sellers")
    products = load_cleaned("clean_products")
    orders = load_cleaned("clean_orders")
    order_items = load_cleaned("clean_order_items")
    payments = load_cleaned("clean_payments")
    reviews = load_cleaned("clean_reviews")
    geolocation = load_cleaned("clean_geolocation")

    dims = build_dimensions(customers, products, sellers)
    fact_order_items = build_fact_order_items(order_items, orders, customers, products, sellers)
    fact_payments = build_fact_payments(payments, orders)
    fact_orders = build_fact_orders(orders, customers, fact_order_items, fact_payments, reviews)
    fact_delivery = build_fact_delivery_performance(fact_orders)
    monthly_kpi = build_monthly_kpis(fact_orders, fact_order_items)
    data_quality_issues = build_data_quality_issues(fact_orders, fact_order_items, products, geolocation)
    reconciliation_summary = build_reconciliation_summary(fact_orders, fact_order_items, fact_delivery, data_quality_issues)

    outputs = {
        **dims,
        "fact_order_items": fact_order_items,
        "fact_payments": fact_payments,
        "fact_orders": fact_orders,
        "fact_delivery_performance": fact_delivery,
        "monthly_kpi_summary": monthly_kpi,
        "data_quality_issues": data_quality_issues,
        "python_reconciliation_summary": reconciliation_summary,
    }

    for name, df in outputs.items():
        write_csv(df, CURATED_PYTHON_DIR / f"{name}.csv")
        print(f"Wrote {name}: {len(df):,} rows")


if __name__ == "__main__":
    main()
