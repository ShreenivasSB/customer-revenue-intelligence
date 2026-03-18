-- ============================================================
-- Customer Revenue Intelligence & Retention Analytics System
-- RFM Queries
-- Author: Shreenivas
-- ============================================================

USE customer_revenue_intelligence;

-- ============================================================
-- QUERY 1: Customer RFM Scores with Segment Labels
-- ============================================================
SELECT
    r.customer_id,
    r.recency,
    r.frequency,
    r.monetary,
    r.r_score,
    r.f_score,
    r.m_score,
    r.rfm_score,
    r.rfm_total,
    r.segment
FROM rfm_segments r
ORDER BY r.monetary DESC
LIMIT 20;

-- ============================================================
-- QUERY 2: Segment Distribution — Customer Count and Revenue
-- ============================================================
SELECT
    r.segment,
    COUNT(r.customer_id)            AS customer_count,
    ROUND(COUNT(r.customer_id) * 100.0 / 
          (SELECT COUNT(*) FROM rfm_segments), 2)
                                    AS customer_pct,
    ROUND(SUM(r.monetary), 2)       AS total_revenue,
    ROUND(AVG(r.monetary), 2)       AS avg_revenue,
    ROUND(AVG(r.recency), 1)        AS avg_recency_days,
    ROUND(AVG(r.frequency), 1)      AS avg_frequency
FROM rfm_segments r
GROUP BY r.segment
ORDER BY total_revenue DESC;

-- ============================================================
-- QUERY 3: Champion Customers Detail
-- ============================================================
SELECT
    r.customer_id,
    c.country,
    r.recency,
    r.frequency,
    ROUND(r.monetary, 2)            AS total_spent,
    r.rfm_score
FROM rfm_segments r
JOIN dim_customer c ON r.customer_id = c.customer_id
WHERE r.segment = 'Champion'
ORDER BY r.monetary DESC
LIMIT 20;

-- ============================================================
-- QUERY 4: At Risk Customers — Recovery Priority List
-- ============================================================
SELECT
    r.customer_id,
    c.country,
    r.recency                       AS days_since_last_purchase,
    r.frequency                     AS total_orders,
    ROUND(r.monetary, 2)            AS total_spent,
    r.rfm_score
FROM rfm_segments r
JOIN dim_customer c ON r.customer_id = c.customer_id
WHERE r.segment = 'At Risk'
ORDER BY r.monetary DESC
LIMIT 20;

-- ============================================================
-- QUERY 5: Revenue Contribution by Segment (Pareto in SQL)
-- ============================================================
SELECT
    segment,
    COUNT(customer_id)              AS customer_count,
    ROUND(SUM(monetary), 2)         AS total_revenue,
    ROUND(SUM(monetary) * 100.0 /
          (SELECT SUM(monetary) FROM rfm_segments), 2)
                                    AS revenue_pct,
    ROUND(SUM(SUM(monetary)) OVER 
          (ORDER BY SUM(monetary) DESC), 2)
                                    AS cumulative_revenue
FROM rfm_segments
GROUP BY segment
ORDER BY total_revenue DESC;
