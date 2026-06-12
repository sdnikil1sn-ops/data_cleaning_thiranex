# Data Cleaning & Visualization Project

This project cleans a raw sales dataset, prepares it for analysis, and creates a visual report of key business insights.

## Features

- Handles missing values in customer, region, category, quantity, unit price, and order date fields.
- Removes duplicate records.
- Detects and caps outliers with the IQR method.
- Creates derived fields such as revenue, month, and order value band.
- Exports cleaned data and an HTML dashboard-style report.
  
## Link

```web
https://github.com/sdnikil1sn-ops/data_cleaning_thiranex
```

## Project Structure

```text
data/
  raw_sales_data.csv
outputs/
  cleaned_sales_data.csv
  data_quality_summary.csv
  visual_report.html
src/
  clean_and_visualize.py
```

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
python src/clean_and_visualize.py
```

The script writes the cleaned dataset and report to the `outputs` folder.

## Expected Outcome

After running the project, you will have:

- A cleaned sales dataset ready for analysis.
- A data quality summary showing missing values, duplicate rows, and outlier handling.
- A visual report with revenue by region, revenue by category, monthly revenue trend, and top products.

