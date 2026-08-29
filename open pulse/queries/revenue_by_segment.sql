-- ============================================================================
-- SHARED METRIC: Monthly Revenue by Customer Segment
-- ============================================================================
-- Write SQL once, store it, everyone uses it. This file is the ONLY
-- definition of "Monthly Revenue". Finance, Sales, Product and Accounting
-- previously computed it five different ways; they now all read THIS file,
-- so every deck, dashboard and report shows the same number.
--
-- Grain:  one row per customer segment per month
-- Window: current month-to-date plus the 12 prior calendar months
-- Metrics (6): order_count, monthly_revenue, avg_order_value,
--              unique_customers, revenue_per_customer (+ segment key)
--
-- Engine notes (this repo runs on SQLite / analytics.db):
--   DATE(t.transaction_date, 'start of month')  == DATE_TRUNC('month', t.transaction_date)::DATE
--   DATE('now', 'start of month', '-12 months') == DATE_TRUNC('month', NOW()) - INTERVAL '12 months'
-- ============================================================================

SELECT
    c.customer_type                                                   AS customer_type,
    DATE(t.transaction_date, 'start of month')                        AS month,
    COUNT(DISTINCT t.order_id)                                        AS order_count,
    SUM(t.amount)                                                     AS monthly_revenue,
    ROUND(AVG(t.amount), 2)                                           AS avg_order_value,
    COUNT(DISTINCT t.customer_id)                                     AS unique_customers,
    ROUND(SUM(t.amount) / COUNT(DISTINCT t.customer_id), 2)           AS revenue_per_customer
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
WHERE t.transaction_date >= DATE('now', 'start of month', '-12 months')
GROUP BY c.customer_type, DATE(t.transaction_date, 'start of month')
ORDER BY month DESC, monthly_revenue DESC;
