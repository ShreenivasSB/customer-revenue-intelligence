import plotly.express as px
import streamlit as st

from db import load_rfm_segments, load_segment_summary
from theme import RFM_SEGMENT_ORDER, SEGMENT_COLORS, style
from ui import inject_css, page_header, section

st.set_page_config(page_title="RFM Segmentation", page_icon="🧩", layout="wide")
inject_css()
page_header("🧩", "RFM Segmentation")
st.caption(
    "Recency / Frequency / Monetary scoring via SQL `NTILE(5)` quintiles against "
    "the Supabase warehouse (`sql/compute_rfm.sql`) — segments carry a real rank, "
    "so they share one ordinal blue ramp (darker = higher value) rather than "
    "unrelated colors."
)

summary = load_segment_summary()
rfm = load_rfm_segments()

st.info(
    "Segment counts here are computed live via SQL `NTILE(5)`. The README/Power BI "
    "numbers were computed via pandas `pd.qcut` in the original notebook. Both follow "
    "the identical rule waterfall and agree closely, but small differences (a handful "
    "of customers per segment) are expected — `pd.qcut` and SQL `NTILE` break quantile "
    "ties slightly differently. Worth stating plainly rather than papering over.",
    icon="ℹ️",
)

st.write("")
col1, col2 = st.columns([3, 2])

with col1:
    with st.container(border=True):
        section("Revenue Concentration by Segment")
        order = [s for s in RFM_SEGMENT_ORDER if s in summary["segment"].values]
        fig = px.bar(
            summary, x="segment", y="total_revenue",
            category_orders={"segment": order},
            color="segment", color_discrete_map=SEGMENT_COLORS,
        )
        fig.update_yaxes(title="Total Revenue (£)", tickprefix="£")
        fig.update_xaxes(title=None)
        st.plotly_chart(style(fig, legend=False), use_container_width=True)

with col2:
    with st.container(border=True):
        section("Segment Scorecard")
        show = summary.rename(columns={
            "segment": "Segment", "customer_count": "Customers",
            "total_revenue": "Revenue (£)", "avg_clv": "Avg CLV (£)",
            "avg_recency_days": "Avg Recency (d)", "avg_frequency": "Avg Frequency",
        })
        st.dataframe(show, hide_index=True, use_container_width=True, height=400)

st.write("")
with st.container(border=True):
    section("Customer-Level View — Recency vs Monetary")
    segments_available = [s for s in RFM_SEGMENT_ORDER if s in rfm["segment"].values]
    picked = st.multiselect(
        "Filter by segment", options=segments_available,
        default=["Champion", "At Risk", "Loyal Customer"],
    )
    filtered = rfm[rfm["segment"].isin(picked)] if picked else rfm

    fig3 = px.scatter(
        filtered, x="recency", y="monetary", size="frequency", color="segment",
        color_discrete_map=SEGMENT_COLORS,
        category_orders={"segment": segments_available},
        hover_data=["customer_id", "country", "frequency"],
        labels={"recency": "Recency (days since last purchase)", "monetary": "Monetary (£)"},
        size_max=28,
    )
    fig3.update_yaxes(tickprefix="£")
    st.plotly_chart(style(fig3, height=480, legend=True), use_container_width=True)

st.write("")
with st.container(border=True):
    section("Drill-down: customers in the selected segment(s)")
    st.dataframe(
        filtered.sort_values("monetary", ascending=False)
        .rename(columns={"customer_id": "Customer ID", "recency": "Recency (d)",
                          "frequency": "Frequency", "monetary": "Monetary (£)",
                          "segment": "Segment", "country": "Country"})
        [["Customer ID", "Segment", "Country", "Recency (d)", "Frequency", "Monetary (£)"]],
        hide_index=True, use_container_width=True, height=350,
    )
    st.caption(f"{len(filtered):,} customers match the current filter.")
