import pandas as pd
import plotly.express as px
import streamlit as st

from db import load_monthly_revenue, load_top_products
from theme import CATEGORICAL, STATUS, style
from ui import inject_css, page_header, section, tile_row

st.set_page_config(page_title="Revenue & Seasonality", page_icon="📈", layout="wide")
inject_css()
page_header("📈", "Revenue & Seasonality")

mr = load_monthly_revenue()
mr["month_start"] = pd.to_datetime(mr["month_start"])
mr["period"] = mr["is_q4"].map({True: "Q4", False: "Non-Q4"})

st.write("")
with st.container(border=True):
    section("Monthly Revenue — Q4 vs Non-Q4")
    fig = px.bar(
        mr, x="month_start", y="revenue", color="period",
        color_discrete_map={"Q4": CATEGORICAL[1], "Non-Q4": CATEGORICAL[0]},
    )
    fig.update_yaxes(title="Revenue (£)", tickprefix="£")
    fig.update_xaxes(title=None)
    st.plotly_chart(style(fig, legend=True), use_container_width=True)

avg_q4 = mr.loc[mr["is_q4"], "revenue"].mean()
avg_non_q4 = mr.loc[~mr["is_q4"], "revenue"].mean()
uplift = (avg_q4 / avg_non_q4 - 1) * 100

st.write("")
tile_row([
    dict(label="Avg Q4 Monthly Revenue", value=f"£{avg_q4:,.0f}",
         sub=f"{int(mr['is_q4'].sum())} Q4 months", accent=CATEGORICAL[1]),
    dict(label="Avg Non-Q4 Monthly Revenue", value=f"£{avg_non_q4:,.0f}",
         sub=f"{int((~mr['is_q4']).sum())} non-Q4 months", accent=CATEGORICAL[0]),
    dict(label="Observed Uplift", value=f"{uplift:.1f}%",
         sub="not statistically significant", accent=STATUS["warning"]),
])

st.write("")
st.warning(
    "**Not statistically significant.** This 41% observed Q4 uplift does not clear "
    "the bar for statistical significance with only 25 months of data (7 Q4, 18 "
    "non-Q4). Reported here as observed, not proven — see the honest accounting below.",
    icon="⚠️",
)

st.write("")
with st.container(border=True):
    section("Statistical Validation")
    st.caption(
        "Precomputed in `notebooks/07_statistical_tests.ipynb` (Welch's t-test, "
        "Shapiro-Wilk, Levene's, Mann-Whitney U) — shown here as a static, documented "
        "result, not re-run live on every page load, since these are one-time "
        "validations of the analysis methodology, not a metric that changes with fresh data."
    )

    validation = pd.DataFrame([
        {"Test": "Champion vs Non-Champion revenue", "Result": "Significant",
         "Welch's p": "<0.0001", "Mann-Whitney p": "<0.0001",
         "Interpretation": "Champions are statistically distinct as a revenue group"},
        {"Test": "UK vs Non-UK order value", "Result": "Significant",
         "Welch's p": "<0.0001", "Mann-Whitney p": "<0.0001",
         "Interpretation": "Non-UK customers spend £441 more per order"},
        {"Test": "RFM segment distribution (Chi-Square)", "Result": "Significant",
         "Welch's p": "~0.000", "Mann-Whitney p": "n/a",
         "Interpretation": "Segment sizes are not randomly distributed"},
        {"Test": "Q4 vs Non-Q4 monthly revenue volume", "Result": "Not significant",
         "Welch's p": "0.052", "Mann-Whitney p": "0.055",
         "Interpretation": "Unequal variance (Levene's p=0.02) invalidated the original "
                            "Student's t-test result (p=0.003)"},
        {"Test": "Q4 vs Non-Q4 AOV (order size)", "Result": "Not significant",
         "Welch's p": "0.697", "Mann-Whitney p": "0.336",
         "Interpretation": "Q4 lift, where real, is volume-driven not spend-per-order-driven"},
    ])

    def _highlight(row):
        color = STATUS["good"] if row["Result"] == "Significant" else STATUS["warning"]
        return [f"color: {color}; font-weight: 600" if col == "Result" else "" for col in row.index]

    st.dataframe(validation.style.apply(_highlight, axis=1), hide_index=True, use_container_width=True)

st.write("")
with st.container(border=True):
    section("Top Products by Revenue")
    n = st.slider("Show top N products", 5, 30, 15)
    products = load_top_products(n)
    fig2 = px.bar(products.sort_values("revenue"), x="revenue", y="description", orientation="h")
    fig2.update_traces(marker_color=CATEGORICAL[0])
    fig2.update_xaxes(title="Revenue (£)", tickprefix="£")
    fig2.update_yaxes(title=None)
    st.plotly_chart(style(fig2, height=max(400, n * 24)), use_container_width=True)
