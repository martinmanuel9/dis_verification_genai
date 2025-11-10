-- Migration: Rename metadata column to agent_metadata
-- Date: 2025-11-08
-- Description: Rename 'metadata' column to 'agent_metadata' to avoid conflict
--              with SQLAlchemy's MetaData class attribute

-- Rename column only if it exists (idempotent)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'test_plan_agents'
          AND column_name = 'metadata'
    ) THEN
        ALTER TABLE test_plan_agents RENAME COLUMN metadata TO agent_metadata;
    END IF;
END $$;

-- Verify
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'test_plan_agents'
  AND column_name = 'agent_metadata';
