-- Migration: Add general and rule_development agent types
-- Date: 2025-11-08
-- Description: Expand test_plan_agents table to support all agent types
--              This consolidates the old agent system into the unified database-backed system

-- The agent_type column already exists as VARCHAR, so we don't need to modify it
-- We just need to update the comment to reflect the new agent types

COMMENT ON COLUMN test_plan_agents.agent_type IS 'Type of agent: actor, critic, contradiction, gap_analysis, general, rule_development, or custom';

-- Update table comment
COMMENT ON TABLE test_plan_agents IS 'Unified agent storage - stores ALL agents in the system (test plan agents, general agents, rule development agents, custom agents)';

-- Verify the change
SELECT
    table_name,
    column_name,
    data_type,
    col_description('test_plan_agents'::regclass, ordinal_position) as column_comment
FROM information_schema.columns
WHERE table_name = 'test_plan_agents'
  AND column_name = 'agent_type';
