-- ============================================================================
-- SHARED METRIC: Monthly Active Users (MAU) with segment breakdown
-- ============================================================================
-- Write SQL once, store it, everyone uses it. This file is the ONLY
-- definition of "Monthly Active Users" -- Finance, Sales, Product and
-- Accounting all load THIS file; nobody hand-writes their own version.
--
-- Grain:  one row per month
-- Window: current month-to-date plus the 12 prior calendar months
--
-- Engine notes (this repo runs on SQLite / analytics.db):
--   DATE(transaction_date, 'start of month')   == DATE_TRUNC('month', transaction_date)::DATE
--   DATE('now', 'start of month', '-12 months') == DATE_TRUNC('month', NOW()) - INTERVAL '12 months'
-- ============================================================================

SELECT
    DATE(transaction_date, 'start of month')                                 AS month,
    COUNT(DISTINCT customer_id)                                              AS active_users,
    COUNT(DISTINCT customer_id) FILTER (WHERE customer_type = 'Enterprise')  AS enterprise_users,
    COUNT(DISTINCT customer_id) FILTER (WHERE customer_type = 'SMB')         AS smb_users
FROM transactions
WHERE transaction_date >= DATE('now', 'start of month', '-12 months')
GROUP BY DATE(transaction_date, 'start of month')
ORDER BY month DESC;
