"""Create portfolio charts and diagrams without external plotting packages."""

from __future__ import annotations

from html import escape
from math import isfinite

import pandas as pd

from common import CURATED_PYTHON_DIR, IMAGE_DIR, VALIDATION_DIR, ensure_output_dirs


PALETTE = {
    "ink": "#1f2933",
    "muted": "#5f6c7b",
    "grid": "#d9e2ec",
    "blue": "#246b9f",
    "green": "#2f855a",
    "amber": "#b7791f",
    "red": "#c53030",
    "panel": "#f7fafc",
    "python": "#2f855a",
    "sql": "#b7791f",
    "validation": "#805ad5",
}


def fmt_money(value: float) -> str:
    value = float(value)
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"${value / 1_000:.1f}K"
    return f"${value:,.2f}"


def fmt_number(value: float) -> str:
    value = float(value)
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.1f}K"
    if value.is_integer():
        return f"{int(value):,}"
    return f"{value:,.2f}"


def metric_label(metric: str) -> str:
    return metric.replace("_", " ").title()


def svg_text(
    x: float,
    y: float,
    value: object,
    *,
    size: int = 14,
    fill: str = PALETTE["ink"],
    weight: str = "400",
    anchor: str = "start",
    extra: str = "",
) -> str:
    attrs = f'x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" font-weight="{weight}" text-anchor="{anchor}" {extra}'
    return f"<text {attrs}>{escape(str(value))}</text>"


def svg_rect(
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    fill: str,
    stroke: str = "none",
    radius: int = 0,
    extra: str = "",
) -> str:
    return (
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{height:.1f}" '
        f'rx="{radius}" fill="{fill}" stroke="{stroke}" {extra}/>'
    )


def save_svg(name: str, width: int, height: int, body: list[str]) -> None:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    marker = """
<defs>
  <marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">
    <path d="M0,0 L0,6 L9,3 z" fill="#1f2933" />
  </marker>
</defs>"""
    content = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">',
        marker,
        svg_rect(0, 0, width, height, fill="#ffffff"),
        *body,
        "</svg>",
    ]
    (IMAGE_DIR / name).write_text("\n".join(content), encoding="utf-8")


def scale(value: float, min_value: float, max_value: float, out_min: float, out_max: float) -> float:
    if max_value == min_value:
        return (out_min + out_max) / 2
    return out_min + (value - min_value) * (out_max - out_min) / (max_value - min_value)


def save_monthly_revenue_chart() -> None:
    df = pd.read_csv(CURATED_PYTHON_DIR / "monthly_kpi_summary.csv").sort_values("purchase_month")
    values = df["total_revenue"].astype(float).tolist()
    labels = df["purchase_month"].astype(str).tolist()

    width, height = 1100, 560
    left, right, top, bottom = 90, 35, 70, 95
    chart_w = width - left - right
    chart_h = height - top - bottom
    max_value = max(values) * 1.08

    body = [
        svg_text(left, 38, "Monthly Revenue Trend", size=24, weight="700"),
        svg_text(left, 61, "Revenue generated from item price plus freight by purchase month", size=13, fill=PALETTE["muted"]),
    ]

    for i in range(6):
        y_value = max_value * i / 5
        y = top + chart_h - (chart_h * i / 5)
        body.append(f'<line x1="{left}" y1="{y:.1f}" x2="{width - right}" y2="{y:.1f}" stroke="{PALETTE["grid"]}" stroke-width="1"/>')
        body.append(svg_text(left - 12, y + 4, fmt_money(y_value), size=12, fill=PALETTE["muted"], anchor="end"))

    points = []
    for idx, value in enumerate(values):
        x = scale(idx, 0, len(values) - 1, left, width - right)
        y = scale(value, 0, max_value, top + chart_h, top)
        points.append((x, y))

    path = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    body.append(f'<polyline points="{path}" fill="none" stroke="{PALETTE["blue"]}" stroke-width="4" stroke-linejoin="round" stroke-linecap="round"/>')
    for x, y in points:
        body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{PALETTE["blue"]}"/>')

    for idx, label in enumerate(labels):
        if idx % 2 == 0 or idx == len(labels) - 1:
            x = scale(idx, 0, len(values) - 1, left, width - right)
            body.append(svg_text(x, height - 55, label, size=11, fill=PALETTE["muted"], anchor="end", extra=f'transform="rotate(-45 {x:.1f} {height - 55})"'))

    save_svg("monthly_revenue_trend.svg", width, height, body)


