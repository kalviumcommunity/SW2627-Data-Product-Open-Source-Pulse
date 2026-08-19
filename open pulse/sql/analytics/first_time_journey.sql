-- First-time contributors: per-contributor onboarding metrics
-- Returns one row per first-time contributor with the journey facts
-- used to compute retention correlation.
WITH first_pr AS (
    SELECT
        contributor_id,
        number,
        created_at,
        merged_at,
        closed_at,
        state,
        additions,
        deleted_files
    FROM pull_requests
    WHERE is_first_pr = 1
),
first_review AS (
    SELECT
        r.pr_id,
        MIN(r.created_at) AS first_review_at
    FROM reviews r
    GROUP BY r.pr_id
),
returned AS (
    SELECT DISTINCT contributor_id
    FROM contribution_history
    WHERE created_at > (SELECT created_at FROM first_pr f WHERE f.contributor_id = contribution_history.contributor_id)
      AND pr_id IS NOT NULL
)
SELECT
    c.github_username,
    fp.number AS first_pr_number,
    fp.state AS first_pr_state,
    fp.is_merged AS first_pr_merged,
    j1.first_review_at,
    (julianday(j1.first_review_at) - julianday(fp.created_at)) AS first_review_wait_days,
    (julianday(fp.merged_at) - julianday(fp.created_at)) AS time_to_merge_days,
    CASE WHEN r.contributor_id IS NOT NULL THEN 1 ELSE 0 END AS returned
FROM first_pr fp
JOIN contributors c ON c.id = fp.contributor_id
LEFT JOIN first_review j1 ON j1.pr_id = fp.id
LEFT JOIN returned r ON r.contributor_id = fp.contributor_id;
