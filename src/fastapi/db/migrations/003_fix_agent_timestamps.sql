-- Migration: Fix NULL timestamps in existing agent records
-- Date: 2025-11-08
-- Description: Update NULL created_at and updated_at values with CURRENT_TIMESTAMP
--              for agents seeded before defaults were properly applied

-- Update NULL created_at values
UPDATE test_plan_agents
SET created_at = CURRENT_TIMESTAMP
WHERE created_at IS NULL;

-- Update NULL updated_at values
UPDATE test_plan_agents
SET updated_at = CURRENT_TIMESTAMP
WHERE updated_at IS NULL;

-- Verify fix
SELECT
    COUNT(*) as total_agents,
    COUNT(created_at) as has_created_at,
    COUNT(updated_at) as has_updated_at
FROM test_plan_agents;
