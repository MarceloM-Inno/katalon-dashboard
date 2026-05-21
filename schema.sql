CREATE TABLE IF NOT EXISTS test_executions (
    id BIGSERIAL PRIMARY KEY,
    suite_name TEXT NOT NULL,
    execution_date TIMESTAMPTZ NOT NULL,
    total_tests INTEGER NOT NULL DEFAULT 0,
    total_failures INTEGER NOT NULL DEFAULT 0,
    total_errors INTEGER NOT NULL DEFAULT 0,
    total_skipped INTEGER NOT NULL DEFAULT 0,
    total_time_sec DOUBLE PRECISION DEFAULT 0,
    hostname TEXT,
    os TEXT,
    browser TEXT,
    katalon_version TEXT,
    user_full_name TEXT,
    project_name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(suite_name, execution_date)
);

CREATE TABLE IF NOT EXISTS test_cases (
    id BIGSERIAL PRIMARY KEY,
    execution_id BIGINT NOT NULL REFERENCES test_executions(id) ON DELETE CASCADE,
    test_name TEXT NOT NULL,
    duration_sec DOUBLE PRECISION DEFAULT 0,
    status TEXT NOT NULL,
    failure_type TEXT,
    failure_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cases_execution_id ON test_cases(execution_id);
CREATE INDEX IF NOT EXISTS idx_executions_date ON test_executions(execution_date);
CREATE INDEX IF NOT EXISTS idx_cases_status ON test_cases(status);
CREATE INDEX IF NOT EXISTS idx_executions_suite ON test_executions(suite_name);
