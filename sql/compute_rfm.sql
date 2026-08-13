-- ============================================================
-- Customer Revenue Intelligence & Retention Analytics System
-- RFM Segmentation — computed in SQL using NTILE(5) quintiles
-- Postgres dialect (Supabase)
--
-- This replaces the pandas/pd.qcut RFM computation for the
-- Supabase warehouse. It is run by the ETL pipeline after
-- fact_sales is loaded and re-populates rfm_segments from
-- scratch each run (TRUNCATE + INSERT), so it is safe to re-run.
--
-- Segment rule waterfall is a direct port of the assign_segment()
-- function in notebooks/03_rfm_segmentation.ipynb — same rule
-- order, same thresholds, same segment names, so results are
-- consistent with the historical pandas-computed segments.
-- ============================================================

TRUNCATE TABLE rfm_segments;

WITH reference_date AS (
    SELECT (MAX(date_id) + INTERVAL '1 day')::date AS ref_date
    FROM fact_sales
),
customer_rfm_base AS (
    SELECT
        f.customer_id,
        ((SELECT ref_date FROM reference_date) - MAX(f.date_id)) AS recency,
        COUNT(DISTINCT f.invoice)                                AS frequency,
        ROUND(SUM(f.revenue), 2)                                 AS monetary
    FROM fact_sales f
    GROUP BY f.customer_id
),
scored AS (
    SELECT
        customer_id,
        recency,
        frequency,
        monetary,
        -- customer_id is appended as a secondary sort key purely to make
        -- tie-breaking deterministic and reproducible across re-runs —
        -- NTILE's tie order is otherwise unspecified by Postgres and not
        -- guaranteed stable (query plan, parallelism, VACUUM can all
        -- affect row scan order). It carries no ranking meaning itself.
        --
        -- Higher R score = more recent purchase (smaller recency in days)
        NTILE(5) OVER (ORDER BY recency DESC, customer_id ASC)   AS r_score,
        -- Higher F/M score = more orders / more spend
        NTILE(5) OVER (ORDER BY frequency ASC, customer_id ASC)  AS f_score,
        NTILE(5) OVER (ORDER BY monetary ASC, customer_id ASC)   AS m_score
    FROM customer_rfm_base
)
INSERT INTO rfm_segments (
    customer_id, recency, frequency, monetary,
    r_score, f_score, m_score, rfm_score, rfm_total, segment
)
SELECT
    customer_id,
    recency,
    frequency,
    monetary,
    r_score,
    f_score,
    m_score,
    (r_score::text || f_score::text || m_score::text)   AS rfm_score,
    (r_score + f_score + m_score)                        AS rfm_total,
    CASE
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champion'
        WHEN r_score >= 3 AND f_score >= 3 AND m_score >= 4 THEN 'Loyal Customer'
        WHEN r_score >= 4 AND f_score <= 2                 THEN 'New Customer'
        WHEN r_score >= 3 AND f_score >= 3 AND m_score >= 3 THEN 'Potential Loyalist'
        WHEN r_score <= 2 AND f_score >= 4 AND m_score >= 4 THEN 'At Risk'
        WHEN r_score <= 2 AND f_score >= 3 AND m_score >= 3 THEN 'Needs Attention'
        WHEN r_score = 1  AND f_score <= 2 AND m_score <= 2 THEN 'Lost'
        WHEN (r_score + f_score + m_score) >= 9             THEN 'Promising'
        WHEN (r_score + f_score + m_score) >= 6             THEN 'About to Sleep'
        ELSE 'Hibernating'
    END AS segment
FROM scored;

-- ============================================================
-- VERIFY
-- ============================================================
SELECT segment, COUNT(*) AS customer_count, ROUND(SUM(monetary), 2) AS total_revenue
FROM rfm_segments
GROUP BY segment
ORDER BY total_revenue DESC;
