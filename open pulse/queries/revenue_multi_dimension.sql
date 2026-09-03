-- ============================================================================
-- MULTI-DIMENSION AGGREGATION: WHERE before GROUP BY, 3+ aggregates
-- ============================================================================
-- Groups by customer_type AND month to show segment-level revenue trends.
--
-- WHERE filters rows first (data quality + date range).
-- GROUP BY defines the aggregation grain (segment x month).
-- Aggregate functions (COUNT, SUM, AVG) run per group.
--
-- Engine notes (SQLite):
--   DATE(transaction_date, 'start of month') == DATE_TRUNC('month', t.transaction_date)::DATE
-- ============================================================================

SELECT
    t.customer_type                                                     AS customer_type,
    DATE(t.transaction_date, 'start of month')                          AS month,
    COUNT(DISTINCT t.customer_id)                                       AS unique_customers,
    COUNT(DISTINCT t.order_id)                                          AS order_count,
    SUM(t.amount)                                                       AS monthly_revenue,
    ROUND(AVG(t.amount), 2)                                             AS avg_transaction,
    ROUND(SUM(t.amount) / COUNT(DISTINCT t.customer_id), 2)             AS revenue_per_customer
FROM transactions t
WHERE t.transaction_date >= DATE('now', 'start of month', '-12 months')
  AND t.status = 'completed'
  AND t.amount > 0
GROUP BY t.customer_type, DATE(t.transaction_date, 'start of month')
ORDER BY month DESC, monthly_revenue DESC;
