-- ============================================================================
-- TASK 4: Multi-Table Join (3 tables)
-- ============================================================================
-- Joins customers -> transactions -> customer_segments to build a complete
-- customer view with transaction history and segment metadata.
--
-- LEFT JOINs preserve all customers even if they lack transactions
-- or segment data. Watch for row multiplication when both sides are
-- one-to-many.
-- ============================================================================

SELECT
    c.customer_id,
    c.customer_name,
    c.customer_type                                   AS cust_type,
    cs.region,
    cs.product_tier,
    cs.lifetime_value,
    cs.retention_days,
    t.transaction_id,
    t.order_id,
    t.transaction_date,
    t.amount,
    t.status
FROM customers c
LEFT JOIN transactions t ON c.customer_id = t.customer_id
LEFT JOIN customer_segments cs ON c.customer_id = cs.customer_id
WHERE c.customer_type = 'Enterprise'
ORDER BY c.customer_id, t.transaction_date DESC;
