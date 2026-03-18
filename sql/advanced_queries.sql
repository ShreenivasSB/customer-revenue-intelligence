-- ============================================================
-- Customer Revenue Intelligence & Retention Analytics System
-- Advanced SQL Queries — Window Functions, Rankings, CTEs
-- Author: Shreenivas
-- ============================================================

USE customer_revenue_intelligence;

-- ============================================================
-- QUERY 1: Customer Revenue Ranking with RANK()
-- ============================================================
SELECT
    f.customer_id,
    c.country,
    ROUND(SUM(f.revenue), 2)                 AS total_revenue,
    COUNT(DISTINCT f.invoice)                AS total_orders,
    RANK() OVER (ORDER BY SUM(f.revenue) DESC)
                                             AS revenue_rank,
    ROUND(SUM(f.revenue) * 100.0 /
          (SELECT SUM(revenue) FROM fact_sales), 4)
                                             AS revenue_pct
FROM fact_sales f
JOIN dim_customer c ON f.customer_id = c.customer_id
GROUP BY f.customer_id, c.country
ORDER BY revenue_rank
LIMIT 20;

-- ============================================================
-- QUERY 2: Product Revenue Ranking with DENSE_RANK()
-- ============================================================
SELECT
    f.stock_code,
    p.description,
    ROUND(SUM(f.revenue), 2)                 AS total_revenue,
    SUM(f.quantity)                          AS total_units,
    DENSE_RANK() OVER (ORDER BY SUM(f.revenue) DESC)
                                             AS revenue_rank,
    ROUND(SUM(f.revenue) * 100.0 /
          (SELECT SUM(revenue) FROM fact_sales), 4)
                                             AS pct_of_total
FROM fact_sales f
JOIN dim_product p ON f.stock_code = p.stock_code
GROUP BY f.stock_code, p.description
ORDER BY revenue_rank
LIMIT 20;

-- ============================================================
-- QUERY 3: Running Total Revenue by Month
-- ============================================================
WITH monthly AS (
    SELECT
        DATE_FORMAT(date_id, '%Y-%m')        AS revenue_month,
        ROUND(SUM(revenue), 2)               AS monthly_revenue
    FROM fact_sales
    GROUP BY DATE_FORMAT(date_id, '%Y-%m')
)
SELECT
    revenue_month,
    monthly_revenue,
    ROUND(SUM(monthly_revenue) OVER (
        ORDER BY revenue_month
        ROWS UNBOUNDED PRECEDING
    ), 2)                                    AS running_total,
    ROUND(SUM(monthly_revenue) OVER (
        ORDER BY revenue_month
        ROWS UNBOUNDED PRECEDING
    ) * 100.0 /
    SUM(monthly_revenue) OVER (), 2)         AS running_pct_of_total
FROM monthly
ORDER BY revenue_month;

-- ============================================================
-- QUERY 4: Customer Percentile Ranking
-- ============================================================
SELECT
    customer_id,
    ROUND(monetary, 2)                       AS total_revenue,
    segment,
    ROUND(PERCENT_RANK() OVER (
        ORDER BY monetary
    ) * 100, 2)                              AS percentile_rank,
    NTILE(10) OVER (ORDER BY monetary DESC)  AS decile
FROM rfm_segments
ORDER BY monetary DESC
LIMIT 20;

-- ============================================================
-- QUERY 5: Month-over-Month Revenue Growth with LAG()
-- ============================================================
WITH monthly AS (
    SELECT
        DATE_FORMAT(date_id, '%Y-%m')        AS revenue_month,
        ROUND(SUM(revenue), 2)               AS monthly_revenue,
        COUNT(DISTINCT invoice)              AS total_orders,
        COUNT(DISTINCT customer_id)          AS unique_customers
    FROM fact_sales
    GROUP BY DATE_FORMAT(date_id, '%Y-%m')
)
SELECT
    revenue_month,
    monthly_revenue,
    total_orders,
    unique_customers,
    LAG(monthly_revenue) OVER (
        ORDER BY revenue_month
    )                                        AS prev_month_revenue,
    ROUND(monthly_revenue - LAG(monthly_revenue) OVER (
        ORDER BY revenue_month
    ), 2)                                    AS revenue_change,
    ROUND((monthly_revenue - LAG(monthly_revenue) OVER (
        ORDER BY revenue_month
    )) * 100.0 / LAG(monthly_revenue) OVER (
        ORDER BY revenue_month
    ), 2)                                    AS growth_pct
FROM monthly
ORDER BY revenue_month;

-- ============================================================
-- QUERY 6: Revenue Percent Contribution by Country
-- ============================================================
SELECT
    c.country,
    ROUND(SUM(f.revenue), 2)                 AS total_revenue,
    ROUND(SUM(f.revenue) * 100.0 /
          SUM(SUM(f.revenue)) OVER (), 2)    AS pct_contribution,
    ROUND(SUM(SUM(f.revenue)) OVER (
        ORDER BY SUM(f.revenue) DESC
        ROWS UNBOUNDED PRECEDING
    ), 2)                                    AS cumulative_revenue,
    RANK() OVER (
        ORDER BY SUM(f.revenue) DESC
    )                                        AS country_rank
FROM fact_sales f
JOIN dim_customer c ON f.customer_id = c.customer_id
GROUP BY c.country
ORDER BY total_revenue DESC
LIMIT 15;