"""Profile raw Olist CSV files.

This script creates a portfolio-ready profiling layer before transformation work
begins. It records file-level health, column-level completeness, key checks,
date ranges, numeric ranges, and relationship checks.
"""

from pathlib import Path

import pandas as pd

from common import RAW_DIR, RAW_FILES, VALIDATION_DIR, ensure_output_dirs


PRIMARY_KEY_CHECKS = {
    "customers": ["customer_id"],
    "orders": ["order_id"],
    "products": ["product_id"],
    "sellers": ["seller_id"],
    "category_translation": ["product_category_name"],
    "order_items": ["order_id", "order_item_id"],
    "payments": ["order_id", "payment_sequential"],
    "reviews": ["review_id"],
}

RELATIONSHIP_CHECKS = [
    ("orders", "customer_id", "customers", "customer_id"),
    ("order_items", "order_id", "orders", "order_id"),
    ("payments", "order_id", "orders", "order_id"),
    ("reviews", "order_id", "orders", "order_id"),
    ("order_items", "product_id", "products", "product_id"),
    ("order_items", "seller_id", "sellers", "seller_id"),
    ("products", "product_category_name", "category_translation", "product_category_name"),
]


def profile_file(table_name: str, path: Path, df: pd.DataFrame) -> dict[str, object]:
    return {
        "table_name": table_name,
        "file_name": path.name,
        "row_count": len(df),
        "column_count": len(df.columns),
        "duplicate_rows": int(df.duplicated().sum()),
        "columns": ", ".join(df.columns),
    }


def profile_columns(table_name: str, df: pd.DataFrame) -> list[dict[str, object]]:
    rows = []
    for column in df.columns:
        series = df[column]
        missing = int(series.isna().sum())
        rows.append(
            {
                "table_name": table_name,
                "column_name": column,
                "dtype": str(series.dtype),
                "missing_count": missing,
                "missing_pct": round(missing / len(df), 4) if len(df) else 0,
                "unique_count": int(series.nunique(dropna=True)),
                "sample_values": " | ".join([str(x) for x in series.dropna().head(3).tolist()]),
            }
        )
    return rows


def profile_dates(table_name: str, df: pd.DataFrame) -> list[dict[str, object]]:
    rows = []
    for column in df.columns:
        if "date" not in column and "timestamp" not in column and not column.endswith("_at"):
            continue
        parsed = pd.to_datetime(df[column], errors="coerce")
        rows.append(
            {
                "table_name": table_name,
                "column_name": column,
                "valid_date_count": int(parsed.notna().sum()),
                "invalid_or_missing_count": int(parsed.isna().sum()),
                "min_date": parsed.min(),
                "max_date": parsed.max(),
            }
        )
    return rows


def profile_numeric(table_name: str, df: pd.DataFrame) -> list[dict[str, object]]:
    rows = []
    numeric_df = df.select_dtypes(include="number")
    for column in numeric_df.columns:
        series = numeric_df[column]
        rows.append(
            {
                "table_name": table_name,
                "column_name": column,
                "min_value": series.min(),
                "max_value": series.max(),
                "mean_value": series.mean(),
                "zero_count": int((series == 0).sum()),
                "negative_count": int((series < 0).sum()),
            }
        )
    return rows


def check_primary_keys(table_name: str, df: pd.DataFrame) -> dict[str, object] | None:
    key_columns = PRIMARY_KEY_CHECKS.get(table_name)
    if not key_columns:
        return None
    missing_columns = [column for column in key_columns if column not in df.columns]
    if missing_columns:
        return {
            "table_name": table_name,
            "key_columns": ", ".join(key_columns),
            "row_count": len(df),
            "distinct_key_count": None,
            "duplicate_key_count": None,
            "missing_key_rows": None,
            "status": f"Missing columns: {', '.join(missing_columns)}",
        }
    missing_key_rows = int(df[key_columns].isna().any(axis=1).sum())
    distinct_key_count = int(df[key_columns].drop_duplicates().shape[0])
    duplicate_key_count = len(df) - distinct_key_count
    return {
        "table_name": table_name,
        "key_columns": ", ".join(key_columns),
        "row_count": len(df),
        "distinct_key_count": distinct_key_count,
        "duplicate_key_count": duplicate_key_count,
        "missing_key_rows": missing_key_rows,
        "status": "Pass" if duplicate_key_count == 0 and missing_key_rows == 0 else "Review",
    }


