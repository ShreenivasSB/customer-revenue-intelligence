-- ============================================================
-- Customer Revenue Intelligence & Retention Analytics System
-- Cohort Analysis Queries
-- Author: Shreenivas
-- ============================================================

USE customer_revenue_intelligence;

-- ============================================================
-- QUERY 1: Customer First Purchase Month (Cohort Assignment)
-- ============================================================
WITH customer_cohort AS (
    SELECT
        customer_id,
        DATE_FORMAT(MIN(date_id), '%Y-%m')  AS cohort_month,
        MIN(date_id)                         AS first_purchase_date
    FROM fact_sales
    GROUP BY customer_id
)
SELECT
    cohort_month,
    COUNT(customer_id)                       AS cohort_size
FROM customer_cohort
GROUP BY cohort_month
ORDER BY cohort_month;

-- ============================================================
-- QUERY 2: Cohort Retention — Months Active After Acquisition
-- ============================================================
WITH customer_cohort AS (
    SELECT
        customer_id,
        DATE_FORMAT(MIN(date_id), '%Y-%m')   AS cohort_month
    FROM fact_sales
    GROUP BY customer_id
),
customer_activity AS (
    SELECT
        f.customer_id,
        DATE_FORMAT(f.date_id, '%Y-%m')      AS activity_month
    FROM fact_sales f
    GROUP BY f.customer_id, DATE_FORMAT(f.date_id, '%Y-%m')
),
cohort_data AS (
    SELECT
        c.cohort_month,
        a.activity_month,
        COUNT(DISTINCT a.customer_id)        AS active_customers,
        PERIOD_DIFF(
            REPLACE(a.activity_month, '-', ''),
            REPLACE(c.cohort_month, '-', '')
        )                                    AS cohort_index
    FROM customer_cohort c
    JOIN customer_activity a ON c.customer_id = a.customer_id
    GROUP BY c.cohort_month, a.activity_month
)
SELECT
    cohort_month,
    cohort_index,
    active_customers
FROM cohort_data
WHERE cohort_index BETWEEN 0 AND 12
ORDER BY cohort_month, cohort_index;

-- ============================================================
-- QUERY 3: Month 1 Retention Rate Per Cohort
-- ============================================================
WITH customer_cohort AS (
    SELECT
        customer_id,
        DATE_FORMAT(MIN(date_id), '%Y-%m')   AS cohort_month
    FROM fact_sales
    GROUP BY customer_id
),
cohort_sizes AS (
    SELECT
        cohort_month,
        COUNT(customer_id)                   AS cohort_size
    FROM customer_cohort
    GROUP BY cohort_month
),
month1_returners AS (
    SELECT
        c.cohort_month,
        COUNT(DISTINCT f.customer_id)        AS returned_month1
    FROM customer_cohort c
    JOIN fact_sales f ON c.customer_id = f.customer_id
    WHERE DATE_FORMAT(f.date_id, '%Y-%m') =
          DATE_FORMAT(DATE_ADD(STR_TO_DATE(CONCAT(c.cohort_month, '-01'), '%Y-%m-%d'),
          INTERVAL 1 MONTH), '%Y-%m')
    GROUP BY c.cohort_month
)
SELECT
    cs.cohort_month,
    cs.cohort_size,
    COALESCE(m.returned_month1, 0)           AS returned_month1,
    ROUND(COALESCE(m.returned_month1, 0) * 100.0 /
          cs.cohort_size, 2)                 AS month1_retention_pct
FROM cohort_sizes cs
LEFT JOIN month1_returners m ON cs.cohort_month = m.cohort_month
ORDER BY cs.cohort_month;

-- ============================================================
-- QUERY 4: Best and Worst Retention Cohorts
-- ============================================================
WITH customer_cohort AS (
    SELECT
        customer_id,
        DATE_FORMAT(MIN(date_id), '%Y-%m')   AS cohort_month
    FROM fact_sales
    GROUP BY customer_id
),
cohort_sizes AS (
    SELECT cohort_month, COUNT(customer_id) AS cohort_size
    FROM customer_cohort
    GROUP BY cohort_month
),
month1_returners AS (
    SELECT
        c.cohort_month,
        COUNT(DISTINCT f.customer_id)        AS returned_month1
    FROM customer_cohort c
    JOIN fact_sales f ON c.customer_id = f.customer_id
    WHERE DATE_FORMAT(f.date_id, '%Y-%m') =
          DATE_FORMAT(DATE_ADD(STR_TO_DATE(CONCAT(c.cohort_month,'-01'),'%Y-%m-%d'),
          INTERVAL 1 MONTH), '%Y-%m')
    GROUP BY c.cohort_month
),
retention AS (
    SELECT
        cs.cohort_month,
        cs.cohort_size,
        COALESCE(m.returned_month1, 0)       AS returned_month1,
        ROUND(COALESCE(m.returned_month1,0)*100.0/cs.cohort_size,2)
                                             AS retention_pct
    FROM cohort_sizes cs
    LEFT JOIN month1_returners m ON cs.cohort_month = m.cohort_month
)
SELECT
    cohort_month,
    cohort_size,
    returned_month1,
    retention_pct,
    RANK() OVER (ORDER BY retention_pct DESC) AS retention_rank
FROM retention
ORDER BY retention_pct DESC;