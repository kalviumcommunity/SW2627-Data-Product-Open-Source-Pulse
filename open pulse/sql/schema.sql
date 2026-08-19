CREATE TABLE IF NOT EXISTS contributors (
    id INTEGER PRIMARY KEY,
    github_username TEXT NOT NULL UNIQUE,
    is_first_time INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS pull_requests (
    id INTEGER PRIMARY KEY,
    contributor_id INTEGER NOT NULL,
    number INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    merged_at TEXT,
    closed_at TEXT,
    closed_by TEXT,
    state TEXT NOT NULL,
    additions INTEGER DEFAULT 0,
    deletions INTEGER DEFAULT 0,
    changed_files INTEGER DEFAULT 0,
    is_first_pr INTEGER DEFAULT 0,
    is_merged INTEGER DEFAULT 0,
    FOREIGN KEY (contributor_id) REFERENCES contributors(id)
);

CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY,
    pr_id INTEGER NOT NULL,
    reviewer_id INTEGER,
    created_at TEXT NOT NULL,
    state TEXT NOT NULL,
    body TEXT,
    FOREIGN KEY (pr_id) REFERENCES pull_requests(id)
);

CREATE TABLE IF NOT EXISTS review_comments (
    id INTEGER PRIMARY KEY,
    review_id INTEGER,
    pr_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    author_id INTEGER,
    body TEXT,
    FOREIGN KEY (review_id) REFERENCES reviews(id)
);

CREATE TABLE IF NOT EXISTS issues (
    id INTEGER PRIMARY KEY,
    contributor_id INTEGER,
    title TEXT,
    created_at TEXT NOT NULL,
    closed_at TEXT,
    state TEXT NOT NULL,
    first_response_at TEXT,
    comment_count INTEGER DEFAULT 0,
    FOREIGN KEY (contributor_id) REFERENCES contributors(id)
);

CREATE TABLE IF NOT EXISTS issue_comments (
    id INTEGER PRIMARY KEY,
    issue_id INTEGER NOT NULL,
    author_id INTEGER,
    created_at TEXT NOT NULL,
    body TEXT,
    FOREIGN KEY (issue_id) REFERENCES issues(id)
);

CREATE TABLE IF NOT EXISTS commits (
    id INTEGER PRIMARY KEY,
    pr_id INTEGER,
    contributor_id INTEGER NOT NULL,
    committed_at TEXT NOT NULL,
    message TEXT,
    FOREIGN KEY (pr_id) REFERENCES pull_requests(id)
);

CREATE TABLE IF NOT EXISTS contribution_history (
    id INTEGER PRIMARY KEY,
    contributor_id INTEGER NOT NULL,
    pr_id INTEGER,
    created_at TEXT NOT NULL,
    contribution_type TEXT NOT NULL,
    FOREIGN KEY (contributor_id) REFERENCES contributors(id)
);
