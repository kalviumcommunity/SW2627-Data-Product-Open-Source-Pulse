-- ============================================================================
-- TASK 3: Compare Join Types
-- ============================================================================
-- INNER  = only rows where both sides match
-- LEFT   = all customers + matched transactions (NULLs where no match)
-- FULL   = all customers + all transactions (simulated, SQLite has no FULL OUTER JOIN)
--
-- INNER <= LEFT (INNER drops customers with no transactions)
-- FULL  >= LEFT (FULL also captures transactions with no customer)
-- ============================================================================

-- A) INNER JOIN: only matched records
SELECT
    c.customer_id,
    c.customer_type,
    t.transaction_id,
    t.order_id,
    t.amount
FROM customers c
INNER JOIN transactions t ON c.customer_id = t.customer_id;

-- B) LEFT JOIN: all customers, matched transactions or NULL
SELECT
    c.customer_id,
    c.customer_type,
    t.transaction_id,
    t.order_id,
    t.amount
FROM customers c
LEFT JOIN transactions t ON c.customer_id = t.customer_id;

-- C) FULL OUTER JOIN simulated with UNION (SQLite does not support FULL OUTER)
SELECT
    c.customer_id,
    c.customer_type,
    t.transaction_id,
    t.order_id,
    t.amount
FROM customers c
LEFT JOIN transactions t ON c.customer_id = t.customer_id

UNION

SELECT
    c.customer_id,
    c.customer_type,
    t.transaction_id,
    t.order_id,
    t.amount
FROM transactions t
LEFT JOIN customers c ON t.customer_id = c.customer_id
WHERE c.customer_id IS NULL;
