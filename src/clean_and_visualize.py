from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DATA = ROOT / "data" / "raw_sales_data.csv"
OUTPUT_DIR = ROOT / "outputs"


def money(value: float) -> str:
    return f"Rs. {value:,.0f}"


def clean_sales_data(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    before_rows = len(df)
    missing_before = df.isna().sum()

    df = df.drop_duplicates().copy()
    duplicates_removed = before_rows - len(df)

    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    df["customer"] = df["customer"].fillna("Unknown Customer")
    df["region"] = df["region"].fillna("Unknown Region")
    df["category"] = df["category"].fillna("Uncategorized")
    df["product"] = df["product"].fillna("Unknown Product")

    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")

    df["quantity"] = df["quantity"].fillna(df["quantity"].median())
    df["unit_price"] = df.groupby("category")["unit_price"].transform(
        lambda values: values.fillna(values.median())
    )
    df["unit_price"] = df["unit_price"].fillna(df["unit_price"].median())
    df["order_date"] = df["order_date"].fillna(df["order_date"].median())

    outlier_count = 0
    for column in ["quantity", "unit_price"]:
        q1 = df[column].quantile(0.25)
        q3 = df[column].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        mask = (df[column] < lower) | (df[column] > upper)
        outlier_count += int(mask.sum())
        df[column] = df[column].clip(lower=lower, upper=upper)

    df["quantity"] = df["quantity"].round().astype(int)
    df["unit_price"] = df["unit_price"].round(2)
    df["revenue"] = (df["quantity"] * df["unit_price"]).round(2)
    df["month"] = df["order_date"].dt.to_period("M").astype(str)
    df["order_value_band"] = pd.cut(
        df["revenue"],
        bins=[0, 10000, 50000, float("inf")],
        labels=["Low", "Medium", "High"],
        include_lowest=True,
    )

    summary = pd.DataFrame(
        {
            "metric": [
                "rows_before_cleaning",
                "rows_after_cleaning",
                "duplicates_removed",
                "missing_values_before",
                "missing_values_after",
                "outlier_values_capped",
                "total_revenue",
            ],
            "value": [
                before_rows,
                len(df),
                duplicates_removed,
                int(missing_before.sum()),
                int(df.isna().sum().sum()),
                outlier_count,
                round(float(df["revenue"].sum()), 2),
            ],
        }
    )

    return df.sort_values("order_id"), summary


def bar_chart(title: str, series: pd.Series, color: str) -> str:
    values = series.astype(float)
    max_value = max(values.max(), 1)
    rows = []
    for label, value in values.items():
        width = 100 * value / max_value
        rows.append(
            f"""
            <div class="bar-row">
              <div class="bar-label">{label}</div>
              <div class="bar-track"><div class="bar-fill" style="width:{width:.1f}%; background:{color};"></div></div>
              <div class="bar-value">{money(value)}</div>
            </div>
            """
        )
    return f"<section><h2>{title}</h2>{''.join(rows)}</section>"


def line_chart(title: str, series: pd.Series) -> str:
    values = series.astype(float)
    max_value = max(values.max(), 1)
    points = []
    labels = []
    width = 680
    height = 240
    step = width / max(len(values) - 1, 1)

    for index, (label, value) in enumerate(values.items()):
        x = index * step
        y = height - (value / max_value * (height - 30)) - 10
        points.append(f"{x:.1f},{y:.1f}")
        labels.append(f'<text x="{x:.1f}" y="235" text-anchor="middle">{label}</text>')

    circles = "".join(
        f'<circle cx="{point.split(",")[0]}" cy="{point.split(",")[1]}" r="5"></circle>'
        for point in points
    )

    return f"""
    <section>
      <h2>{title}</h2>
      <svg viewBox="0 0 {width} {height}" role="img" aria-label="{title}">
        <polyline points="{' '.join(points)}"></polyline>
        {circles}
        {''.join(labels)}
      </svg>
    </section>
    """


def build_report(df: pd.DataFrame, summary: pd.DataFrame) -> str:
    revenue_by_region = df.groupby("region")["revenue"].sum().sort_values(ascending=False)
    revenue_by_category = df.groupby("category")["revenue"].sum().sort_values(ascending=False)
    monthly_revenue = df.groupby("month")["revenue"].sum().sort_index()
    top_products = df.groupby("product")["revenue"].sum().sort_values(ascending=False).head(6)

    total_revenue = float(df["revenue"].sum())
    avg_order_value = float(df["revenue"].mean())
    top_region = revenue_by_region.index[0]
    top_category = revenue_by_category.index[0]

    quality_rows = "".join(
        f"<tr><td>{row.metric}</td><td>{row.value}</td></tr>"
        for row in summary.itertuples(index=False)
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Sales Data Cleaning & Visualization Report</title>
  <style>
    body {{
      margin: 0;
      background: #f5f7fb;
      color: #172033;
      font-family: Arial, Helvetica, sans-serif;
      line-height: 1.5;
    }}
    main {{
      max-width: 1120px;
      margin: 0 auto;
      padding: 32px 20px 48px;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: 32px;
    }}
    h2 {{
      margin: 0 0 18px;
      font-size: 20px;
    }}
    .subtitle {{
      margin: 0 0 24px;
      color: #586174;
    }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
      gap: 14px;
      margin: 24px 0;
    }}
    .metric, section {{
      background: #ffffff;
      border: 1px solid #dce3ef;
      border-radius: 8px;
      padding: 18px;
      box-shadow: 0 8px 20px rgba(23, 32, 51, 0.06);
    }}
    .metric span {{
      display: block;
      color: #586174;
      font-size: 13px;
    }}
    .metric strong {{
      display: block;
      margin-top: 8px;
      font-size: 22px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 18px;
    }}
    .bar-row {{
      display: grid;
      grid-template-columns: 120px 1fr 120px;
      gap: 12px;
      align-items: center;
      margin: 12px 0;
      font-size: 14px;
    }}
    .bar-track {{
      height: 14px;
      background: #e9edf5;
      border-radius: 999px;
      overflow: hidden;
    }}
    .bar-fill {{
      height: 100%;
      border-radius: 999px;
    }}
    .bar-value {{
      color: #39445a;
      text-align: right;
    }}
    svg {{
      width: 100%;
      height: auto;
    }}
    polyline {{
      fill: none;
      stroke: #2f6fed;
      stroke-width: 4;
    }}
    circle {{
      fill: #00a676;
      stroke: #ffffff;
      stroke-width: 2;
    }}
    text {{
      fill: #586174;
      font-size: 13px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: #ffffff;
      border: 1px solid #dce3ef;
      border-radius: 8px;
      overflow: hidden;
    }}
    th, td {{
      padding: 12px 14px;
      border-bottom: 1px solid #e7ecf4;
      text-align: left;
    }}
    th {{
      background: #eef3fb;
    }}
    @media (max-width: 640px) {{
      .bar-row {{
        grid-template-columns: 1fr;
        gap: 6px;
      }}
      .bar-value {{
        text-align: left;
      }}
    }}
  </style>
</head>
<body>
  <main>
    <h1>Sales Data Cleaning & Visualization Report</h1>
    <p class="subtitle">Raw sales data was cleaned, standardized, enriched, and summarized into key visual insights.</p>
    <div class="metrics">
      <div class="metric"><span>Total revenue</span><strong>{money(total_revenue)}</strong></div>
      <div class="metric"><span>Average order value</span><strong>{money(avg_order_value)}</strong></div>
      <div class="metric"><span>Top region</span><strong>{top_region}</strong></div>
      <div class="metric"><span>Top category</span><strong>{top_category}</strong></div>
    </div>
    <div class="grid">
      {bar_chart("Revenue by Region", revenue_by_region, "#2f6fed")}
      {bar_chart("Revenue by Category", revenue_by_category, "#00a676")}
      {line_chart("Monthly Revenue Trend", monthly_revenue)}
      {bar_chart("Top Products by Revenue", top_products, "#ef7b45")}
    </div>
    <section style="margin-top:18px;">
      <h2>Data Quality Summary</h2>
      <table>
        <thead><tr><th>Metric</th><th>Value</th></tr></thead>
        <tbody>{quality_rows}</tbody>
      </table>
    </section>
  </main>
</body>
</html>
"""


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    raw_df = pd.read_csv(RAW_DATA)
    clean_df, summary = clean_sales_data(raw_df)

    clean_df.to_csv(OUTPUT_DIR / "cleaned_sales_data.csv", index=False)
    summary.to_csv(OUTPUT_DIR / "data_quality_summary.csv", index=False)
    (OUTPUT_DIR / "visual_report.html").write_text(
        build_report(clean_df, summary),
        encoding="utf-8",
    )

    print(f"Cleaned rows: {len(clean_df)}")
    print(f"Total revenue: {money(float(clean_df['revenue'].sum()))}")
    print(f"Report written to: {OUTPUT_DIR / 'visual_report.html'}")


if __name__ == "__main__":
    main()

