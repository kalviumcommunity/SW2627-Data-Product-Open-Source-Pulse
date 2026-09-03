-- ============================================================================
-- TASK 4b: Validate No Unexpected Duplication
-- ============================================================================
-- After multi-table join, verify that aggregate totals at the transaction
-- level still match the base table. If they don't, the join multiplied rows.
-- ============================================================================

-- Revenue per customer before join (from transactions alone)
SELECT
    customer_id,
    ROUND(SUM(amount), 2) AS revenue_before_join
FROM transactions
WHERE status = 'completed'
GROUP BY customer_id
ORDER BY customer_id;

-- Revenue per customer after 3-table join (should match)
SELECT
    c.customer_id,
    ROUND(SUM(t.amount), 2) AS revenue_after_join
FROM customers c
LEFT JOIN transactions t ON c.customer_id = t.customer_id
LEFT JOIN customer_segments cs ON c.customer_id = cs.customer_id
WHERE t.status = 'completed'
GROUP BY c.customer_id
ORDER BY c.customer_id;
