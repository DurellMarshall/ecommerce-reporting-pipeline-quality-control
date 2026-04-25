"""Compare Python and SQL curated outputs.

Outputs are written to data/validation_outputs. The comparison includes the
requested revenue checks plus count, delivery, category, customer, and seller
checks.
"""

from __future__ import annotations

import pandas as pd

from common import CURATED_PYTHON_DIR, CURATED_SQL_DIR, VALIDATION_DIR, ensure_output_dirs, write_csv


TOLERANCE = 0.05


def compare_metric(metric: str, python_value: float, sql_value: float) -> dict[str, object]:
    difference = float(python_value) - float(sql_value)
    return {
        "metric": metric,
        "python_value": python_value,
        "sql_value": sql_value,
        "difference": round(difference, 6),
        "absolute_difference": round(abs(difference), 6),
        "status": "Pass" if abs(difference) <= TOLERANCE else "Review",
    }


def load_summary(path, value_column: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    return df[["metric", value_column]]


def compare_reconciliation_summaries() -> pd.DataFrame:
    python_summary = load_summary(CURATED_PYTHON_DIR / "python_reconciliation_summary.csv", "python_value")
    sql_summary = load_summary(CURATED_SQL_DIR / "sql_reconciliation_summary.csv", "sql_value")
    merged = python_summary.merge(sql_summary, on="metric", how="outer").fillna(0)
    return pd.DataFrame(
        [
            compare_metric(row.metric, row.python_value, row.sql_value)
            for row in merged.itertuples(index=False)
        ]
    )


def compare_monthly_revenue() -> pd.DataFrame:
    py = pd.read_csv(CURATED_PYTHON_DIR / "monthly_kpi_summary.csv")
    sql = pd.read_csv(CURATED_SQL_DIR / "monthly_kpi_summary.csv")
    merged = py[["purchase_month", "total_revenue", "total_orders", "late_delivery_count"]].merge(
        sql[["purchase_month", "total_revenue", "total_orders", "late_delivery_count"]],
        on="purchase_month",
        how="outer",
        suffixes=("_python", "_sql"),
    ).fillna(0)
    merged["revenue_difference"] = merged["total_revenue_python"] - merged["total_revenue_sql"]
    merged["order_difference"] = merged["total_orders_python"] - merged["total_orders_sql"]
    merged["late_delivery_difference"] = merged["late_delivery_count_python"] - merged["late_delivery_count_sql"]
    merged["status"] = merged.apply(
        lambda row: "Pass"
        if abs(row["revenue_difference"]) <= TOLERANCE
        and abs(row["order_difference"]) <= TOLERANCE
        and abs(row["late_delivery_difference"]) <= TOLERANCE
        else "Review",
        axis=1,
    )
    return merged


def main() -> None:
    ensure_output_dirs()
    comparison = compare_reconciliation_summaries()
    monthly_comparison = compare_monthly_revenue()

    write_csv(comparison, VALIDATION_DIR / "python_sql_comparison_summary.csv")
    write_csv(monthly_comparison, VALIDATION_DIR / "monthly_python_sql_revenue_comparison.csv")

    pass_count = int(comparison["status"].eq("Pass").sum())
    review_count = int(comparison["status"].eq("Review").sum())
    reconciliation_summary = pd.DataFrame(
        [
            {"check_group": "Python vs SQL metric checks", "pass_count": pass_count, "review_count": review_count},
            {
                "check_group": "Monthly revenue checks",
                "pass_count": int(monthly_comparison["status"].eq("Pass").sum()),
                "review_count": int(monthly_comparison["status"].eq("Review").sum()),
            },
        ]
    )
    write_csv(reconciliation_summary, VALIDATION_DIR / "reconciliation_summary.csv")

    print("Python vs SQL comparison complete:")
    print(f"- Metric checks passing: {pass_count}")
    print(f"- Metric checks needing review: {review_count}")


if __name__ == "__main__":
    main()