def save_top_categories_chart() -> None:
    items = pd.read_csv(CURATED_PYTHON_DIR / "fact_order_items.csv")
    top = (
        items.groupby("product_category_label", as_index=False)["line_revenue"]
        .sum()
        .sort_values("line_revenue", ascending=False)
        .head(10)
        .sort_values("line_revenue", ascending=True)
    )
    width, height = 1080, 640
    left, right, top_margin, row_h = 280, 60, 82, 44
    chart_w = width - left - right
    max_value = float(top["line_revenue"].max())

    body = [
        svg_text(left, 38, "Top Product Categories By Revenue", size=24, weight="700"),
        svg_text(left, 61, "Top 10 categories based on item price plus freight", size=13, fill=PALETTE["muted"]),
    ]

    for idx, row in enumerate(top.itertuples(index=False)):
        y = top_margin + idx * row_h
        bar_w = scale(float(row.line_revenue), 0, max_value, 0, chart_w)
        label = str(row.product_category_label)
        body.append(svg_text(left - 14, y + 24, label[:34], size=13, fill=PALETTE["ink"], anchor="end"))
        body.append(svg_rect(left, y + 6, bar_w, 25, fill=PALETTE["green"], radius=3))
        body.append(svg_text(left + bar_w + 8, y + 24, fmt_money(float(row.line_revenue)), size=12, fill=PALETTE["muted"]))

    save_svg("top_categories_by_revenue.svg", width, height, body)


def save_validation_summary_chart() -> None:
    df = pd.read_csv(VALIDATION_DIR / "reconciliation_summary.csv")
    width, height = 820, 410
    left, top = 90, 95
    bar_w, gap = 130, 75
    max_checks = max((df["pass_count"] + df["review_count"]).astype(float).max(), 1)

    body = [
        svg_text(left, 40, "Validation Summary", size=24, weight="700"),
        svg_text(left, 63, "Python-vs-SQL metric and monthly revenue checks", size=13, fill=PALETTE["muted"]),
    ]

    for idx, row in enumerate(df.itertuples(index=False)):
        x = left + idx * (bar_w + gap)
        pass_h = scale(float(row.pass_count), 0, max_checks, 0, 210)
        review_h = scale(float(row.review_count), 0, max_checks, 0, 210)
        base_y = top + 220
        body.append(svg_rect(x, top, bar_w, 220, fill="#f8fafc", stroke="#d9e2ec", radius=4))
        body.append(svg_rect(x + 20, base_y - pass_h, bar_w - 40, pass_h, fill=PALETTE["green"], radius=3))
        if review_h:
            body.append(svg_rect(x + 20, base_y - pass_h - review_h, bar_w - 40, review_h, fill=PALETTE["red"], radius=3))
        body.append(svg_text(x + bar_w / 2, base_y - pass_h - review_h - 10, f"{int(row.pass_count)} pass / {int(row.review_count)} review", size=12, anchor="middle"))
        body.append(svg_text(x + bar_w / 2, base_y + 28, metric_label(row.check_group), size=12, fill=PALETTE["muted"], anchor="middle"))

    body.append(svg_rect(width - 230, 37, 16, 16, fill=PALETTE["green"], radius=2))
    body.append(svg_text(width - 207, 50, "Pass", size=12, fill=PALETTE["muted"]))
    body.append(svg_rect(width - 160, 37, 16, 16, fill=PALETTE["red"], radius=2))
    body.append(svg_text(width - 137, 50, "Review", size=12, fill=PALETTE["muted"]))
    save_svg("validation_summary.svg", width, height, body)


def save_revenue_validation_chart() -> None:
    comparison = pd.read_csv(VALIDATION_DIR / "python_sql_comparison_summary.csv")
    revenue_metrics = comparison[
        comparison["metric"].str.contains("revenue|variance|average_order_value", case=False)
    ].copy()

    width, row_h = 1180, 44
    height = 105 + row_h * (len(revenue_metrics) + 1)
    body = [
        svg_text(55, 40, "Revenue Validation Checks", size=24, weight="700"),
        svg_text(55, 63, "Python and SQL outputs match on revenue, freight, payment, variance, and AOV metrics", size=13, fill=PALETTE["muted"]),
        svg_rect(45, 82, width - 90, row_h, fill="#edf2f7", radius=4),
        svg_text(65, 110, "Metric", size=13, weight="700"),
        svg_text(420, 110, "Python", size=13, weight="700"),
        svg_text(610, 110, "SQL", size=13, weight="700"),
        svg_text(800, 110, "Difference", size=13, weight="700"),
        svg_text(990, 110, "Status", size=13, weight="700"),
    ]

    for idx, row in enumerate(revenue_metrics.itertuples(index=False)):
        y = 126 + idx * row_h
        fill = "#ffffff" if idx % 2 == 0 else "#f8fafc"
        py_value = float(row.python_value)
        sql_value = float(row.sql_value)
        diff = float(row.difference)
        status_color = PALETTE["green"] if row.status == "Pass" else PALETTE["red"]
        value_formatter = fmt_money if any(token in row.metric for token in ["revenue", "variance", "average_order_value"]) else fmt_number
        body.append(svg_rect(45, y, width - 90, row_h, fill=fill))
        body.append(svg_text(65, y + 28, metric_label(row.metric), size=13))
        body.append(svg_text(420, y + 28, value_formatter(py_value), size=13, fill=PALETTE["python"]))
        body.append(svg_text(610, y + 28, value_formatter(sql_value), size=13, fill=PALETTE["sql"]))
        body.append(svg_text(800, y + 28, value_formatter(diff), size=13, fill=PALETTE["muted"]))
        body.append(svg_rect(990, y + 12, 74, 21, fill=status_color, radius=10))
        body.append(svg_text(1027, y + 27, row.status.upper(), size=11, fill="#ffffff", weight="700", anchor="middle"))

    save_svg("revenue_validation_checks.svg", width, height, body)


