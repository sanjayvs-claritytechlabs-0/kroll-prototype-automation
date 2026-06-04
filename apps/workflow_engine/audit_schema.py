"""SQLite schema for workflow audit and human review queue."""

WORKFLOW_RUNS_TABLE = """
CREATE TABLE IF NOT EXISTS workflow_runs (
    run_id TEXT PRIMARY KEY,
    workflow_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'running',
    started_at TEXT NOT NULL,
    finished_at TEXT,
    error TEXT
);
"""

WORKFLOW_STEPS_TABLE = """
CREATE TABLE IF NOT EXISTS workflow_steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    step_name TEXT NOT NULL,
    status TEXT NOT NULL,
    expected TEXT,
    actual TEXT,
    control_name TEXT,
    window_name TEXT,
    screenshot_path TEXT,
    error TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES workflow_runs(run_id) ON DELETE CASCADE
);
"""

REVIEW_QUEUE_TABLE = """
CREATE TABLE IF NOT EXISTS review_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    step_name TEXT NOT NULL,
    field TEXT,
    expected TEXT,
    actual TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES workflow_runs(run_id) ON DELETE CASCADE
);
"""

INDEX_STEPS_RUN = """
CREATE INDEX IF NOT EXISTS idx_workflow_steps_run_id ON workflow_steps(run_id);
"""

INDEX_REVIEW_RUN = """
CREATE INDEX IF NOT EXISTS idx_review_queue_run_id ON review_queue(run_id);
"""

AUDIT_SCHEMA_STATEMENTS = (
    WORKFLOW_RUNS_TABLE,
    WORKFLOW_STEPS_TABLE,
    REVIEW_QUEUE_TABLE,
    INDEX_STEPS_RUN,
    INDEX_REVIEW_RUN,
)
