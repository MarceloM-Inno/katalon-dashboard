-- ========================================
-- SCHEMA PARA TESTES MANUAIS
-- ========================================

-- ========================================
-- Tabela: manual_registered_projects
-- Projetos cadastrados pela equipe de testes
-- ========================================
CREATE TABLE IF NOT EXISTS manual_registered_projects (
    id BIGSERIAL PRIMARY KEY,
    project_key TEXT NOT NULL,
    base_project TEXT NOT NULL,
    date_start DATE NOT NULL,
    date_end DATE NOT NULL,
    friendly_name TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(project_key, base_project)
);

CREATE INDEX IF NOT EXISTS idx_manual_registered_base ON manual_registered_projects(base_project);
CREATE INDEX IF NOT EXISTS idx_manual_registered_key ON manual_registered_projects(project_key);
CREATE INDEX IF NOT EXISTS idx_manual_registered_dates ON manual_registered_projects(date_start, date_end);

-- ========================================
-- Tabela: manual_daily_snapshots
-- Metadados das extrações diárias do CSV
-- ========================================
CREATE TABLE IF NOT EXISTS manual_daily_snapshots (
    id BIGSERIAL PRIMARY KEY,
    base_project TEXT NOT NULL,
    snapshot_date TIMESTAMPTZ NOT NULL,
    snapshot_datetime TIMESTAMPTZ NOT NULL,
    file_name TEXT NOT NULL,
    total_rows_in_csv INTEGER DEFAULT 0,
    processed_rows INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(base_project, snapshot_datetime)
);

CREATE INDEX IF NOT EXISTS idx_manual_snapshots_base ON manual_daily_snapshots(base_project);
CREATE INDEX IF NOT EXISTS idx_manual_snapshots_date ON manual_daily_snapshots(snapshot_date);
CREATE INDEX IF NOT EXISTS idx_manual_snapshots_datetime ON manual_daily_snapshots(snapshot_datetime);

-- ========================================
-- Tabela: manual_project_history
-- Histórico diário por projeto cadastrado
-- ========================================
CREATE TABLE IF NOT EXISTS manual_project_history (
    id BIGSERIAL PRIMARY KEY,
    snapshot_id BIGINT NOT NULL REFERENCES manual_daily_snapshots(id) ON DELETE CASCADE,
    registered_project_id BIGINT NOT NULL REFERENCES manual_registered_projects(id) ON DELETE CASCADE,
    base_project TEXT NOT NULL,
    project_key TEXT NOT NULL,
    snapshot_date DATE NOT NULL,
    snapshot_datetime TIMESTAMPTZ NOT NULL,
    total_tests INTEGER DEFAULT 0,
    total_pass INTEGER DEFAULT 0,
    total_fail INTEGER DEFAULT 0,
    total_aborted INTEGER DEFAULT 0,
    total_blocked INTEGER DEFAULT 0,
    total_pending INTEGER DEFAULT 0,
    total_other INTEGER DEFAULT 0,
    priority_high_total INTEGER DEFAULT 0,
    priority_high_pass INTEGER DEFAULT 0,
    priority_med_total INTEGER DEFAULT 0,
    priority_med_pass INTEGER DEFAULT 0,
    priority_low_total INTEGER DEFAULT 0,
    priority_low_pass INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(registered_project_id, snapshot_datetime)
);

CREATE INDEX IF NOT EXISTS idx_manual_history_snapshot ON manual_project_history(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_manual_history_registered ON manual_project_history(registered_project_id);
CREATE INDEX IF NOT EXISTS idx_manual_history_project ON manual_project_history(project_key, snapshot_datetime);
CREATE INDEX IF NOT EXISTS idx_manual_history_date ON manual_project_history(snapshot_date);
CREATE INDEX IF NOT EXISTS idx_manual_history_datetime ON manual_project_history(snapshot_datetime);

-- ========================================
-- Tabela: manual_test_cases
-- Casos de teste individuais com histórico
-- ========================================
CREATE TABLE IF NOT EXISTS manual_test_cases (
    id BIGSERIAL PRIMARY KEY,
    snapshot_id BIGINT NOT NULL REFERENCES manual_daily_snapshots(id) ON DELETE CASCADE,
    registered_project_id BIGINT REFERENCES manual_registered_projects(id) ON DELETE SET NULL,
    base_project TEXT NOT NULL,
    project_key TEXT NOT NULL,
    project_name TEXT,
    issue_key TEXT NOT NULL,
    issue_id BIGINT,
    status TEXT NOT NULL,
    priority TEXT,
    snapshot_date DATE NOT NULL,
    snapshot_datetime TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_manual_cases_snapshot ON manual_test_cases(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_manual_cases_registered ON manual_test_cases(registered_project_id);
CREATE INDEX IF NOT EXISTS idx_manual_cases_project ON manual_test_cases(project_key);
CREATE INDEX IF NOT EXISTS idx_manual_cases_issue ON manual_test_cases(issue_key);
CREATE INDEX IF NOT EXISTS idx_manual_cases_status ON manual_test_cases(status);
CREATE INDEX IF NOT EXISTS idx_manual_cases_date ON manual_test_cases(snapshot_date);
CREATE INDEX IF NOT EXISTS idx_manual_cases_datetime ON manual_test_cases(snapshot_datetime);
CREATE INDEX IF NOT EXISTS idx_manual_cases_base_date ON manual_test_cases(base_project, snapshot_date);
CREATE INDEX IF NOT EXISTS idx_manual_cases_unique ON manual_test_cases(project_key, base_project, snapshot_datetime);

-- ========================================
-- Tabela: manual_defects
-- Defeitos/Bugs de Defects All Projects e FillAutoDefects
-- ========================================
CREATE TABLE IF NOT EXISTS manual_defects (
    id BIGSERIAL PRIMARY KEY,
    snapshot_id BIGINT NOT NULL REFERENCES manual_daily_snapshots(id) ON DELETE CASCADE,
    base_project TEXT NOT NULL,
    project_key TEXT NOT NULL,
    project_name TEXT,
    issue_key TEXT NOT NULL,
    issue_id BIGINT,
    summary TEXT,
    status TEXT NOT NULL,
    priority TEXT,
    assignee TEXT,
    reporter TEXT,
    created_dt TIMESTAMPTZ,
    updated_dt TIMESTAMPTZ,
    custom_fornecedor TEXT,
    custom_impact_qa TEXT,
    custom_reopen_bug TEXT,
    links_blocks TEXT[],
    links_relates TEXT[],
    links_problem_incident TEXT[],
    links_tests TEXT[],
    snapshot_date DATE NOT NULL,
    snapshot_datetime TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_manual_defects_snapshot ON manual_defects(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_manual_defects_project ON manual_defects(project_key);
CREATE INDEX IF NOT EXISTS idx_manual_defects_issue ON manual_defects(issue_key);
CREATE INDEX IF NOT EXISTS idx_manual_defects_status ON manual_defects(status);
CREATE INDEX IF NOT EXISTS idx_manual_defects_priority ON manual_defects(priority);
CREATE INDEX IF NOT EXISTS idx_manual_defects_date ON manual_defects(snapshot_date);
CREATE INDEX IF NOT EXISTS idx_manual_defects_datetime ON manual_defects(snapshot_datetime);
CREATE INDEX IF NOT EXISTS idx_manual_defects_base_date ON manual_defects(base_project, snapshot_date);
CREATE INDEX IF NOT EXISTS idx_manual_defects_unique ON manual_defects(project_key, base_project, snapshot_datetime);
