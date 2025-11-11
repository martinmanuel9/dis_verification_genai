-- ============================================================================
-- FRESH INSTALL SCHEMA
-- ============================================================================
-- This migration creates the complete database schema for fresh installations.
-- It replaces migrations 001-010 with a single optimized schema.
--
-- Date: 2025-11-11
-- Version: 1.0
-- ============================================================================

-- ============================================================================
-- TABLE: compliance_agents
-- ============================================================================
-- Unified agent table supporting all workflows:
-- - Test Plan Generation (actor, critic, contradiction, gap_analysis)
-- - Document Analysis (compliance, custom)
-- - General Purpose (general, rule_development, custom)

CREATE TABLE IF NOT EXISTS compliance_agents (
    id SERIAL PRIMARY KEY,
    name VARCHAR UNIQUE NOT NULL,
    model_name VARCHAR NOT NULL,
    system_prompt TEXT NOT NULL,
    user_prompt_template TEXT NOT NULL,
    temperature FLOAT DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 300,

    -- Agent classification
    agent_type VARCHAR,  -- actor, critic, contradiction, gap_analysis, compliance, custom, general, rule_development
    workflow_type VARCHAR,  -- document_analysis, test_plan_generation, general

    -- Metadata
    is_system_default BOOLEAN DEFAULT FALSE,
    description TEXT,
    agent_metadata JSON DEFAULT '{}',

    -- Advanced features
    use_structured_output BOOLEAN DEFAULT FALSE,
    output_schema JSON,
    chain_type VARCHAR DEFAULT 'basic',
    memory_enabled BOOLEAN DEFAULT FALSE,
    tools_enabled JSON DEFAULT '{}',

    -- Performance tracking
    total_queries INTEGER DEFAULT 0,
    avg_response_time_ms FLOAT,
    success_rate FLOAT,

    -- Audit fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR,
    is_active BOOLEAN DEFAULT TRUE
);

-- Indexes for compliance_agents
CREATE INDEX IF NOT EXISTS idx_compliance_agents_agent_type ON compliance_agents(agent_type);
CREATE INDEX IF NOT EXISTS idx_compliance_agents_workflow_type ON compliance_agents(workflow_type);
CREATE INDEX IF NOT EXISTS idx_compliance_agents_is_system_default ON compliance_agents(is_system_default);
CREATE INDEX IF NOT EXISTS idx_compliance_agents_created_at ON compliance_agents(created_at);

-- ============================================================================
-- TABLE: agent_sets
-- ============================================================================
-- Orchestration pipelines combining multiple agents in stages

CREATE TABLE IF NOT EXISTS agent_sets (
    id SERIAL PRIMARY KEY,
    name VARCHAR UNIQUE NOT NULL,
    description TEXT,
    set_type VARCHAR DEFAULT 'sequence',  -- sequence, parallel, custom
    set_config JSON NOT NULL,  -- {stages: [{stage_name, agent_ids, execution_mode}]}

    -- Metadata
    is_system_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    usage_count INTEGER DEFAULT 0,

    -- Audit fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR
);

-- Indexes for agent_sets
CREATE INDEX IF NOT EXISTS idx_agent_sets_is_system_default ON agent_sets(is_system_default);
CREATE INDEX IF NOT EXISTS idx_agent_sets_is_active ON agent_sets(is_active);

-- ============================================================================
-- SEED: Test Plan Generation Agents (4 agents)
-- ============================================================================

INSERT INTO compliance_agents (
    name, agent_type, workflow_type, model_name, system_prompt, user_prompt_template,
    temperature, max_tokens, is_system_default, is_active, created_by, description,
    agent_metadata, created_at, updated_at
) VALUES
-- Actor Agent
(
    'Actor Agent (Default)',
    'actor',
    'test_plan_generation',
    'gpt-4',
    'You are an Actor Agent specialized in extracting testable requirements from military standard documents.

Your role is to carefully analyze each section and extract EVERY possible testable rule, specification, constraint, or requirement.',
    'Analyze the following section of a military standard and extract EVERY possible testable rule, specification, constraint, or requirement.

REQUIREMENTS:
1. Rules MUST be extremely detailed, explicit, and testable
2. Extract ALL rules, including implied ones
3. Each rule must be independently verifiable
4. Use precise technical language
5. Reference section numbers

## SECTION TITLE
{section_title}

## SECTION CONTENT
{section_content}

---

PROVIDE YOUR RESPONSE IN THE FOLLOWING JSON FORMAT:
{
  "extracted_rules": [
    {
      "rule_id": "unique_id",
      "description": "detailed rule description",
      "test_method": "how to verify this rule",
      "priority": "high|medium|low",
      "references": ["section references"]
    }
  ]
}',
    0.7,
    4000,
    TRUE,
    TRUE,
    'system',
    'Extracts testable requirements from document sections with detailed analysis',
    '{}',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),

