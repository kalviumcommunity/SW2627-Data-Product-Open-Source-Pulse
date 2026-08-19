-- Segments first-time contributors by first-review wait time bucket and
-- computes return rate per bucket. Drives the "slow review -> low return"
-- onboarding insight.
WITH first_pr AS (
    SELECT
        id,
        contributor_id,
        created_at
    FROM pull_requests
    WHERE is_first_pr = 1
),
first_review AS (
    SELECT pr_id, MIN(created_at) AS first_review_at
    FROM reviews
    GROUP BY pr_id
),
journey AS (
    SELECT
        fp.contributor_id,
        CASE
            WHEN j1.first_review_at IS NULL THEN 'no_review'
            WHEN julianday(j1.first_review_at) - julianday(fp.created_at) <= 2 THEN 'fast_le_2d'
            WHEN julianday(j1.first_review_at) - julianday(fp.created_at) <= 10 THEN 'medium_2_10d'
            ELSE 'slow_gt_10d'
        END AS wait_bucket
    FROM first_pr fp
    LEFT JOIN first_review j1 ON j1.pr_id = fp.id
),
returned AS (
    SELECT DISTINCT contributor_id
    FROM contribution_history
    WHERE pr_id IS NOT NULL
      AND created_at > (SELECT created_at FROM first_pr f WHERE f.contributor_id = contribution_history.contributor_id)
)
SELECT
    j.wait_bucket,
    COUNT(*) AS first_time_contributors,
    SUM(CASE WHEN r.contributor_id IS NOT NULL THEN 1 ELSE 0 END) AS returned,
    ROUND(
        100.0 * SUM(CASE WHEN r.contributor_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*),
        1
    ) AS return_rate_pct
FROM journey j
LEFT JOIN returned r ON r.contributor_id = j.contributor_id
GROUP BY j.wait_bucket;
