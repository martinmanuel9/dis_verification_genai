-- Migration: Unify Agent Tables
-- Description: Merge test_plan_agents into compliance_agents to create a unified, modular agent system
-- Date: 2025-11-09

-- Step 1: Add missing fields from test_plan_agents to compliance_agents
ALTER TABLE compliance_agents
ADD COLUMN IF NOT EXISTS agent_type VARCHAR(50),
ADD COLUMN IF NOT EXISTS is_system_default BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS description TEXT,
ADD COLUMN IF NOT EXISTS agent_metadata JSON DEFAULT '{}';

-- Step 2: Create indexes for new fields
CREATE INDEX IF NOT EXISTS ix_compliance_agents_agent_type ON compliance_agents(agent_type);
CREATE INDEX IF NOT EXISTS ix_compliance_agents_is_system_default ON compliance_agents(is_system_default);

-- Step 3: Migrate data from test_plan_agents to compliance_agents
-- Only insert agents that don't already exist (by name)
INSERT INTO compliance_agents (
    name,
    model_name,
    system_prompt,
    user_prompt_template,
    temperature,
    max_tokens,
    created_at,
    updated_at,
    created_by,
    is_active,
    agent_type,
    is_system_default,
    description,
    agent_metadata,
    -- Set defaults for compliance_agents-specific fields
    total_queries,
    avg_response_time_ms,
    success_rate,
    chain_type,
    memory_enabled,
    tools_enabled,
    use_structured_output,
    output_schema
)
SELECT
    tpa.name,
    tpa.model_name,
    tpa.system_prompt,
    tpa.user_prompt_template,
    tpa.temperature,
    tpa.max_tokens,
    tpa.created_at,
    tpa.updated_at,
    tpa.created_by,
    tpa.is_active,
    tpa.agent_type,
    tpa.is_system_default,
    tpa.description,
    tpa.agent_metadata,
    -- Default values for compliance-specific fields
    0 as total_queries,
    NULL as avg_response_time_ms,
    NULL as success_rate,
    'basic' as chain_type,
    FALSE as memory_enabled,
    '{}'::json as tools_enabled,
    FALSE as use_structured_output,
    NULL as output_schema
FROM test_plan_agents tpa
WHERE NOT EXISTS (
    SELECT 1 FROM compliance_agents ca
    WHERE ca.name = tpa.name
)
ORDER BY tpa.id;

-- Step 4: Add comment to document the unified structure
COMMENT ON TABLE compliance_agents IS 'Unified agent table supporting all agent types: compliance, test plan generation (actor, critic, contradiction, gap_analysis), and custom agents';
COMMENT ON COLUMN compliance_agents.agent_type IS 'Type classification: actor, critic, contradiction, gap_analysis, compliance, custom, etc.';
COMMENT ON COLUMN compliance_agents.is_system_default IS 'Whether this is a system-provided default agent';
COMMENT ON COLUMN compliance_agents.agent_metadata IS 'Flexible JSON field for agent-specific configuration';

-- Step 5: Output summary
DO $$
DECLARE
    total_agents INTEGER;
    migrated_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_agents FROM compliance_agents;
    SELECT COUNT(*) INTO migrated_count FROM compliance_agents WHERE agent_type IS NOT NULL;

    RAISE NOTICE '===========================================';
    RAISE NOTICE 'Agent Table Unification Complete';
    RAISE NOTICE '===========================================';
    RAISE NOTICE 'Total agents in compliance_agents: %', total_agents;
    RAISE NOTICE 'Agents with agent_type (migrated): %', migrated_count;
    RAISE NOTICE '===========================================';
    RAISE NOTICE 'Next Steps:';
    RAISE NOTICE '1. Update APIs to use compliance_agents table';
    RAISE NOTICE '2. Update agent_sim.py configuration';
    RAISE NOTICE '3. Consider deprecating test_plan_agents table';
    RAISE NOTICE '===========================================';
END $$;