-- Critic Agent
(
    'Critic Agent (Default)',
    'critic',
    'test_plan_generation',
    'gpt-4',
    'You are a Critic Agent responsible for synthesizing and deduplicating outputs from multiple Actor agents.

Your role is to:
1. Merge similar rules from different actors
2. Remove exact duplicates
3. Resolve conflicts
4. Create a single coherent set of test procedures',
    'Review the following actor outputs and synthesize them into a coherent, deduplicated set of test procedures.

## SECTION TITLE
{section_title}

## SECTION CONTENT
{section_content}

## ACTOR OUTPUTS
{actor_outputs}

---

PROVIDE SYNTHESIZED TEST PROCEDURES:
1. Merge similar rules
2. Remove duplicates
3. Resolve conflicts
4. Maintain traceability to original rules',
    0.7,
    4000,
    TRUE,
    TRUE,
    'system',
    'Synthesizes and deduplicates outputs from multiple actor agents',
    '{}',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),

-- Contradiction Detection Agent
(
    'Contradiction Detection Agent (Default)',
    'contradiction',
    'test_plan_generation',
    'gpt-4',
    'You are a Contradiction Detection Agent specialized in identifying conflicts and inconsistencies in test procedures.

Your role is to detect:
1. Direct contradictions between test steps
2. Conflicting requirements across sections
3. Logical inconsistencies
4. Mutually exclusive conditions',
    'Analyze the following test plan section for contradictions and conflicts.

## SECTION TITLE
{section_title}

## SYNTHESIZED TEST PROCEDURES (from Critic Agent)
{critic_output}

## ACTOR OUTPUTS (for comparison)
{actor_outputs_summary}

## PREVIOUS SECTIONS (for cross-section analysis)
{previous_sections_summary}

---

IDENTIFY AND REPORT:
1. Direct contradictions
2. Conflicting requirements
3. Logical inconsistencies
4. Recommended resolutions',
    0.4,
    3000,
    TRUE,
    TRUE,
    'system',
    'Detects contradictions and conflicts in test procedures',
    '{}',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),

