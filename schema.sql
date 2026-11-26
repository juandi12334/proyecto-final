-- AI citation (CS50x Final Project): Claude (Anthropic) and ChatGPT (OpenAI)
-- were used as development assistants during the creation of this project.
--
-- FocusBoard database schema.
-- Running this script RESETS the database (all tables are dropped first).

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS focus_logs;
DROP TABLE IF EXISTS tasks;
DROP TABLE IF EXISTS projects;

-- Projects work as labels that group tasks (e.g. "CS50", "Work").
CREATE TABLE projects (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE COLLATE NOCASE
                        CHECK (length(trim(name)) BETWEEN 1 AND 40),
    color       TEXT    NOT NULL DEFAULT '#7f9cc2',
    created_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- Each task optionally belongs to one project.
-- priority: 1 = low, 2 = medium, 3 = high.
CREATE TABLE tasks (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id        INTEGER REFERENCES projects(id) ON DELETE SET NULL,
    title             TEXT    NOT NULL CHECK (length(trim(title)) BETWEEN 1 AND 120),
    description       TEXT    NOT NULL DEFAULT '',
    priority          INTEGER NOT NULL DEFAULT 2 CHECK (priority IN (1, 2, 3)),
    status            TEXT    NOT NULL DEFAULT 'pending'
                              CHECK (status IN ('pending', 'in_progress', 'done')),
    due_date          TEXT,                       -- ISO date YYYY-MM-DD or NULL
    estimate_minutes  INTEGER CHECK (estimate_minutes IS NULL OR estimate_minutes > 0),
    created_at        TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at        TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    completed_at      TEXT
);

-- Every focus session (timer or manual entry) logged against a task.
CREATE TABLE focus_logs (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id    INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    minutes    INTEGER NOT NULL CHECK (minutes BETWEEN 1 AND 600),
    note       TEXT    NOT NULL DEFAULT '',
    logged_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- Indexes for the columns used by filters, joins and summaries.
CREATE INDEX idx_tasks_status     ON tasks (status);
CREATE INDEX idx_tasks_priority   ON tasks (priority);
CREATE INDEX idx_tasks_project    ON tasks (project_id);
CREATE INDEX idx_tasks_due_date   ON tasks (due_date);
CREATE INDEX idx_focus_task       ON focus_logs (task_id);
CREATE INDEX idx_focus_logged_at  ON focus_logs (logged_at);