def box(x: float, y: float, w: float, h: float, label: str, fill: str) -> list[str]:
    return [
        svg_rect(x, y, w, h, fill=fill, stroke="#334e68", radius=6),
        svg_text(x + w / 2, y + h / 2 + 5, label, size=14, weight="700", anchor="middle"),
    ]


def arrow(x1: float, y1: float, x2: float, y2: float) -> str:
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#1f2933" stroke-width="2" marker-end="url(#arrow)"/>'


def save_pipeline_architecture() -> None:
    width, height = 1120, 680
    body = [
        svg_text(70, 42, "Olist Reporting Pipeline Architecture", size=24, weight="700"),
        svg_text(70, 66, "One raw dataset, two transformation paths, one reconciled reporting layer", size=13, fill=PALETTE["muted"]),
    ]
    boxes = [
        (70, 130, 190, 70, "Raw Olist CSVs", "#e8f1ff"),
        (350, 95, 230, 70, "Python/Pandas Pipeline", "#eaf7ea"),
        (350, 200, 230, 70, "SQLite SQL Pipeline", "#fff3dd"),
        (670, 95, 235, 70, "Curated Python Outputs", "#eaf7ea"),
        (670, 200, 235, 70, "Curated SQL Outputs", "#fff3dd"),
        (430, 340, 300, 75, "Validation & Reconciliation", "#f3e8ff"),
        (430, 475, 300, 75, "Final Reporting Tables", "#eef2f3"),
        (430, 590, 300, 55, "Tableau Dashboard", "#e6fffa"),
    ]
    for item in boxes:
        body.extend(box(*item))
    body.extend(
        [
            arrow(260, 165, 350, 130),
            arrow(260, 165, 350, 235),
            arrow(580, 130, 670, 130),
            arrow(580, 235, 670, 235),
            arrow(785, 165, 650, 340),
            arrow(785, 270, 650, 340),
            arrow(580, 415, 580, 475),
            arrow(580, 550, 580, 590),
        ]
    )
    save_svg("pipeline_architecture.svg", width, height, body)


def save_data_model_diagram() -> None:
    width, height = 1100, 620
    body = [
        svg_text(70, 42, "Curated Reporting Data Model", size=24, weight="700"),
        svg_text(70, 66, "Fact and dimension outputs used for validation and dashboarding", size=13, fill=PALETTE["muted"]),
    ]
    boxes = [
        (70, 130, 190, 62, "dim_customer", "#e8f1ff"),
        (70, 260, 190, 62, "dim_product", "#e8f1ff"),
        (70, 390, 190, 62, "dim_seller", "#e8f1ff"),
        (440, 130, 210, 62, "fact_orders", "#f3e8ff"),
        (440, 260, 210, 62, "fact_order_items", "#f3e8ff"),
        (815, 130, 190, 62, "fact_payments", "#fff3dd"),
        (785, 260, 250, 62, "fact_delivery_performance", "#fff3dd"),
        (430, 500, 240, 62, "monthly_kpi_summary", "#eef2f3"),
    ]
    for item in boxes:
        body.extend(box(*item))
    body.extend(
        [
            arrow(260, 161, 440, 161),
            arrow(260, 291, 440, 291),
            arrow(260, 421, 440, 291),
            arrow(650, 161, 815, 161),
            arrow(650, 161, 785, 291),
            arrow(545, 322, 545, 500),
            arrow(545, 192, 545, 500),
        ]
    )
    save_svg("data_model.svg", width, height, body)


def main() -> None:
    ensure_output_dirs()
    save_monthly_revenue_chart()
    save_top_categories_chart()
    save_validation_summary_chart()
    save_revenue_validation_chart()
    save_pipeline_architecture()
    save_data_model_diagram()
    print("Charts and diagrams created in images/")


if __name__ == "__main__":
    main()
