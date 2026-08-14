import streamlit as st

from db import load_kpis, load_rfm_segments, load_survival_features
from ui import inject_css, page_header

st.set_page_config(page_title="Recommendations", page_icon="💡", layout="wide")
inject_css()
page_header("💡", "Business Recommendations")
st.caption(
    "Six prioritised actions, each tied to a quantified figure from the analysis. "
    "Figures below recompute live from the warehouse — see the caption on each card."
)

kpis = load_kpis()
rfm = load_rfm_segments()
survival = load_survival_features()

at_risk = rfm[rfm["segment"] == "At Risk"]
champions = rfm[rfm["segment"] == "Champion"]

recs = [
    dict(
        icon="🎯", title="Fix the One-Hit Wonder Problem",
        value="£174K annual upside",
        body="79% of customers never return after their first purchase. Month-1 "
             "retention averages ~21% across 25 cohorts. A Day-7 thank-you email and "
             "Day-30 discount sequence (10–15% offer) is low-cost. Even 10% recovery "
             "on first-time buyers adds ~£174,000/year.",
    ),
    dict(
        icon="🔄", title="Recover Revenue from At-Risk Customers",
        value=f"£{at_risk['monetary'].sum():,.0f} recoverable",
        body=f"{len(at_risk):,} customers classified At Risk (SQL-live count) haven't "
             f"purchased in an average of {at_risk['recency'].mean():.0f} days. Their lead "
             "recovery product is WHITE HANGING HEART T-LIGHT HOLDER. A 20% recovery "
             f"rate alone secures £{at_risk['monetary'].sum() * 0.2:,.0f} immediately.",
    ),
    dict(
        icon="📦", title="Prepare for the Observed Q4 Pattern",
        value="Not statistically proven, still worth planning for",
        body="Q4 revenue was ~41% higher than non-Q4 in both observed years, but with "
             "only 25 months of data this doesn't clear statistical significance "
             "(Welch's p=0.052). Treat scaled Q4 ad spend and October 1 stock "
             "readiness as a well-supported working assumption, not a proven fact.",
    ),
    dict(
        icon="👑", title="Protect the Champions",
        value=f"£{champions['monetary'].sum():,.0f} at stake",
        body=f"{len(champions):,} Champions (SQL-live count) generate the majority of "
             "revenue at an average CLV far above every other segment. A VIP tier — "
             "early access, free shipping, dedicated support for the top 50 — "
             "protects this concentration directly.",
    ),
    dict(
        icon="🧾", title="Convert Guest Checkouts to Accounts",
        value=f"£{kpis['guest_revenue'] * 0.2:,.0f} trackable at 20% conversion",
        body=f"£{kpis['guest_revenue']:,.0f} across {kpis['guest_rows']:,} guest-checkout "
             "transactions is currently unattributed to any customer record — 98.8% "
             "UK-based. A post-checkout 5%-off account-creation prompt is low-friction.",
    ),
    dict(
        icon="⏳", title="Prioritise Outreach by Churn Risk Score",
        value=f"{(~survival['event_churned']).sum():,} active customers ranked",
        body="The Cox partial hazard score (Churn Risk page) ranks every active "
             "customer by relative churn risk, driven overwhelmingly by order "
             "frequency, not recency alone — catching elevated risk *before* a "
             "customer crosses the 180-day lapsed threshold used in Recommendation #2.",
    ),
]

st.write("")
for i in range(0, len(recs), 2):
    cols = st.columns(2)
    for col, rec in zip(cols, recs[i:i + 2]):
        with col:
            with st.container(border=True):
                st.markdown(
                    f"<div style='font-size:1.6rem;line-height:1;margin-bottom:.4rem;'>{rec['icon']}</div>",
                    unsafe_allow_html=True,
                )
                st.markdown(f"##### {rec['title']}")
                st.markdown(f"**{rec['value']}**")
                st.write(rec["body"])

st.write("")
st.caption(
    "Full write-up, statistical validation, and survival-analysis methodology in the "
    "[project README](https://github.com/ShreenivasSB/customer-revenue-intelligence)."
)
