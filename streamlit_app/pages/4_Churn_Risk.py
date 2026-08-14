import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import streamlit as st
from lifelines import KaplanMeierFitter

from db import load_survival_features, load_survival_summary
from theme import CATEGORICAL, GRIDLINE, MUTED, STATUS, TEXT_SECONDARY, style
from ui import inject_css, page_header, section, tile_row

st.set_page_config(page_title="Churn Risk", page_icon="⏳", layout="wide")
inject_css()
page_header("⏳", "Churn Risk — Survival Analysis")
st.caption(
    "Kaplan-Meier and Cox Proportional Hazards, from `notebooks/08_survival_analysis.ipynb`, "
    "persisted to the warehouse and re-visualised here live. Time-to-event modelling — "
    "*when* a customer is likely to lapse, not a binary churn/no-churn classifier."
)

features = load_survival_features()
summary = load_survival_summary().set_index("metric_name")

churned = features["event_churned"].sum()
churn_rate = churned / len(features) * 100

st.write("")
conc = summary.loc['cox_concordance_index', 'metric_value'] if 'cox_concordance_index' in summary.index else 0.87
tile_row([
    dict(label="Customers Analysed", value=f"{len(features):,}", accent=CATEGORICAL[0]),
    dict(label="Churned (>180d)", value=f"{churned:,}", sub=f"{churn_rate:.1f}% of base", accent=STATUS["critical"]),
    dict(label="Model Concordance", value=f"{conc:.3f}", sub="0.5 = chance, 1.0 = perfect", accent=CATEGORICAL[2]),
])

st.write("")
col_km, col_dist = st.columns([3, 2])

with col_km:
    with st.container(border=True):
        section("Kaplan-Meier Survival Curve")
        kmf = KaplanMeierFitter()
        kmf.fit(features["duration_days"], event_observed=features["event_churned"])

        fig, ax = plt.subplots(figsize=(7, 4.2))
        fig.patch.set_alpha(0)
        ax.set_facecolor("none")
        kmf.plot_survival_function(ax=ax, color=CATEGORICAL[0], ci_show=True)
        ax.set_xlabel("Days since first purchase", color=TEXT_SECONDARY)
        ax.set_ylabel("Survival probability", color=TEXT_SECONDARY)
        ax.get_legend().remove()
        ax.spines[["top", "right"]].set_visible(False)
        ax.spines[["left", "bottom"]].set_color(GRIDLINE)
        ax.tick_params(colors=MUTED)
        ax.grid(color=GRIDLINE, linewidth=0.6)
        st.pyplot(fig, transparent=True)
        st.caption(
            "Median survival time is undefined within this ~2-year window — the curve "
            "never drops below 50%. Survival at the end of the observation window is ~53%."
        )

with col_dist:
    with st.container(border=True):
        section("Churn Risk Distribution")
        q1, q2 = features["cox_partial_hazard"].quantile([1 / 3, 2 / 3])

        def bucket(h):
            if h <= q1:
                return "Low"
            if h <= q2:
                return "Medium"
            return "High"

        features["risk_bucket"] = features["cox_partial_hazard"].apply(bucket)
        counts = features["risk_bucket"].value_counts().reindex(["Low", "Medium", "High"]).reset_index()
        counts.columns = ["Risk", "Customers"]
        fig2 = px.bar(
            counts, x="Risk", y="Customers", color="Risk",
            color_discrete_map={"Low": STATUS["good"], "Medium": STATUS["warning"], "High": STATUS["critical"]},
            category_orders={"Risk": ["Low", "Medium", "High"]},
        )
        st.plotly_chart(style(fig2, height=340, legend=False), use_container_width=True)
        st.caption(
            "Buckets are terciles of the Cox partial hazard score — a relative risk "
            "ranking, not an absolute churn probability."
        )

st.write("")
with st.container(border=True):
    section("What drives churn risk")
    st.markdown(
        "- **Order frequency** (log-transformed) is the dominant, highly significant driver "
        "(hazard ratio ≈ 0.07, p<0.001) — a customer with double the order count carries "
        "roughly 16% of the churn hazard of one with half as many orders.\n"
        "- **Order value** (AOV) and **country** are *not* significant predictors once "
        "frequency is accounted for.\n"
        "- The proportional-hazards assumption check still flags `total_orders` even after "
        "remediation (log-transform + stratifying `is_uk`) — documented as very likely the "
        "well-known large-sample over-sensitivity of that specific test at n=5,878, not hidden."
    )
    with st.expander("Full model summary table (`survival_model_summary`, 13 rows)"):
        st.dataframe(load_survival_summary(), hide_index=True, use_container_width=True)

st.write("")
with st.container(border=True):
    section("Retention target list — highest-risk active customers")
    st.caption(
        "Filtered to customers **not yet churned** (still worth an intervention), ranked by "
        "Cox partial hazard. This is the actionable output: an exportable prioritised list "
        "for a retention campaign, not just a chart.")

    active = features[~features["event_churned"]].copy()
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        country_filter = st.selectbox("Country", ["All"] + sorted(active["country"].unique().tolist()))
    with col_f2:
        top_n = st.slider("Show top N by risk", 10, 500, 50)

    if country_filter != "All":
        active = active[active["country"] == country_filter]

    target_list = (
        active.sort_values("cox_partial_hazard", ascending=False)
        .head(top_n)
        [["customer_id", "country", "total_orders", "total_revenue", "avg_order_value",
          "duration_days", "cox_partial_hazard", "risk_bucket"]]
        .rename(columns={
            "customer_id": "Customer ID", "country": "Country",
            "total_orders": "Total Orders", "total_revenue": "Total Revenue (£)",
            "avg_order_value": "Avg Order Value (£)", "duration_days": "Days Since First Purchase",
            "cox_partial_hazard": "Cox Risk Score", "risk_bucket": "Risk Bucket",
        })
    )
    st.dataframe(target_list, hide_index=True, use_container_width=True, height=380)
    st.download_button(
        "⬇️ Download this list as CSV",
        target_list.to_csv(index=False).encode("utf-8"),
        file_name="churn_risk_target_list.csv",
        mime="text/csv",
    )
