-- ============================================================================
-- ENTERPRISE ANNUAL SPENDING: WHERE filters rows BEFORE grouping
-- ============================================================================
-- This query answers: "Which Enterprise customers spend >$10k/year?"
--
-- WHERE removes invalid rows BEFORE GROUP BY runs.
-- Every condition below targets a data-quality or business rule:
--   - customer_type = 'Enterprise'  -> only Enterprise segment
--   - status = 'completed'          -> exclude pending/refunded
--   - amount > 0                    -> exclude refund line items
--   - date range                    -> current calendar year only
--
-- Engine notes (SQLite):
--   DATE(transaction_date)          == DATE_TRUNC('day', transaction_date)::DATE
--   DATE('now', 'start of year')    == DATE_TRUNC('year', NOW())::DATE
-- ============================================================================

SELECT
    t.customer_id,
    c.customer_name,
    COUNT(DISTINCT t.order_id)                          AS order_count,
    COUNT(*)                                            AS line_items,
    SUM(t.amount)                                       AS annual_revenue,
    ROUND(AVG(t.amount), 2)                             AS avg_line_item
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
WHERE t.customer_type = 'Enterprise'
  AND t.status = 'completed'
  AND t.amount > 0
  AND t.transaction_date >= DATE('now', 'start of year')
GROUP BY t.customer_id, c.customer_name
ORDER BY annual_revenue DESC;
