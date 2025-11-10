-- Migration: Create test_plan_agents table
-- Date: 2025-11-08
-- Description: Add database table for test plan generation agents
--              Consolidates hardcoded agents into database-backed system

-- Create test_plan_agents table
CREATE TABLE IF NOT EXISTS test_plan_agents (
    id SERIAL PRIMARY KEY,
    name VARCHAR UNIQUE NOT NULL,
    agent_type VARCHAR NOT NULL,
    model_name VARCHAR NOT NULL,
    system_prompt TEXT NOT NULL,
    user_prompt_template TEXT NOT NULL,
    temperature FLOAT DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 4000,
    is_system_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR,
    description TEXT,
    metadata JSONB
);

-- Create indexes
CREATE INDEX IF NOT EXISTS ix_test_plan_agents_id ON test_plan_agents(id);
CREATE INDEX IF NOT EXISTS ix_test_plan_agents_agent_type ON test_plan_agents(agent_type);
CREATE INDEX IF NOT EXISTS ix_test_plan_agents_is_system_default ON test_plan_agents(is_system_default);
CREATE INDEX IF NOT EXISTS ix_test_plan_agents_is_active ON test_plan_agents(is_active);
CREATE INDEX IF NOT EXISTS ix_test_plan_agents_created_at ON test_plan_agents(created_at);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_test_plan_agents_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_test_plan_agents_updated_at
    BEFORE UPDATE ON test_plan_agents
    FOR EACH ROW
    EXECUTE FUNCTION update_test_plan_agents_updated_at();

-- Add comment to table
COMMENT ON TABLE test_plan_agents IS 'Test plan generation agents - stores specialized agents for test plan pipeline (Actor, Critic, Contradiction, Gap Analysis)';
COMMENT ON COLUMN test_plan_agents.agent_type IS 'Type of agent: actor, critic, contradiction, gap_analysis';
COMMENT ON COLUMN test_plan_agents.is_system_default IS 'Whether this is a system-provided default agent (pre-configured)';
COMMENT ON COLUMN test_plan_agents.metadata IS 'Additional configuration in JSON format';
