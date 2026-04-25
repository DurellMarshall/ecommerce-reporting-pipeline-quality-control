"""Shared helpers for the Olist e-commerce reporting pipeline."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
CLEANED_DIR = PROJECT_ROOT / "data" / "cleaned_python"
CURATED_PYTHON_DIR = PROJECT_ROOT / "data" / "curated_python"
CURATED_SQL_DIR = PROJECT_ROOT / "data" / "curated_sql"
VALIDATION_DIR = PROJECT_ROOT / "data" / "validation_outputs"
IMAGE_DIR = PROJECT_ROOT / "images"
DOCS_DIR = PROJECT_ROOT / "docs"


RAW_FILES = {
    "customers": "olist_customers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
}


DATE_COLUMNS = {
    "order_items": ["shipping_limit_date"],
    "reviews": ["review_creation_date", "review_answer_timestamp"],
    "orders": [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
}


def ensure_output_dirs() -> None:
    for directory in [
        CLEANED_DIR,
        CURATED_PYTHON_DIR,
        CURATED_SQL_DIR,
        VALIDATION_DIR,
        IMAGE_DIR,
        DOCS_DIR,
    ]:
        directory.mkdir(parents=True, exist_ok=True)


def raw_path(table_name: str) -> Path:
    return RAW_DIR / RAW_FILES[table_name]


def load_raw_table(table_name: str, parse_dates: bool = False) -> pd.DataFrame:
    date_cols = DATE_COLUMNS.get(table_name, []) if parse_dates else []
    return pd.read_csv(raw_path(table_name), parse_dates=date_cols, low_memory=False)


def load_all_raw(parse_dates: bool = False) -> dict[str, pd.DataFrame]:
    return {name: load_raw_table(name, parse_dates=parse_dates) for name in RAW_FILES}


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def clean_text(value: object) -> str | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    return text if text else None


def clean_city(value: object) -> str | None:
    text = clean_text(value)
    return text.lower() if text else None


def clean_state(value: object) -> str | None:
    text = clean_text(value)
    return text.upper() if text else None


def clean_category_label(value: object) -> str:
    text = clean_text(value)
    if not text:
        return "Unknown"
    return text.replace("_", " ").title()


def month_start(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce").dt.to_period("M").astype(str)


def days_between(end: pd.Series, start: pd.Series) -> pd.Series:
    return (pd.to_datetime(end, errors="coerce") - pd.to_datetime(start, errors="coerce")).dt.total_seconds() / 86400