def check_relationships(tables: dict[str, pd.DataFrame]) -> list[dict[str, object]]:
    rows = []
    for child, child_key, parent, parent_key in RELATIONSHIP_CHECKS:
        child_df = tables[child]
        parent_df = tables[parent]
        child_values = child_df[child_key].dropna()
        parent_values = set(parent_df[parent_key].dropna().unique())
        orphan_mask = ~child_values.isin(parent_values)
        orphan_count = int(orphan_mask.sum())
        rows.append(
            {
                "child_table": child,
                "child_key": child_key,
                "parent_table": parent,
                "parent_key": parent_key,
                "child_non_null_keys": len(child_values),
                "orphan_key_count": orphan_count,
                "status": "Pass" if orphan_count == 0 else "Review",
            }
        )
    return rows


def markdown_table(df: pd.DataFrame) -> str:
    """Render a small DataFrame as a GitHub-flavored Markdown table."""
    if df.empty:
        return "_No rows found._"
    display = df.copy().astype(str)
    headers = list(display.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in display.iterrows():
        values = [str(row[column]).replace("\n", " ") for column in headers]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def write_markdown_summary(file_profile: pd.DataFrame, key_checks: pd.DataFrame, relationship_checks: pd.DataFrame) -> None:
    lines = [
        "# Raw Data Profile Summary",
        "",
        "This profile records the starting condition of the Olist raw CSV files before transformation.",
        "",
        "## File Inventory",
        "",
        markdown_table(file_profile[["table_name", "file_name", "row_count", "column_count", "duplicate_rows"]]),
        "",
        "## Primary Key Checks",
        "",
        markdown_table(key_checks),
        "",
        "## Relationship Checks",
        "",
        markdown_table(relationship_checks),
        "",
    ]
    (VALIDATION_DIR / "raw_data_profile_summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ensure_output_dirs()
    tables: dict[str, pd.DataFrame] = {}
    file_rows = []
    column_rows = []
    date_rows = []
    numeric_rows = []
    key_rows = []

    for table_name, file_name in RAW_FILES.items():
        path = RAW_DIR / file_name
        df = pd.read_csv(path, low_memory=False)
        tables[table_name] = df
        file_rows.append(profile_file(table_name, path, df))
        column_rows.extend(profile_columns(table_name, df))
        date_rows.extend(profile_dates(table_name, df))
        numeric_rows.extend(profile_numeric(table_name, df))
        key_result = check_primary_keys(table_name, df)
        if key_result:
            key_rows.append(key_result)

    file_profile = pd.DataFrame(file_rows)
    column_profile = pd.DataFrame(column_rows)
    date_profile = pd.DataFrame(date_rows)
    numeric_profile = pd.DataFrame(numeric_rows)
    key_checks = pd.DataFrame(key_rows)
    relationship_checks = pd.DataFrame(check_relationships(tables))

    file_profile.to_csv(VALIDATION_DIR / "raw_file_profile.csv", index=False)
    column_profile.to_csv(VALIDATION_DIR / "raw_column_profile.csv", index=False)
    date_profile.to_csv(VALIDATION_DIR / "raw_date_profile.csv", index=False)
    numeric_profile.to_csv(VALIDATION_DIR / "raw_numeric_profile.csv", index=False)
    key_checks.to_csv(VALIDATION_DIR / "raw_primary_key_checks.csv", index=False)
    relationship_checks.to_csv(VALIDATION_DIR / "raw_relationship_checks.csv", index=False)
    write_markdown_summary(file_profile, key_checks, relationship_checks)

    print("Raw profiling complete:")
    for output in [
        "raw_file_profile.csv",
        "raw_column_profile.csv",
        "raw_date_profile.csv",
        "raw_numeric_profile.csv",
        "raw_primary_key_checks.csv",
        "raw_relationship_checks.csv",
        "raw_data_profile_summary.md",
    ]:
        print(f"- {VALIDATION_DIR / output}")


if __name__ == "__main__":
    main()
