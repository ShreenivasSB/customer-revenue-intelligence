"""
Customer Revenue Intelligence — Streamlit reporting app.

An interactive BI layer on top of the same Supabase Postgres warehouse that
feeds the Power BI dashboard — filters and drill-downs the static PNGs and
the fixed 4-page report can't offer. This is a reporting/analytics app, not
a deployed model: every number here is a live SQL aggregate against the
warehouse (see streamlit_app/db.py), not a prediction.
"""
import plotly.express as px
import streamlit as st

from db import load_kpis, load_monthly_revenue, load_revenue_by_country
from theme import CATEGORICAL, style
from ui import hero, inject_css, section, tile_row

st.set_page_config(
    page_title="Customer Revenue Intelligence",
    page_icon="📊",
    layout="wide",
)
inject_css()

hero(
    "📊 Customer Revenue Intelligence",
    "UK e-commerce, Dec 2009 – Dec 2011 · 5,878 customers · £20.6M total revenue. "
    "Live queries against the Supabase warehouse — not a static export — with "
    "filters, drill-downs, and a churn-risk target list the fixed dashboard can't offer.",
    badges=["UCI Online Retail II", "Supabase Postgres", "Live SQL", "lifelines survival analysis"],
)

with st.sidebar:
    st.markdown("### 📊 CRI Reporting")
    st.markdown(
        "Companion app to the project's "
        "[Power BI dashboard](https://app.powerbi.com/view?r=eyJrIjoiODBhZWIyMjUtMDk1NS00MjYyLThiM2MtMDEwYjI5MTVkYzIzIiwidCI6ImRiMTljMjFjLWFlODctNDY4Yi05MjQ4LTFhMjkyZDM3OWRjMiJ9) "
        "and [GitHub repo](https://github.com/ShreenivasSB/customer-revenue-intelligence). "
        "Same warehouse, same numbers — this layer adds ad-hoc filtering, a "
        "churn-risk drill-down, and a downloadable retention target list."
    )
    st.divider()
    st.markdown(
        "**Pages**\n"
        "- Executive Overview *(this page)*\n"
        "- 🧩 RFM Segmentation\n"
        "- 🔁 Cohort Retention\n"
        "- 📈 Revenue & Seasonality\n"
        "- ⏳ Churn Risk\n"
        "- 💡 Recommendations"
    )

kpis = load_kpis()

section("Executive KPIs")
tile_row([
    dict(label="Total Revenue", value=f"£{kpis['total_revenue']:,.0f}", accent=CATEGORICAL[0]),
    dict(label="Customers", value=f"{kpis['total_customers']:,}", accent=CATEGORICAL[2]),
    dict(label="Orders", value=f"{kpis['total_orders']:,}", accent=CATEGORICAL[6]),
    dict(label="Avg Order Value", value=f"£{kpis['aov']:,.2f}", accent=CATEGORICAL[3]),
    dict(label="+ Guest Checkout", value=f"£{kpis['guest_revenue']:,.0f}",
         sub=f"{kpis['guest_rows']:,} unattributed transactions", accent=CATEGORICAL[1]),
])

st.write("")
with st.container(border=True):
    section("Monthly Revenue Trend")
    mr = load_monthly_revenue()
    fig = px.line(mr, x="month_start", y="revenue", markers=True)
    fig.update_traces(line_color=CATEGORICAL[0], line_width=2.5,
                       marker=dict(size=6, color=CATEGORICAL[0]))
    q4 = mr[mr["is_q4"]]
    fig.add_scatter(
        x=q4["month_start"], y=q4["revenue"], mode="markers", name="Q4 month",
        marker=dict(size=10, color=CATEGORICAL[1], symbol="circle",
                    line=dict(width=2, color="white")),
    )
    fig.update_yaxes(title="Revenue (£)", tickprefix="£")
    fig.update_xaxes(title=None)
    st.plotly_chart(style(fig, height=360, legend=True), use_container_width=True)
    st.caption(
        "Orange markers = Q4 months. The visible Q4 uplift is real but not "
        "statistically significant at this sample size — see Revenue & Seasonality."
    )

st.write("")
with st.container(border=True):
    section("Revenue by Country")
    rc = load_revenue_by_country(10)
    fig2 = px.bar(rc.sort_values("revenue"), x="revenue", y="country", orientation="h")
    fig2.update_traces(marker_color=CATEGORICAL[0])
    fig2.update_xaxes(title="Revenue (£)", tickprefix="£")
    fig2.update_yaxes(title=None)
    # Full-width chart: automargin (set in style()) has enough room here to
    # fit "United Kingdom" without a hand-tuned margin — that only became
    # necessary, and still wasn't enough, in the cramped 1/3-width column
    # this used to live in.
    st.plotly_chart(style(fig2, height=380), use_container_width=True)
    st.caption(f"UK: {rc.iloc[0]['revenue_pct']:.1f}% of identified-customer revenue.")

st.write("")
st.info(
    "💡 **Business Problem Statement:** which customers drive revenue, why "
    "most never return, whether the Q4 spike is statistically real, where "
    "untracked revenue is hiding, and what to do about all four next week. "
    "See the **Recommendations** page for the six actions this analysis supports.",
    icon="💡",
)
