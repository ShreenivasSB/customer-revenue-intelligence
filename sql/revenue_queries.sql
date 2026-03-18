-- ============================================================
-- Customer Revenue Intelligence & Retention Analytics System
-- Revenue Analysis Queries
-- Author: Shreenivas
-- ============================================================

USE customer_revenue_intelligence;

-- ============================================================
-- QUERY 1: Monthly Revenue Trend
-- ============================================================
SELECT
    DATE_FORMAT(date_id, '%Y-%m')           AS revenue_month,
    COUNT(DISTINCT invoice)                  AS total_orders,
    COUNT(DISTINCT customer_id)              AS unique_customers,
    ROUND(SUM(revenue), 2)                   AS total_revenue,
    ROUND(SUM(revenue) /
          COUNT(DISTINCT invoice), 2)        AS avg_order_value
FROM fact_sales
GROUP BY DATE_FORMAT(date_id, '%Y-%m')
ORDER BY revenue_month;

-- ============================================================
-- QUERY 2: Revenue by Country (Top 10)
-- ============================================================
SELECT
    c.country,
    COUNT(DISTINCT f.invoice)                AS total_orders,
    COUNT(DISTINCT f.customer_id)            AS unique_customers,
    ROUND(SUM(f.revenue), 2)                 AS total_revenue,
    ROUND(SUM(f.revenue) * 100.0 /
          (SELECT SUM(revenue) FROM fact_sales), 2)
                                             AS revenue_pct,
    ROUND(SUM(f.revenue) /
          COUNT(DISTINCT f.customer_id), 2)  AS revenue_per_customer
FROM fact_sales f
JOIN dim_customer c ON f.customer_id = c.customer_id
GROUP BY c.country
ORDER BY total_revenue DESC
LIMIT 10;

-- ============================================================
-- QUERY 3: Monthly Rolling 3-Month Average Revenue
-- ============================================================
WITH monthly_revenue AS (
    SELECT
        DATE_FORMAT(date_id, '%Y-%m')        AS revenue_month,
        ROUND(SUM(revenue), 2)               AS monthly_revenue
    FROM fact_sales
    GROUP BY DATE_FORMAT(date_id, '%Y-%m')
)
SELECT
    revenue_month,
    monthly_revenue,
    ROUND(AVG(monthly_revenue) OVER (
        ORDER BY revenue_month
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 2)                                    AS rolling_3month_avg,
    ROUND(monthly_revenue - LAG(monthly_revenue)
          OVER (ORDER BY revenue_month), 2)  AS month_over_month_change,
    ROUND((monthly_revenue - LAG(monthly_revenue)
          OVER (ORDER BY revenue_month)) * 100.0 /
          LAG(monthly_revenue)
          OVER (ORDER BY revenue_month), 2)  AS mom_growth_pct
FROM monthly_revenue
ORDER BY revenue_month;

-- ============================================================
-- QUERY 4: Q4 vs Non-Q4 Revenue Comparison
-- ============================================================
SELECT
    d.is_q4,
    CASE WHEN d.is_q4 = 1 THEN 'Q4 (Oct-Dec)'
         ELSE 'Non-Q4 (Jan-Sep)' END         AS period,
    COUNT(DISTINCT f.invoice)                AS total_orders,
    ROUND(SUM(f.revenue), 2)                 AS total_revenue,
    ROUND(SUM(f.revenue) /
          COUNT(DISTINCT f.invoice), 2)      AS avg_order_value
FROM fact_sales f
JOIN dim_date d ON f.date_id = d.date_id
GROUP BY d.is_q4
ORDER BY d.is_q4 DESC;

-- ============================================================
-- QUERY 5: Top 10 Products by Revenue
-- ============================================================
SELECT
    f.stock_code,
    p.description,
    COUNT(DISTINCT f.invoice)                AS total_orders,
    SUM(f.quantity)                          AS total_units_sold,
    ROUND(SUM(f.revenue), 2)                 AS total_revenue,
    ROUND(SUM(f.revenue) * 100.0 /
          (SELECT SUM(revenue) FROM fact_sales), 2)
                                             AS revenue_pct,
    ROUND(AVG(f.price), 2)                   AS avg_price
FROM fact_sales f
JOIN dim_product p ON f.stock_code = p.stock_code
GROUP BY f.stock_code, p.description
ORDER BY total_revenue DESC
LIMIT 10;