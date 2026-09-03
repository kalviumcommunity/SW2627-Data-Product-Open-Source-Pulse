-- ============================================================================
-- ORDER BY + RANK: top segment performers with window function ranking
-- ============================================================================
-- Combines WHERE -> GROUP BY -> HAVING -> ORDER BY -> LIMIT to surface
-- the top-performing industry x segment combinations.
--
-- RANK() assigns a rank based on total revenue so you can compare
-- segments even when two have identical revenue.
--
-- Execution order:
--   1. WHERE  -> valid completed transactions this year
--   2. GROUP BY -> aggregate by segment x region
--   3. HAVING -> only groups with >= 10 customers
--   4. SELECT -> compute metrics + RANK() window function
--   5. ORDER BY -> sort by revenue descending
--   6. LIMIT -> top 20 results only
-- ============================================================================

SELECT
    t.customer_type                                                     AS segment,
    cs.region                                                           AS region,
    cs.product_tier                                                     AS product_tier,
    COUNT(DISTINCT t.customer_id)                                       AS customers,
    COUNT(DISTINCT t.order_id)                                          AS orders,
    SUM(t.amount)                                                       AS total_revenue,
    ROUND(AVG(t.amount), 2)                                             AS avg_order,
    RANK() OVER (ORDER BY SUM(t.amount) DESC)                           AS revenue_rank
FROM transactions t
JOIN customer_segments cs ON t.customer_id = cs.customer_id
WHERE t.transaction_date >= DATE('now', 'start of year')
  AND t.status = 'completed'
  AND t.amount > 0
GROUP BY t.customer_type, cs.region, cs.product_tier
HAVING COUNT(DISTINCT t.customer_id) >= 10
ORDER BY total_revenue DESC
LIMIT 20;
