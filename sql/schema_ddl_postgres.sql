-- ============================================================
-- Customer Revenue Intelligence & Retention Analytics System
-- Star Schema DDL — Postgres dialect (Supabase)
-- Author: Shreenivas
-- Ported from sql/schema_ddl.sql (MySQL). Differences from the
-- MySQL version:
--   - AUTO_INCREMENT -> GENERATED ALWAYS AS IDENTITY
--   - TINYINT(1)      -> BOOLEAN
--   - No "USE <db>"   -> database is selected via the connection
--                        string, not a SQL statement, in Postgres
--   - Explicit indexes on FK columns: Postgres does not
--     auto-index foreign keys the way MySQL does
--   - New table: fact_guest_checkout — persists the guest
--     (null Customer ID) revenue stream that was previously only
--     computed ad hoc in a notebook and never given a real home
-- ============================================================

-- ============================================================
-- DIMENSION TABLE 1: dim_customer
-- ============================================================
CREATE TABLE IF NOT EXISTS dim_customer (
    customer_id     INTEGER         PRIMARY KEY,
    country         VARCHAR(100)    NOT NULL
);

-- ============================================================
-- DIMENSION TABLE 2: dim_product
-- ============================================================
CREATE TABLE IF NOT EXISTS dim_product (
    stock_code      VARCHAR(20)     PRIMARY KEY,
    description     VARCHAR(255)
);

-- ============================================================
-- DIMENSION TABLE 3: dim_date
-- ============================================================
CREATE TABLE IF NOT EXISTS dim_date (
    date_id         DATE            PRIMARY KEY,
    year            INTEGER         NOT NULL,
    month           INTEGER         NOT NULL,
    day             INTEGER         NOT NULL,
    quarter         INTEGER         NOT NULL,
    month_name      VARCHAR(20)     NOT NULL,
    is_q4           BOOLEAN         NOT NULL
);

-- ============================================================
-- FACT TABLE: fact_sales
-- Identified customers only (Customer ID present, cleaned per
-- scripts/clean_data.py rules)
-- ============================================================
CREATE TABLE IF NOT EXISTS fact_sales (
    sale_id         BIGINT          GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    invoice         VARCHAR(20)     NOT NULL,
    customer_id     INTEGER         NOT NULL REFERENCES dim_customer(customer_id),
    stock_code      VARCHAR(20)     NOT NULL REFERENCES dim_product(stock_code),
    date_id         DATE            NOT NULL REFERENCES dim_date(date_id),
    quantity        INTEGER         NOT NULL,
    price           DECIMAL(10,2)   NOT NULL,
    revenue         DECIMAL(10,2)   NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_fact_sales_customer_id ON fact_sales(customer_id);
CREATE INDEX IF NOT EXISTS idx_fact_sales_stock_code   ON fact_sales(stock_code);
CREATE INDEX IF NOT EXISTS idx_fact_sales_date_id      ON fact_sales(date_id);

-- ============================================================
-- FACT TABLE: fact_guest_checkout
-- Null Customer ID rows (guest checkouts) — real revenue, never
-- attributable to a specific customer, so no customer_id FK.
-- Same cleaning rules as fact_sales (no cancellations, no stock
-- adjustments, positive price/quantity) applied except the
-- Customer ID filter, which is inverted.
-- ============================================================
CREATE TABLE IF NOT EXISTS fact_guest_checkout (
    guest_sale_id   BIGINT          GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    invoice         VARCHAR(20)     NOT NULL,
    stock_code      VARCHAR(20)     NOT NULL REFERENCES dim_product(stock_code),
    date_id         DATE            NOT NULL REFERENCES dim_date(date_id),
    country         VARCHAR(100)    NOT NULL,
    quantity        INTEGER         NOT NULL,
    price           DECIMAL(10,2)   NOT NULL,
    revenue         DECIMAL(10,2)   NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_fact_guest_checkout_stock_code ON fact_guest_checkout(stock_code);
CREATE INDEX IF NOT EXISTS idx_fact_guest_checkout_date_id    ON fact_guest_checkout(date_id);
CREATE INDEX IF NOT EXISTS idx_fact_guest_checkout_country    ON fact_guest_checkout(country);

-- ============================================================
-- RFM SEGMENTS TABLE
-- Populated by sql/compute_rfm.sql, run in Postgres using
-- NTILE(5) window functions — computed in SQL, not pandas.
-- ============================================================
CREATE TABLE IF NOT EXISTS rfm_segments (
    customer_id     INTEGER         PRIMARY KEY REFERENCES dim_customer(customer_id),
    recency         INTEGER         NOT NULL,
    frequency       INTEGER         NOT NULL,
    monetary        DECIMAL(12,2)   NOT NULL,
    r_score         INTEGER         NOT NULL,
    f_score         INTEGER         NOT NULL,
    m_score         INTEGER         NOT NULL,
    rfm_score       VARCHAR(5)      NOT NULL,
    rfm_total       INTEGER         NOT NULL,
    segment         VARCHAR(50)     NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_rfm_segments_segment ON rfm_segments(segment);

-- ============================================================
-- VERIFY ALL TABLES CREATED
-- ============================================================
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
