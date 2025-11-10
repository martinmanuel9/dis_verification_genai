-- Migration: Create Agent Sets for Orchestration
-- Date: 2025-11-09
-- Description: Create tables for managing reusable agent sequences/sets for test plan generation

-- ============================================================================
-- AGENT SETS TABLE
-- ============================================================================
-- Stores named collections of agents that can be used together in pipelines
CREATE TABLE IF NOT EXISTS agent_sets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,

    -- Set type: 'sequence' (ordered execution), 'parallel' (concurrent execution)
    set_type VARCHAR(50) NOT NULL DEFAULT 'sequence',

    -- Configuration (agents and their roles in this set)
    set_config JSONB NOT NULL,
    /* Example set_config structure:
    {
        "stages": [
            {
                "stage_name": "actor",
                "agent_ids": [1, 1, 1],  -- Can include same agent multiple times
                "execution_mode": "parallel"
            },
            {
                "stage_name": "critic",
                "agent_ids": [2],
                "execution_mode": "sequential"
            },
            {
                "stage_name": "qa",
                "agent_ids": [3, 4],  -- Contradiction and Gap Analysis
                "execution_mode": "parallel"
            }
        ]
    }
    */

    -- Metadata
    is_system_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    usage_count INTEGER DEFAULT 0,  -- Track how often this set is used

    -- Audit fields
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES
-- ============================================================================
CREATE INDEX IF NOT EXISTS ix_agent_sets_name ON agent_sets(name);
CREATE INDEX IF NOT EXISTS ix_agent_sets_set_type ON agent_sets(set_type);
CREATE INDEX IF NOT EXISTS ix_agent_sets_is_system_default ON agent_sets(is_system_default);
CREATE INDEX IF NOT EXISTS ix_agent_sets_is_active ON agent_sets(is_active);
CREATE INDEX IF NOT EXISTS ix_agent_sets_created_at ON agent_sets(created_at);

-- ============================================================================
-- TRIGGERS
-- ============================================================================
-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_agent_sets_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_agent_sets_updated_at
    BEFORE UPDATE ON agent_sets
    FOR EACH ROW
    EXECUTE FUNCTION update_agent_sets_updated_at();

-- ============================================================================
-- COMMENTS
-- ============================================================================
COMMENT ON TABLE agent_sets IS 'Reusable collections of agents for test plan generation pipelines';
COMMENT ON COLUMN agent_sets.set_type IS 'Type of set: sequence (ordered), parallel (concurrent), or custom';
COMMENT ON COLUMN agent_sets.set_config IS 'JSON configuration defining stages, agents, and execution modes';
COMMENT ON COLUMN agent_sets.is_system_default IS 'Whether this is a system-provided default set';
COMMENT ON COLUMN agent_sets.usage_count IS 'Number of times this set has been used (incremented on each use)';

-- ============================================================================
-- DEFAULT AGENT SETS
-- ============================================================================

-- Default Set 1: Standard Test Plan Pipeline
INSERT INTO agent_sets (name, description, set_type, set_config, is_system_default, created_by)
VALUES (
    'Standard Test Plan Pipeline',
    'Standard multi-agent pipeline with actor, critic, QA agents. Recommended for comprehensive test plan generation.',
    'sequence',
    '{
        "stages": [
            {
                "stage_name": "actor",
                "agent_ids": [1, 1, 1],
                "execution_mode": "parallel",
                "description": "3 actor agents analyze sections in parallel"
            },
            {
                "stage_name": "critic",
                "agent_ids": [2],
                "execution_mode": "sequential",
                "description": "Critic synthesizes and deduplicates actor outputs"
            },
            {
                "stage_name": "qa",
                "agent_ids": [3, 4],
                "execution_mode": "parallel",
                "description": "Contradiction detection and gap analysis in parallel"
            }
        ]
    }'::jsonb,
    TRUE,
    'system'
) ON CONFLICT (name) DO NOTHING;

-- Default Set 2: Quick Draft (No QA)
INSERT INTO agent_sets (name, description, set_type, set_config, is_system_default, created_by)
VALUES (
    'Quick Draft Pipeline',
    'Fast pipeline without quality assurance steps. Use for rapid prototyping and drafts.',
    'sequence',
    '{
        "stages": [
            {
                "stage_name": "actor",
                "agent_ids": [1],
                "execution_mode": "sequential",
                "description": "Single actor agent for quick analysis"
            },
            {
                "stage_name": "critic",
                "agent_ids": [2],
                "execution_mode": "sequential",
                "description": "Basic synthesis without QA"
            }
        ]
    }'::jsonb,
    TRUE,
    'system'
) ON CONFLICT (name) DO NOTHING;

-- Default Set 3: Comprehensive QA Pipeline
INSERT INTO agent_sets (name, description, set_type, set_config, is_system_default, created_by)
VALUES (
    'Comprehensive QA Pipeline',
    'Full quality assurance pipeline with multiple actors and extensive QA. Use for critical compliance documents.',
    'sequence',
    '{
        "stages": [
            {
                "stage_name": "actor",
                "agent_ids": [1, 1, 1, 1, 1],
                "execution_mode": "parallel",
                "description": "5 actor agents for thorough analysis"
            },
            {
                "stage_name": "critic",
                "agent_ids": [2],
                "execution_mode": "sequential",
                "description": "Comprehensive synthesis"
            },
            {
                "stage_name": "contradiction_detection",
                "agent_ids": [3, 3],
                "execution_mode": "parallel",
                "description": "Dual contradiction detection for confidence"
            },
            {
                "stage_name": "gap_analysis",
                "agent_ids": [4],
                "execution_mode": "sequential",
                "description": "Thorough gap analysis"
            }
        ]
    }'::jsonb,
    TRUE,
    'system'
) ON CONFLICT (name) DO NOTHING;

-- Default Set 4: Custom Actor Set Example
INSERT INTO agent_sets (name, description, set_type, set_config, is_system_default, created_by)
VALUES (
    'Mixed Agent Set Example',
    'Example showing how to mix different agent types. Clone this to create custom sets.',
    'sequence',
    '{
        "stages": [
            {
                "stage_name": "initial_analysis",
                "agent_ids": [2, 1, 4],
                "execution_mode": "parallel",
                "description": "Critic, Actor, Gap Analysis in parallel"
            },
            {
                "stage_name": "synthesis",
                "agent_ids": [2],
                "execution_mode": "sequential",
                "description": "Final synthesis"
            }
        ]
    }'::jsonb,
    TRUE,
    'system'
) ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- VERIFICATION
-- ============================================================================
-- Verify the migration
DO $$
BEGIN
    RAISE NOTICE 'Agent Sets table created successfully';
    RAISE NOTICE 'Seeded % default agent sets', (SELECT COUNT(*) FROM agent_sets WHERE is_system_default = TRUE);
END $$;
