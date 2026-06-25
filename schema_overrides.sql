-- ========================================
-- SCHEMA PARA OVERRIDES DE STATUS
-- Permite editar manualmente o status de
-- casos de teste automatizados (Katalon)
-- ========================================

CREATE TABLE IF NOT EXISTS test_status_overrides (
    id BIGSERIAL PRIMARY KEY,
    test_case_id BIGINT NOT NULL REFERENCES test_cases(id) ON DELETE CASCADE,
    execution_id BIGINT NOT NULL REFERENCES test_executions(id) ON DELETE CASCADE,
    original_status TEXT NOT NULL,
    overridden_status TEXT NOT NULL,
    reason TEXT,
    created_by TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(test_case_id)
);

CREATE INDEX IF NOT EXISTS idx_overrides_test_case ON test_status_overrides(test_case_id);
CREATE INDEX IF NOT EXISTS idx_overrides_execution ON test_status_overrides(execution_id);
CREATE INDEX IF NOT EXISTS idx_overrides_status ON test_status_overrides(overridden_status);
