-- ============================================================================
-- HAVING FILTERS GROUPS AFTER AGGREGATION
-- ============================================================================
-- WHERE cannot filter on SUM() or COUNT() because those don't exist
-- until after GROUP BY runs. HAVING runs after grouping, so it can
-- reference aggregate expressions.
--
-- This query finds Enterprise customers who:
--   - spent >$10k in the current year (HAVING SUM)
--   - placed >= 5 orders (HAVING COUNT)
--
-- WHERE cleans data before grouping; HAVING sets business thresholds
-- on the grouped results.
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
HAVING SUM(t.amount) > 10000
   AND COUNT(DISTINCT t.order_id) >= 5
ORDER BY annual_revenue DESC;
