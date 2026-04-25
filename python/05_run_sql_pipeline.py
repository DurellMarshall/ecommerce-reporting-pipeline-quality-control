"""Run the SQLite implementation of the Olist reporting pipeline."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from common import CURATED_SQL_DIR, RAW_FILES, RAW_DIR, VALIDATION_DIR, ensure_output_dirs, write_csv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = PROJECT_ROOT / "sql"
DATABASE_PATH = VALIDATION_DIR / "olist_reporting_pipeline.sqlite"

RAW_TABLE_NAMES = {
    "customers": "raw_customers",
    "geolocation": "raw_geolocation",
    "order_items": "raw_order_items",
    "payments": "raw_payments",
    "reviews": "raw_reviews",
    "orders": "raw_orders",
    "products": "raw_products",
    "sellers": "raw_sellers",
    "category_translation": "raw_category_translation",
}

EXPORT_TABLES = [
    "dim_customer",
    "dim_product",
    "dim_seller",
    "fact_orders",
    "fact_order_items",
    "fact_payments",
    "fact_delivery_performance",
    "monthly_kpi_summary",
    "data_quality_issues",
    "sql_reconciliation_summary",
]


def load_raw_tables(connection: sqlite3.Connection) -> None:
    for source_name, file_name in RAW_FILES.items():
        table_name = RAW_TABLE_NAMES[source_name]
        df = pd.read_csv(RAW_DIR / file_name, low_memory=False)
        df.to_sql(table_name, connection, if_exists="replace", index=False)
        print(f"Loaded {table_name}: {len(df):,} rows")


def execute_sql_scripts(connection: sqlite3.Connection) -> None:
    for script_name in [
        "01_create_tables.sql",
        "02_cleaning_views.sql",
        "03_reporting_layer.sql",
        "04_data_quality_checks.sql",
        "05_reconciliation_queries.sql",
    ]:
        script_path = SQL_DIR / script_name
        sql = script_path.read_text(encoding="utf-8")
        connection.executescript(sql)
        print(f"Executed {script_name}")


def export_tables(connection: sqlite3.Connection) -> None:
    for table_name in EXPORT_TABLES:
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", connection)
        write_csv(df, CURATED_SQL_DIR / f"{table_name}.csv")
        print(f"Exported {table_name}: {len(df):,} rows")


def main() -> None:
    ensure_output_dirs()
    if DATABASE_PATH.exists():
        DATABASE_PATH.unlink()

    with sqlite3.connect(DATABASE_PATH) as connection:
        load_raw_tables(connection)
        execute_sql_scripts(connection)
        export_tables(connection)

    print(f"SQLite pipeline complete: {DATABASE_PATH}")


if __name__ == "__main__":
    main()
