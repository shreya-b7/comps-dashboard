DROP VIEW IF EXISTS ev_revenue;
DROP VIEW IF EXISTS rule_of_40;

CREATE VIEW ev_revenue AS
WITH ttm AS (
    SELECT ticker, quarter,
           SUM(revenue) OVER (
               PARTITION BY ticker ORDER BY quarter
               ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
           ) AS ttm_revenue
    FROM financials
)
SELECT t.ticker, t.quarter, m.ev / t.ttm_revenue AS ev_revenue_multiple
FROM ttm t
JOIN market_data m ON m.ticker = t.ticker AND m.date = t.quarter
WHERE t.ttm_revenue IS NOT NULL;

CREATE VIEW rule_of_40 AS
SELECT ticker, quarter, (revenue_growth_qoq * 100 + fcf_margin * 100) AS rule_of_40_score
FROM financials;