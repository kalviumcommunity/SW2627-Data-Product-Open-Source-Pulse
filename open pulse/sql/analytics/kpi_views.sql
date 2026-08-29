-- KPI views over the daily business metrics table.
--
-- The dashboard reads these views, never the base table, so a change to a
-- metric definition happens here once and every consumer picks it up.
--
-- Nothing here hard-codes a date. The current period is derived from the data
-- itself, so loading a newer extract moves the reporting window forward with
-- no code change.

DROP VIEW IF EXISTS vw_daily_metrics;
CREATE VIEW vw_daily_metrics AS
SELECT
    date,
    daily_revenue,
    transaction_count,
    signup_rate,
    strftime('%Y-%m', date) AS month
FROM daily_metrics;


-- Position of each day within its own month. This is what makes a
-- like-for-like comparison possible: day 1 of this month lines up against
-- day 1 of last month regardless of how many days each month holds.
DROP VIEW IF EXISTS vw_daily_metrics_indexed;
CREATE VIEW vw_daily_metrics_indexed AS
SELECT
    *,
    ROW_NUMBER() OVER (PARTITION BY month ORDER BY date) AS day_index
FROM vw_daily_metrics;


-- The two periods under comparison, derived from the data rather than the
-- calendar: the newest month present, and the month immediately before it.
DROP VIEW IF EXISTS vw_kpi_periods;
CREATE VIEW vw_kpi_periods AS
WITH current_month AS (
    SELECT MAX(month) AS month FROM vw_daily_metrics
),
window_length AS (
    -- How many days of the current month have data. The prior month is cut to
    -- the same length so the two windows are directly comparable.
    SELECT COUNT(*) AS days
    FROM vw_daily_metrics
    WHERE month = (SELECT month FROM current_month)
)
SELECT
    (SELECT month FROM current_month) AS current_month,
    strftime('%Y-%m', date((SELECT month FROM current_month) || '-01', '-1 month'))
        AS prior_month,
    (SELECT days FROM window_length) AS window_days;


-- One row per period with every additive measure aggregated over the matched
-- window, plus the derived average order value.
DROP VIEW IF EXISTS vw_kpi_period_totals;
CREATE VIEW vw_kpi_period_totals AS
SELECT
    CASE
        WHEN d.month = p.current_month THEN 'current'
        ELSE 'prior'
    END AS period,
    d.month,
    COUNT(*) AS days,
    SUM(d.daily_revenue) AS revenue,
    SUM(d.transaction_count) AS transactions,
    SUM(d.signup_rate) AS signups,
    SUM(d.daily_revenue) / NULLIF(SUM(d.transaction_count), 0) AS avg_order_value
FROM vw_daily_metrics_indexed d
CROSS JOIN vw_kpi_periods p
WHERE (d.month = p.current_month)
   OR (d.month = p.prior_month AND d.day_index <= p.window_days)
GROUP BY period, d.month;


-- The KPI table the dashboard consumes: one row per metric with its current
-- value, its prior value, and the percentage change between them.
DROP VIEW IF EXISTS vw_kpi_summary;
CREATE VIEW vw_kpi_summary AS
WITH pivoted AS (
    SELECT
        MAX(CASE WHEN period = 'current' THEN revenue END)          AS cur_revenue,
        MAX(CASE WHEN period = 'prior'   THEN revenue END)          AS pri_revenue,
        MAX(CASE WHEN period = 'current' THEN transactions END)     AS cur_transactions,
        MAX(CASE WHEN period = 'prior'   THEN transactions END)     AS pri_transactions,
        MAX(CASE WHEN period = 'current' THEN signups END)          AS cur_signups,
        MAX(CASE WHEN period = 'prior'   THEN signups END)          AS pri_signups,
        MAX(CASE WHEN period = 'current' THEN avg_order_value END)  AS cur_aov,
        MAX(CASE WHEN period = 'prior'   THEN avg_order_value END)  AS pri_aov
    FROM vw_kpi_period_totals
)
SELECT 'revenue' AS metric, cur_revenue AS current_value, pri_revenue AS prior_value,
       (cur_revenue - pri_revenue) * 100.0 / NULLIF(pri_revenue, 0) AS change_pct
FROM pivoted
UNION ALL
SELECT 'transactions', cur_transactions, pri_transactions,
       (cur_transactions - pri_transactions) * 100.0 / NULLIF(pri_transactions, 0)
FROM pivoted
UNION ALL
SELECT 'avg_order_value', cur_aov, pri_aov,
       (cur_aov - pri_aov) * 100.0 / NULLIF(pri_aov, 0)
FROM pivoted
UNION ALL
SELECT 'signups', cur_signups, pri_signups,
       (cur_signups - pri_signups) * 100.0 / NULLIF(pri_signups, 0)
FROM pivoted;


-- Churn has no date column in this project, so it is compared against the
-- retention target rather than against a prior period. The 0.10 threshold is
-- the one analyze_segments.py already uses to flag a segment HIGH PRIORITY.
DROP VIEW IF EXISTS vw_churn_kpi;
CREATE VIEW vw_churn_kpi AS
SELECT
    'churn_rate' AS metric,
    AVG(churn) AS current_value,
    0.10 AS target_value,
    (AVG(churn) - 0.10) * 100.0 / 0.10 AS change_pct
FROM customer_segments;