-- Gap Analysis Agent
(
    'Gap Analysis Agent (Default)',
    'gap_analysis',
    'test_plan_generation',
    'gpt-4',
    'You are a Gap Analysis Agent specialized in identifying missing requirements and test coverage gaps.

Your role is to ensure:
1. All requirements from the standard are covered
2. No test procedures are missing
3. Edge cases are addressed
4. Complete test coverage',
    'Analyze the test plan for gaps and missing coverage.

## SECTION TITLE
{section_title}

## SECTION CONTENT (Original Standard)
{section_content}

## SYNTHESIZED TEST PROCEDURES
{critic_output}

---

IDENTIFY GAPS:
1. Missing test procedures
2. Uncovered requirements
3. Edge cases not addressed
4. Recommended additions',
    0.5,
    3000,
    TRUE,
    TRUE,
    'system',
    'Identifies missing requirements and test coverage gaps',
    '{}',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- ============================================================================
-- SEED: Document Analysis Agents (4 agents)
-- ============================================================================

INSERT INTO compliance_agents (
    name, agent_type, workflow_type, model_name, system_prompt, user_prompt_template,
    temperature, max_tokens, is_system_default, is_active, created_by, description,
    agent_metadata, created_at, updated_at
) VALUES
-- Compliance Checker
(
    'Compliance Checker (Document Analysis)',
    'compliance',
    'document_analysis',
    'gpt-4',
    'You are a compliance verification expert specializing in analyzing technical documents, standards, and requirements.

Your role is to carefully evaluate whether the provided content meets specified requirements, identify compliance issues, and provide detailed analysis.',
    'Analyze the following content for compliance and provide a detailed assessment:

{data_sample}

---

Provide your analysis in the following format:

## Compliance Assessment

**Overall Status:** [Compliant / Non-Compliant / Partially Compliant]

**Key Findings:**
- List the most important compliance observations
- Identify any violations or gaps
- Note areas of strength

**Detailed Analysis:**
Provide a thorough evaluation of the content, including:
1. Specific compliance issues found
2. Requirements that are met
3. Requirements that are missing or unclear
4. Recommendations for achieving full compliance

**Risk Assessment:**
- Highlight any high-priority compliance risks
- Suggest mitigation strategies',
    0.3,
    2000,
    TRUE,
    TRUE,
    'system',
    'Evaluates documents for compliance with requirements and standards',
    '{}',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),

-- Requirements Extractor
(
    'Requirements Extractor (Document Analysis)',
    'custom',
    'document_analysis',
    'gpt-4',
    'You are an expert at extracting and analyzing requirements from technical documents, specifications, and standards.

Your role is to identify explicit and implicit requirements, categorize them, and present them in a structured format.',
    'Extract all requirements from the following content:

{data_sample}

---

Provide your analysis in the following format:

## Extracted Requirements

**Mandatory Requirements (SHALL/MUST):**
1. [Requirement text with reference]
2. [Requirement text with reference]

**Recommended Requirements (SHOULD):**
1. [Requirement text with reference]
2. [Requirement text with reference]

**Optional Requirements (MAY):**
1. [Requirement text with reference]

**Implicit Requirements:**
- [Requirements that are implied but not explicitly stated]

**Categorization:**
- **Functional:** [Number] requirements
- **Performance:** [Number] requirements
- **Security:** [Number] requirements
- **Quality:** [Number] requirements
- **Other:** [Number] requirements

**Notes:**
- Highlight any ambiguous or unclear requirements
- Identify dependencies between requirements',
    0.5,
    2500,
    TRUE,
    TRUE,
    'system',
    'Extracts and categorizes requirements from technical documents',
    '{}',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),

-- Technical Reviewer
(
    'Technical Reviewer (Document Analysis)',
    'custom',
    'document_analysis',
    'gpt-4',
    'You are a senior technical reviewer with expertise in evaluating technical documentation, code, architectures, and engineering designs.

Your role is to provide thorough, constructive technical reviews focusing on correctness, completeness, quality, and best practices.',
    'Provide a comprehensive technical review of the following content:

{data_sample}

---

Structure your review as follows:

## Technical Review

**Executive Summary:**
Provide a 2-3 sentence overview of the content and your assessment.

**Strengths:**
- Identify what is done well
- Highlight positive aspects

**Issues Found:**
**Critical Issues:**
1. [Issue description and impact]

**Major Issues:**
1. [Issue description and impact]

**Minor Issues:**
1. [Issue description and impact]

**Recommendations:**
1. [Specific, actionable recommendations for improvement]
2. [Consider best practices and industry standards]

**Technical Observations:**
- Note any technical patterns, anti-patterns, or design decisions
- Comment on clarity, maintainability, and completeness

**Overall Rating:** [Excellent / Good / Acceptable / Needs Improvement / Poor]',
    0.4,
    2500,
    TRUE,
    TRUE,
    'system',
    'Provides comprehensive technical reviews of documents and content',
    '{}',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),

-- General Document Analyzer
(
    'General Document Analyzer (Document Analysis)',
    'custom',
    'document_analysis',
    'gpt-4o',
    'You are a versatile document analysis expert capable of analyzing any type of technical or business content.

Your role is to provide clear, structured analysis that helps users understand and work with the provided content.',
    'Analyze the following content and provide a comprehensive breakdown:

{data_sample}

---

Provide your analysis:

## Document Analysis

**Content Type:** [Identify the type of content - e.g., specification, policy, procedure, code, etc.]

**Purpose & Context:**
Briefly describe the purpose and context of this content.

**Key Points:**
1. [Main point or theme]
2. [Main point or theme]
3. [Main point or theme]

**Detailed Analysis:**
Provide a thorough analysis including:
- Main concepts and their relationships
- Important details and nuances
- Potential questions or areas needing clarification
- Practical implications

**Structure & Organization:**
Comment on how well the content is organized and presented.

**Actionable Insights:**
What should someone do with this information? Provide practical next steps or applications.

**Questions & Clarifications:**
List any questions that arise or areas that need clarification.',
    0.6,
    2500,
    TRUE,
    TRUE,
    'system',
    'General-purpose analyzer for any type of document or content',
    '{}',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- ============================================================================
-- SEED: Agent Sets (4 pipelines)
-- ============================================================================

INSERT INTO agent_sets (
    name, description, set_type, set_config, is_system_default, is_active,
    usage_count, created_at, updated_at, created_by
) VALUES
-- Standard Test Plan Pipeline
(
    'Standard Test Plan Pipeline',
    'Standard multi-agent pipeline with actor, critic, QA agents. Recommended for comprehensive test plan generation.',
    'sequence',
    '{
      "stages": [
        {
          "stage_name": "actor",
          "agent_ids": [1, 1, 1],
          "execution_mode": "parallel",
          "description": "Three actor agents analyze sections in parallel"
        },
        {
          "stage_name": "critic",
          "agent_ids": [2],
          "execution_mode": "sequential",
          "description": "Critic synthesizes actor outputs"
        },
        {
          "stage_name": "qa",
          "agent_ids": [3, 4],
          "execution_mode": "parallel",
          "description": "QA agents check for contradictions and gaps"
        }
      ]
    }',
    TRUE,
    TRUE,
    0,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP,
    'system'
),

-- Quick Draft Pipeline
(
    'Quick Draft Pipeline',
    'Fast pipeline without quality assurance steps. Use for rapid prototyping and drafts.',
    'sequence',
    '{
      "stages": [
        {
          "stage_name": "actor",
          "agent_ids": [1, 1],
          "execution_mode": "parallel",
          "description": "Two actor agents for quick analysis"
        },
        {
          "stage_name": "critic",
          "agent_ids": [2],
          "execution_mode": "sequential",
          "description": "Critic synthesizes outputs"
        }
      ]
    }',
    TRUE,
    TRUE,
    0,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP,
    'system'
),

