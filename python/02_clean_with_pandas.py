"""Clean raw Olist tables with Pandas.

The cleaned outputs preserve the original business grains while adding typed
dates, normalized geography/category labels, revenue fields, delivery fields,
and flags needed by the reporting layer.
"""

from __future__ import annotations

import pandas as pd

from common import CLEANED_DIR, ensure_output_dirs, load_all_raw, write_csv


def clean_customers(customers: pd.DataFrame) -> pd.DataFrame:
    df = customers.copy()
    df["customer_city"] = df["customer_city"].str.strip().str.lower()
    df["customer_state"] = df["customer_state"].str.strip().str.upper()
    return df


def clean_sellers(sellers: pd.DataFrame) -> pd.DataFrame:
    df = sellers.copy()
    df["seller_city"] = df["seller_city"].str.strip().str.lower()
    df["seller_state"] = df["seller_state"].str.strip().str.upper()
    return df


def clean_products(products: pd.DataFrame, translation: pd.DataFrame) -> pd.DataFrame:
    df = products.copy()
    df = df.merge(translation, on="product_category_name", how="left")
    df["product_category_name_english"] = df["product_category_name_english"].fillna("unknown")
    df["product_category_label"] = df["product_category_name_english"].str.replace("_", " ", regex=False).str.title()
    numeric_columns = [
        "product_name_lenght",
        "product_description_lenght",
        "product_photos_qty",
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
    ]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    return df


def clean_orders(orders: pd.DataFrame) -> pd.DataFrame:
    df = orders.copy()
    date_columns = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    for column in date_columns:
        df[column] = pd.to_datetime(df[column], errors="coerce")

    df["purchase_date"] = df["order_purchase_timestamp"].dt.date
    df["purchase_month"] = df["order_purchase_timestamp"].dt.to_period("M").astype(str)
    df["is_delivered"] = df["order_status"].eq("delivered")
    df["delivery_days"] = (
        df["order_delivered_customer_date"] - df["order_purchase_timestamp"]
    ).dt.total_seconds() / 86400
    df["estimated_delivery_days"] = (
        df["order_estimated_delivery_date"] - df["order_purchase_timestamp"]
    ).dt.total_seconds() / 86400
    df["days_late"] = (
        df["order_delivered_customer_date"] - df["order_estimated_delivery_date"]
    ).dt.total_seconds() / 86400
    df["is_late_delivery"] = df["is_delivered"] & df["days_late"].gt(0)
    return df


def clean_order_items(order_items: pd.DataFrame) -> pd.DataFrame:
    df = order_items.copy()
    df["shipping_limit_date"] = pd.to_datetime(df["shipping_limit_date"], errors="coerce")
    df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0)
    df["freight_value"] = pd.to_numeric(df["freight_value"], errors="coerce").fillna(0)
    df["line_revenue"] = df["price"] + df["freight_value"]
    return df


def clean_payments(payments: pd.DataFrame) -> pd.DataFrame:
    df = payments.copy()
    df["payment_value"] = pd.to_numeric(df["payment_value"], errors="coerce").fillna(0)
    df["payment_installments"] = pd.to_numeric(df["payment_installments"], errors="coerce").fillna(0).astype(int)
    return df


def clean_reviews(reviews: pd.DataFrame) -> pd.DataFrame:
    df = reviews.copy()
    df["review_creation_date"] = pd.to_datetime(df["review_creation_date"], errors="coerce")
    df["review_answer_timestamp"] = pd.to_datetime(df["review_answer_timestamp"], errors="coerce")
    df["has_review_comment"] = df["review_comment_message"].notna()
    return df


def clean_geolocation(geolocation: pd.DataFrame) -> pd.DataFrame:
    df = geolocation.copy()
    df["geolocation_city"] = df["geolocation_city"].str.strip().str.lower()
    df["geolocation_state"] = df["geolocation_state"].str.strip().str.upper()
    return df


def main() -> None:
    ensure_output_dirs()
    raw = load_all_raw(parse_dates=False)

    cleaned = {
        "clean_customers": clean_customers(raw["customers"]),
        "clean_sellers": clean_sellers(raw["sellers"]),
        "clean_products": clean_products(raw["products"], raw["category_translation"]),
        "clean_orders": clean_orders(raw["orders"]),
        "clean_order_items": clean_order_items(raw["order_items"]),
        "clean_payments": clean_payments(raw["payments"]),
        "clean_reviews": clean_reviews(raw["reviews"]),
        "clean_geolocation": clean_geolocation(raw["geolocation"]),
    }

    summary_rows = []
    for name, df in cleaned.items():
        output = CLEANED_DIR / f"{name}.csv"
        write_csv(df, output)
        summary_rows.append({"table_name": name, "row_count": len(df), "column_count": len(df.columns)})

    pd.DataFrame(summary_rows).to_csv(CLEANED_DIR / "cleaning_summary.csv", index=False)
    print("Pandas cleaning complete:")
    for row in summary_rows:
        print(f"- {row['table_name']}: {row['row_count']} rows")


if __name__ == "__main__":
    main()
