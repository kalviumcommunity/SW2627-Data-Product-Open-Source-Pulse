-- ============================================================================
-- WHERE + HAVING COMBINED: data quality + business thresholds
-- ============================================================================
-- WHERE  -> removes bad rows (refunds, pending, wrong dates)
-- HAVING -> removes groups that don't meet business criteria
--
-- Execution order:
--   1. FROM / JOIN    -> identify tables
--   2. WHERE          -> filter rows (data quality)
--   3. GROUP BY       -> aggregate into groups
--   4. HAVING         -> filter groups (business thresholds)
--   5. SELECT         -> pick columns
--   6. ORDER BY       -> sort results
--
-- Use case: executive segment report showing only segments large
-- enough to be actionable (>= 10 customers, >$100k revenue).
-- ============================================================================

SELECT
    t.customer_type                                                     AS segment,
    COUNT(DISTINCT t.customer_id)                                       AS segment_customers,
    COUNT(DISTINCT t.order_id)                                          AS total_orders,
    SUM(t.amount)                                                       AS segment_revenue,
    ROUND(AVG(t.amount), 2)                                             AS avg_order_value,
    ROUND(SUM(t.amount) / COUNT(DISTINCT t.customer_id), 2)             AS revenue_per_customer
FROM transactions t
WHERE t.transaction_date >= DATE('now', 'start of year')
  AND t.status = 'completed'
  AND t.amount > 0
GROUP BY t.customer_type
HAVING COUNT(DISTINCT t.customer_id) >= 10
   AND SUM(t.amount) > 100000
ORDER BY segment_revenue DESC;