-- Comprehensive QA Pipeline
(
    'Comprehensive QA Pipeline',
    'Full quality assurance pipeline with multiple actors and extensive QA. Use for critical compliance documents.',
    'sequence',
    '{
      "stages": [
        {
          "stage_name": "actor",
          "agent_ids": [1, 1, 1, 1],
          "execution_mode": "parallel",
          "description": "Four actor agents for thorough analysis"
        },
        {
          "stage_name": "critic",
          "agent_ids": [2],
          "execution_mode": "sequential",
          "description": "Critic synthesizes all outputs"
        },
        {
          "stage_name": "contradiction",
          "agent_ids": [3],
          "execution_mode": "sequential",
          "description": "Check for contradictions"
        },
        {
          "stage_name": "gap_analysis",
          "agent_ids": [4],
          "execution_mode": "sequential",
          "description": "Identify coverage gaps"
        }
      ]
    }',
    TRUE,
    TRUE,
    0,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP,
    'system'
),

-- Mixed Agent Set Example
(
    'Mixed Agent Set Example',
    'Example showing how to mix different agent types. Clone this to create custom sets.',
    'sequence',
    '{
      "stages": [
        {
          "stage_name": "analysis",
          "agent_ids": [1, 1],
          "execution_mode": "parallel",
          "description": "Parallel analysis stage"
        },
        {
          "stage_name": "synthesis",
          "agent_ids": [2],
          "execution_mode": "sequential",
          "description": "Synthesis stage"
        }
      ]
    }',
    TRUE,
    TRUE,
    0,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP,
    'system'
);

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
DECLARE
    agent_count INTEGER;
    agent_set_count INTEGER;
    test_plan_agents INTEGER;
    doc_analysis_agents INTEGER;
BEGIN
    SELECT COUNT(*) INTO agent_count FROM compliance_agents;
    SELECT COUNT(*) INTO agent_set_count FROM agent_sets;
    SELECT COUNT(*) INTO test_plan_agents FROM compliance_agents WHERE workflow_type = 'test_plan_generation';
    SELECT COUNT(*) INTO doc_analysis_agents FROM compliance_agents WHERE workflow_type = 'document_analysis';

    RAISE NOTICE '========================================';
    RAISE NOTICE 'FRESH INSTALL COMPLETE';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Total Agents: %', agent_count;
    RAISE NOTICE '  - Test Plan Generation: %', test_plan_agents;
    RAISE NOTICE '  - Document Analysis: %', doc_analysis_agents;
    RAISE NOTICE 'Total Agent Sets: %', agent_set_count;
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Database schema ready for use!';
    RAISE NOTICE '========================================';
END $$;
