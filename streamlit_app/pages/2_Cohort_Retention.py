import pandas as pd
import plotly.express as px
import streamlit as st

from db import load_cohort_activity
from theme import CATEGORICAL, SEQUENTIAL_BLUE, style
from ui import inject_css, page_header, section, tile_row

st.set_page_config(page_title="Cohort Retention", page_icon="🔁", layout="wide")
inject_css()
page_header("🔁", "Cohort Retention")
st.caption(
    "Month-0 to Month-N retention per acquisition cohort, computed live from "
    "`fact_sales` (same logic as `sql/cohort_queries.sql`, ported to Postgres). "
    "Cell shade = % of the cohort still active — one hue, light→dark, since "
    "this is a magnitude, not an identity."
)

activity = load_cohort_activity()
activity["cohort_month"] = pd.to_datetime(activity["cohort_month"])
activity["month_index"] = activity["month_index"].astype(int)

pivot = activity.pivot(index="cohort_month", columns="month_index", values="active_customers")
cohort_size = pivot[0]
retention = pivot.div(cohort_size, axis=0) * 100

st.write("")
with st.container(border=True):
    section("Retention Heatmap (%)")
    max_month = st.slider(
        "Months since acquisition to show", min_value=3, max_value=int(retention.columns.max()),
        value=min(12, int(retention.columns.max())),
    )
    view = retention.loc[:, :max_month]
    view.index = view.index.strftime("%Y-%m")

    fig = px.imshow(
        view, color_continuous_scale=SEQUENTIAL_BLUE, aspect="auto",
        labels=dict(x="Months since acquisition", y="Acquisition cohort", color="Retention %"),
        text_auto=".0f",
    )
    fig.update_traces(hovertemplate="Cohort %{y}<br>Month %{x}<br>%{z:.1f}% retained<extra></extra>")
    st.plotly_chart(style(fig, height=560), use_container_width=True)

st.write("")
m1 = retention[1].dropna()
best_idx = m1.idxmax()
worst_idx = m1.idxmin()
tile_row([
    dict(label="Avg Month-1 Retention", value=f"{m1.mean():.2f}%", sub="across all cohorts", accent=CATEGORICAL[0]),
    dict(label="Best Month-1 Cohort", value=f"{m1.max():.2f}%", sub=best_idx.strftime("%b %Y"), accent=CATEGORICAL[2]),
    dict(label="Worst Month-1 Cohort", value=f"{m1.min():.2f}%", sub=worst_idx.strftime("%b %Y"), accent=CATEGORICAL[7]),
])

st.caption(
    "Matches the README's headline finding: 79% of customers never return after "
    "their first purchase, and average Month-1 retention sits around 21% across "
    "all 25 monthly cohorts."
)
