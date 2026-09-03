-- ============================================================================
-- TASK 1: LEFT JOIN with Row Count Validation
-- ============================================================================
-- LEFT JOIN keeps ALL customers, even those with zero transactions.
-- Result rows >= customer rows because one customer maps to many transactions.
--
-- Table: customers (60 rows, PK: customer_id)
-- Table: transactions (~1600 rows, FK: customer_id)
-- Expected: result > 60 rows (multiplied by orders per customer)
-- ============================================================================

SELECT
    c.customer_id,
    c.customer_name,
    c.customer_type,
    COUNT(DISTINCT t.order_id)                          AS order_count,
    COUNT(t.transaction_id)                             AS line_items,
    ROUND(SUM(t.amount), 2)                             AS total_spent,
    ROUND(AVG(t.amount), 2)                             AS avg_line_item
FROM customers c
LEFT JOIN transactions t ON c.customer_id = t.customer_id
GROUP BY c.customer_id, c.customer_name, c.customer_type
ORDER BY total_spent DESC NULLS LAST;
