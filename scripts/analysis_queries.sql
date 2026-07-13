-- Percentile rank on EV/Revenue within each sub-vertical
SELECT c.ticker, c.sub_vertical, e.quarter, e.ev_revenue_multiple,
       PERCENT_RANK() OVER (PARTITION BY c.sub_vertical ORDER BY e.ev_revenue_multiple) AS pct_rank
FROM ev_revenue e
JOIN companies c ON c.ticker = e.ticker
WHERE e.ev_revenue_multiple IS NOT NULL;

-- Rank on Rule of 40 score within each sub-vertical
SELECT c.ticker, c.sub_vertical, r.quarter, r.rule_of_40_score,
       RANK() OVER (PARTITION BY c.sub_vertical ORDER BY r.rule_of_40_score DESC) AS rank_in_vertical
FROM rule_of_40 r
JOIN companies c ON c.ticker = r.ticker
WHERE r.rule_of_40_score IS NOT NULL;