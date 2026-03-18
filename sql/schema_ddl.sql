-- ============================================================
-- Customer Revenue Intelligence & Retention Analytics System
-- Star Schema DDL
-- Author: Shreenivas
-- Database: customer_revenue_intelligence
-- ============================================================

USE customer_revenue_intelligence;

-- ============================================================
-- DIMENSION TABLE 1: dim_customer
-- ============================================================
CREATE TABLE IF NOT EXISTS dim_customer (
    customer_id     INT             PRIMARY KEY,
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
    year            INT             NOT NULL,
    month           INT             NOT NULL,
    day             INT             NOT NULL,
    quarter         INT             NOT NULL,
    month_name      VARCHAR(20)     NOT NULL,
    is_q4           TINYINT(1)      NOT NULL
);

-- ============================================================
-- FACT TABLE: fact_sales
-- ============================================================
CREATE TABLE IF NOT EXISTS fact_sales (
    sale_id         BIGINT          AUTO_INCREMENT PRIMARY KEY,
    invoice         VARCHAR(20)     NOT NULL,
    customer_id     INT             NOT NULL,
    stock_code      VARCHAR(20)     NOT NULL,
    date_id         DATE            NOT NULL,
    quantity        INT             NOT NULL,
    price           DECIMAL(10,2)   NOT NULL,
    revenue         DECIMAL(10,2)   NOT NULL,
    FOREIGN KEY (customer_id)   REFERENCES dim_customer(customer_id),
    FOREIGN KEY (stock_code)    REFERENCES dim_product(stock_code),
    FOREIGN KEY (date_id)       REFERENCES dim_date(date_id)
);

-- ============================================================
-- RFM SEGMENTS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS rfm_segments (
    customer_id     INT             PRIMARY KEY,
    recency         INT             NOT NULL,
    frequency       INT             NOT NULL,
    monetary        DECIMAL(12,2)   NOT NULL,
    r_score         INT             NOT NULL,
    f_score         INT             NOT NULL,
    m_score         INT             NOT NULL,
    rfm_score       VARCHAR(5)      NOT NULL,
    rfm_total       INT             NOT NULL,
    segment         VARCHAR(50)     NOT NULL,
    FOREIGN KEY (customer_id)   REFERENCES dim_customer(customer_id)
);

-- ============================================================
-- VERIFY ALL TABLES CREATED
-- ============================================================
SHOW TABLES;