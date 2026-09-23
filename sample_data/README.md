# Sample data

`sample_sales.csv` — 120 synthetic sales orders, generated for demos. It is
deliberately mixed-type so every part of the dashboard has something to work on:

| Column            | Type        | Good for                                  |
|-------------------|-------------|-------------------------------------------|
| `order_id`        | string      | —                                          |
| `order_date`      | date string | —                                          |
| `region`          | categorical | Pie chart, bar chart                       |
| `category`        | categorical | Pie chart                                  |
| `channel`         | categorical | Pie chart                                  |
| `units_sold`      | integer     | Histogram, scatter, regression             |
| `unit_price`      | float       | Scatter, boxplot                           |
| `revenue`         | float       | Regression against `units_sold`, heatmap   |
| `discount_pct`    | float       | Correlation heatmap                        |
| `customer_rating` | float       | Boxplot, histogram                         |

Try: **Scatter** with `units_sold` × `revenue`, then **Pie** on `region`,
then **Heatmap** — three charts is enough to fill the combined dashboard
and produce a multi-page PDF report.
