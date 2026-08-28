-- ============================================================================
-- SHARED METRIC: Daily Signup -> First Purchase Conversion Funnel
-- ============================================================================
-- Write SQL once, store it, everyone uses it. This file is the ONLY
-- definition of the signup funnel. Growth, Product and Marketing all load
-- THIS file, so funnel numbers never disagree between decks.
--
-- Grain:  one row per signup day
-- Window: last 90 days (rolling)
-- Stages: signups -> email_verified -> first_purchase, plus conversion_pct
--
-- Engine notes (this repo runs on SQLite / analytics.db):
--   DATE(u.created_at)          == DATE_TRUNC('day', u.created_at)::DATE
--   DATETIME('now', '-90 days') == NOW() - INTERVAL '90 days'
-- ============================================================================

SELECT
    DATE(u.created_at)                                                        AS signup_date,
    COUNT(*)                                                                  AS signups,
    COUNT(*) FILTER (WHERE u.email_verified_at IS NOT NULL)                   AS email_verified,
    COUNT(*) FILTER (WHERE u.first_purchase_at IS NOT NULL)                   AS first_purchase,
    ROUND(100.0 * COUNT(*) FILTER (WHERE u.first_purchase_at IS NOT NULL)
          / COUNT(*), 1)                                                      AS conversion_pct
FROM users u
WHERE u.created_at >= DATETIME('now', '-90 days')
GROUP BY DATE(u.created_at)
ORDER BY signup_date DESC;
