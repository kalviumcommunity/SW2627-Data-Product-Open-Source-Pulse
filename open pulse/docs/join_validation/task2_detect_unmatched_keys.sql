-- ============================================================================
-- TASK 2: Detect Unmatched Keys
-- ============================================================================
-- Query A: Customers with NO transactions (orphaned dimension rows)
-- Query B: Transactions with NO matching customer (orphaned fact rows)
--
-- Unmatched customers = signups who never purchased (churn risk).
-- Unphaned transactions = data integrity issue (FK violation).
-- ============================================================================

-- A) Customers with zero transactions
SELECT
    c.customer_id,
    c.customer_name,
    c.customer_type,
    c.signup_date
FROM customers c
LEFT JOIN transactions t ON c.customer_id = t.customer_id
WHERE t.transaction_id IS NULL
ORDER BY c.signup_date;

-- B) Transactions referencing a customer_id not in customers
SELECT
    t.transaction_id,
    t.customer_id,
    t.order_id,
    t.amount,
    t.transaction_date
FROM transactions t
LEFT JOIN customers c ON t.customer_id = c.customer_id
WHERE c.customer_id IS NULL
ORDER BY t.transaction_date;
