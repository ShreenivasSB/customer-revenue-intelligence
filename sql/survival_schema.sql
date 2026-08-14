-- ============================================================
-- Customer Revenue Intelligence & Retention Analytics System
-- Survival Analysis result tables — Postgres dialect (Supabase)
--
-- Populated by notebooks/08_survival_analysis.ipynb (Kaplan-Meier +
-- Cox Proportional Hazards on retention/time-to-churn). Kept separate
-- from schema_ddl_postgres.sql since this is notebook-driven, not
-- part of the scheduled ETL pipeline — re-run the notebook manually
-- to refresh these tables (idempotent: TRUNCATE + INSERT).
-- ============================================================

-- ============================================================
-- Per-customer survival features + Cox partial hazard risk score
-- ============================================================
CREATE TABLE IF NOT EXISTS survival_customer_features (
    customer_id          INTEGER         PRIMARY KEY REFERENCES dim_customer(customer_id),
    first_purchase_date  DATE            NOT NULL,
    last_purchase_date   DATE            NOT NULL,
    duration_days        INTEGER         NOT NULL,
    event_churned        BOOLEAN         NOT NULL,
    total_orders          INTEGER        NOT NULL,
    total_revenue          DECIMAL(12,2) NOT NULL,
    avg_order_value        DECIMAL(10,2) NOT NULL,
    is_uk                   BOOLEAN      NOT NULL,
    cox_partial_hazard     DECIMAL(14,6) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_survival_customer_features_event ON survival_customer_features(event_churned);

-- ============================================================
-- Model/test summary metrics — flexible key-value table so it can
-- hold both numeric KPIs (hazard ratios, p-values) and textual notes
-- (e.g. documented caveats about assumption checks) without a rigid
-- per-metric schema.
-- ============================================================
CREATE TABLE IF NOT EXISTS survival_model_summary (
    metric_name    VARCHAR(100)    PRIMARY KEY,
    metric_value   DECIMAL(18,6),
    metric_text    VARCHAR(500)
);
