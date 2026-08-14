"""
db.py — Supabase Postgres connection and cached data-loading queries.

Credentials: reads DATABASE_URL from Streamlit's secrets manager first (how
Streamlit Community Cloud is configured — see the deployment note in the
project README), falling back to the repo-root .env file for local runs
(same .env used by scripts/load_to_supabase.py, via python-dotenv).
"""
import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()


def _database_url() -> str:
    try:
        if "DATABASE_URL" in st.secrets:
            return st.secrets["DATABASE_URL"]
    except Exception:
        pass
    url = os.environ.get("DATABASE_URL")
    if not url:
        st.error(
            "DATABASE_URL is not configured. Locally: copy .env.example to "
            ".env at the repo root. On Streamlit Community Cloud: add it "
            "under App settings -> Secrets."
        )
        st.stop()
    return url


@st.cache_resource
def get_engine():
    url = _database_url()
    if url.startswith("postgresql://") and "+psycopg2" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return create_engine(url, pool_pre_ping=True)


def _query(sql: str, params: dict | None = None) -> pd.DataFrame:
    with get_engine().connect() as conn:
        return pd.read_sql(text(sql), conn, params=params or {})


# ---------------------------------------------------------------------------
# Cached loaders — ttl=3600 matches the pipeline's own weekly refresh cadence
# (the underlying warehouse doesn't change more often than that; see the
# Automated Data Pipeline section of the main README).
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600)
def load_kpis() -> dict:
    # NOTE: .iloc[0].to_dict() would upcast every value in the row to a single
    # common dtype (float), turning integer counts like total_customers into
    # "5878.0". .to_dict("records")[0] keeps each column's own dtype instead.
    row = _query("""
        SELECT
            (SELECT ROUND(SUM(revenue), 2) FROM fact_sales)            AS total_revenue,
            (SELECT COUNT(DISTINCT customer_id) FROM fact_sales)       AS total_customers,
            (SELECT COUNT(DISTINCT invoice) FROM fact_sales)           AS total_orders,
            (SELECT ROUND(SUM(revenue) / COUNT(DISTINCT invoice), 2)
                FROM fact_sales)                                       AS aov,
            (SELECT ROUND(SUM(revenue), 2) FROM fact_guest_checkout)   AS guest_revenue,
            (SELECT COUNT(*) FROM fact_guest_checkout)                 AS guest_rows
    """).to_dict("records")[0]
    for int_field in ("total_customers", "total_orders", "guest_rows"):
        row[int_field] = int(row[int_field])
    return row


@st.cache_data(ttl=3600)
def load_monthly_revenue() -> pd.DataFrame:
    return _query("""
        SELECT d.year, d.month, d.month_name, d.is_q4,
               MIN(d.date_id)                       AS month_start,
               ROUND(SUM(f.revenue), 2)              AS revenue,
               COUNT(DISTINCT f.invoice)              AS orders
        FROM fact_sales f
        JOIN dim_date d ON f.date_id = d.date_id
        GROUP BY d.year, d.month, d.month_name, d.is_q4
        ORDER BY d.year, d.month
    """)


@st.cache_data(ttl=3600)
def load_revenue_by_country(limit: int = 10) -> pd.DataFrame:
    return _query("""
        SELECT c.country,
               ROUND(SUM(f.revenue), 2)             AS revenue,
               COUNT(DISTINCT f.customer_id)         AS customers,
               ROUND(SUM(f.revenue) * 100.0 /
                     (SELECT SUM(revenue) FROM fact_sales), 2) AS revenue_pct
        FROM fact_sales f
        JOIN dim_customer c ON f.customer_id = c.customer_id
        GROUP BY c.country
        ORDER BY revenue DESC
        LIMIT :limit
    """, {"limit": limit})


@st.cache_data(ttl=3600)
def load_rfm_segments() -> pd.DataFrame:
    return _query("""
        SELECT r.customer_id, r.recency, r.frequency, r.monetary,
               r.r_score, r.f_score, r.m_score, r.rfm_score, r.segment,
               c.country
        FROM rfm_segments r
        JOIN dim_customer c ON r.customer_id = c.customer_id
    """)


@st.cache_data(ttl=3600)
def load_segment_summary() -> pd.DataFrame:
    return _query("""
        SELECT segment,
               COUNT(*)                                        AS customer_count,
               ROUND(SUM(monetary), 2)                          AS total_revenue,
               ROUND(AVG(monetary), 2)                          AS avg_clv,
               ROUND(AVG(recency), 1)                           AS avg_recency_days,
               ROUND(AVG(frequency), 1)                         AS avg_frequency
        FROM rfm_segments
        GROUP BY segment
        ORDER BY total_revenue DESC
    """)


@st.cache_data(ttl=3600)
def load_cohort_activity() -> pd.DataFrame:
    """One row per (cohort_month, month_index) with the count of customers
    from that cohort still active that many months after acquisition.
    Mirrors the CTE logic in sql/cohort_queries.sql, ported to Postgres."""
    return _query("""
        WITH first_purchase AS (
            SELECT customer_id, date_trunc('month', MIN(date_id))::date AS cohort_month
            FROM fact_sales
            GROUP BY customer_id
        ),
        monthly_activity AS (
            SELECT DISTINCT customer_id, date_trunc('month', date_id)::date AS activity_month
            FROM fact_sales
        )
        SELECT
            fp.cohort_month,
            (DATE_PART('year', ma.activity_month) - DATE_PART('year', fp.cohort_month)) * 12
                + (DATE_PART('month', ma.activity_month) - DATE_PART('month', fp.cohort_month))
                AS month_index,
            COUNT(DISTINCT ma.customer_id) AS active_customers
        FROM first_purchase fp
        JOIN monthly_activity ma ON fp.customer_id = ma.customer_id
        GROUP BY fp.cohort_month, month_index
        ORDER BY fp.cohort_month, month_index
    """)


@st.cache_data(ttl=3600)
def load_survival_features() -> pd.DataFrame:
    return _query("""
        SELECT s.customer_id, s.first_purchase_date, s.last_purchase_date,
               s.duration_days, s.event_churned, s.total_orders,
               s.total_revenue, s.avg_order_value, s.is_uk,
               s.cox_partial_hazard, c.country
        FROM survival_customer_features s
        JOIN dim_customer c ON s.customer_id = c.customer_id
    """)


@st.cache_data(ttl=3600)
def load_survival_summary() -> pd.DataFrame:
    return _query("SELECT metric_name, metric_value, metric_text FROM survival_model_summary")


@st.cache_data(ttl=3600)
def load_top_products(limit: int = 15) -> pd.DataFrame:
    return _query("""
        SELECT p.stock_code, p.description,
               ROUND(SUM(f.revenue), 2)   AS revenue,
               SUM(f.quantity)             AS units_sold
        FROM fact_sales f
        JOIN dim_product p ON f.stock_code = p.stock_code
        GROUP BY p.stock_code, p.description
        ORDER BY revenue DESC
        LIMIT :limit
    """, {"limit": limit})
