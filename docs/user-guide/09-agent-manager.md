# Agent & Orchestration Manager

Create, configure, and manage custom AI agents for document analysis.

## Overview

The Agent Manager allows you to:
- Create custom AI agents with specific roles
- Configure agent prompts and behavior
- Organize agents into sets
- Run single or multiple agents on documents
- Orchestrate complex multi-agent workflows

## Creating Custom Agents

### Step 1: Access Agent Manager

1. Select Mode: **⚙️ Agent & Orchestration Manager**
2. Click **Create New Agent**

### Step 2: Configure Agent

[Screenshot: Agent creation form]

```
┌──────────────────────────────────────┐
│ Create New Agent                     │
├──────────────────────────────────────┤
│ Agent Name: *                        │
│ [Security Requirements Analyst    ]  │
│                                      │
│ Description:                         │
│ [Identifies security requirements    │
│  and generates security test cases]  │
│                                      │
│ Role/Purpose:                        │
│ [Extract and analyze all security-   │
│  related requirements from docs]     │
│                                      │
│ AI Model: [gpt-4o ▼]                │
│                                      │
│ Temperature: [0.3 ▼]                │
│ ├─ Precise ────●──── Creative       │
│                                      │
│ Max Tokens: [4000 ▼]                │
│                                      │
│ System Prompt:                       │
│ ┌────────────────────────────────┐  │
│ │You are an expert security      │  │
│ │analyst specializing in...      │  │
│ │                                │  │
│ └────────────────────────────────┘  │
│                                      │
│ User Prompt Template:                │
│ ┌────────────────────────────────┐  │
│ │Analyze the following document  │  │
│ │and extract all security reqs:  │  │
│ │{document_content}              │  │
│ └────────────────────────────────┘  │
│                                      │
│ Output Format: [Structured JSON ▼]  │
│                                      │
│ Created By: John Doe                 │
│ Tags: [security] [requirements]      │
│                                      │
│ [Cancel]              [Create Agent] │
└──────────────────────────────────────┘
```

### Step 3: Test Agent

Before saving, test the agent:

```
Test Agent Output

Input: [Sample security requirement text]

[Run Test]

Output:
{
  "requirements": [
    {
      "id": "SEC-001",
      "text": "System shall use TLS 1.3...",
      "priority": "Critical",
      "test_cases": [...]
    }
  ]
}

Quality Score: 9.2/10
Processing Time: 3.4s

[Looks Good] [Adjust Settings]
```

## Agent Configuration

### System Prompts

Define agent personality and expertise:

**Example: Requirements Analyst**
```
You are an expert requirements engineer with 20 years of
experience in defense systems.

Your expertise includes:
- Extracting functional and non-functional requirements
- Identifying requirement ambiguities
- Classifying requirements by priority
- Ensuring requirements traceability

Always:
- Be precise and factual
- Cite source locations (page, section)
- Use standard requirement keywords (SHALL, MUST, SHOULD)
- Identify unclear or incomplete requirements
```

**Example: Test Case Generator**
```
You are a senior test engineer specializing in comprehensive
test coverage.

For each requirement, you create:
1. Positive test (happy path)
2. Negative test (error handling)
3. Boundary test (edge cases)
4. Integration test (if applicable)

Your test cases are:
- Clear and actionable
- Include prerequisites
- Specify expected results
- Reference source requirements
```

### User Prompt Templates

Template for each agent invocation:

**Variables Available**:
- `{document_content}` - Full document text
- `{document_name}` - Document filename
- `{section}` - Specific section (if chunked)
- `{previous_output}` - Output from previous agent
- `{user_instruction}` - User's specific request

**Example Template**:
```
Analyze the following technical specification document:

Document: {document_name}
Content:
{document_content}

Task: {user_instruction}

Additional Context:
Previous analysis from requirements agent:
{previous_output}

Provide structured output in JSON format.
```

### Output Formats

Specify how agent should format responses:

**Structured JSON**:
```json
{
  "summary": "...",
  "findings": [...],
  "recommendations": [...]
}
```

**Markdown**:
```markdown
# Analysis Results

## Summary
...

## Findings
1. ...
2. ...
```

**Plain Text**:
```
Requirements found: 45
Critical: 12
High: 18
Medium: 15
```

## Managing Agents

### Agent Library

View all created agents:

[Screenshot: Agent library view]

```
My Agents (23)

Filter: [Security ▼] Sort: [Recently Used ▼]

┌─────────────────────────────────────────────┐
│ ★ Security Requirements Analyst             │
│ Extract security requirements & generate... │
│ Model: gpt-4o | Used: 45 times             │
│ Tags: security, requirements                │
│ [Edit] [Run] [Duplicate] [Delete]          │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ Performance Test Generator                  │
│ Create performance and load test cases...   │
│ Model: llama3.1:8b | Used: 12 times        │
│ Tags: performance, testing                  │
│ [Edit] [Run] [Duplicate] [Delete]          │
└─────────────────────────────────────────────┘
```

### Agent Actions

**Edit**: Modify agent configuration
**Run**: Execute agent on document
**Duplicate**: Create copy for customization
**Share**: Export agent config (future)
**Delete**: Remove agent

## Agent Sets

Group agents for complex workflows.

### Creating Agent Sets

```
┌──────────────────────────────────────┐
│ Create Agent Set                     │
├──────────────────────────────────────┤
│ Name: Comprehensive Security Review  │
│                                      │
│ Description:                         │
│ Full security analysis with multiple │
│ perspectives and validation          │
│                                      │
│ Agents in Set (drag to reorder):    │
│                                      │
│ 1. ☰ Security Requirements Analyst  │
│ 2. ☰ Threat Modeling Agent          │
│ 3. ☰ Security Test Generator        │
│ 4. ☰ Compliance Validator            │
│ 5. ☰ Security Review Critic          │
│                                      │
│ [+ Add Agent]                        │
│                                      │
│ Execution Mode:                      │
│ ● Sequential (one after another)     │
│ ○ Parallel (all at once)            │
│ ○ Hierarchical (staged)             │
│                                      │
│ Agent Interaction:                   │
│ ☑ Pass outputs to next agent        │
│ ☑ Enable agent debate               │
│ ☐ Require consensus                  │
│                                      │
│ [Cancel]           [Create Set]      │
└──────────────────────────────────────┘
```

### Execution Modes

**Sequential**:
```
Agent 1 → Agent 2 → Agent 3 → Agent 4
```
Each agent sees previous outputs.

**Parallel**:
```
       ┌─ Agent 1 ─┐
Doc ──┼─ Agent 2 ─┼─→ Combine
       └─ Agent 3 ─┘
```
All agents analyze independently.

**Hierarchical**:
```
Level 1: Agent 1, Agent 2, Agent 3
         ↓
Level 2: Synthesis Agent
         ↓
Level 3: Validation Agent
```

## Running Agents

### Single Agent Execution

1. Select agent from library
2. Click **Run**
3. Choose document
4. Add instructions (optional)
5. Click **Start**

[Screenshot: Single agent execution]

```
Run Agent: Security Requirements Analyst

Document: [Technical_Spec_v2.pdf ▼]

Additional Instructions (optional):
[Focus on authentication and authorization
requirements. Include threat analysis.]

Model Override: [Use agent default ▼]
Temperature Override: [Use agent default ▼]

[Cancel]                    [Run Agent]
```

### Multi-Agent Orchestration

1. Select agent set
2. Choose document
3. Configure run parameters
4. Monitor progress

[Screenshot: Multi-agent orchestration progress]

```
Running: Comprehensive Security Review

Overall Progress: ████████████░░░░░░░░ 60%

Agent Status:
✓ Security Requirements Analyst (4m 23s)
  → Found 34 security requirements
  
✓ Threat Modeling Agent (6m 12s)
  → Identified 18 potential threats
  
▶ Security Test Generator (in progress)
  Current: Generating test case 12/34
  
⏳ Compliance Validator (queued)
⏳ Security Review Critic (queued)

[View Live Output] [Cancel Run]
```

## Advanced Features

### Agent Chaining

Create workflows where agents build on each other:

```
Document
   ↓
[Requirements Extractor]
   ↓ (requirements list)
[Test Case Generator]
   ↓ (test cases)
[Procedure Writer]
   ↓ (detailed procedures)
[Review Critic]
   ↓
Final Output
```

### Conditional Logic

Run agents based on conditions:

```
If document.type == "API Spec":
    Run API Testing Agent Set
Else if document.type == "UI Spec":
    Run UI Testing Agent Set
Else:
    Run General Testing Agent Set
```

### Feedback Loops

Agents refine based on critic feedback:

```
Round 1: Agent generates output
         ↓
         Critic reviews (issues found)
         ↓
Round 2: Agent refines output
         ↓
         Critic reviews (fewer issues)
         ↓
Round 3: Agent final refinement
         ↓
         Critic approves
```

## Best Practices

### Agent Specialization

Create focused agents:

✅ **Good**: "API Authentication Test Generator"
❌ **Bad**: "General Testing Agent"

### Prompt Engineering

- Be specific about role and expertise
- Provide examples of desired output
- Define quality criteria
- Specify output format
- Include constraints

### Model Selection

Choose appropriate models:

**Analysis/Extraction**: gpt-4o (high accuracy)
**Test Generation**: gpt-4o-mini (fast, cost-effective)
**Validation/Review**: gpt-4o (thorough)
**Local/Private**: llama3.1:8b (on-premises)

### Temperature Guidelines

- **0.0-0.2**: Factual extraction, classification
- **0.3-0.5**: Requirements analysis, validation
- **0.6-0.8**: Test case generation, creativity
- **0.9-1.2**: Brainstorming, alternatives

## Next Steps

- **[Multi-Agent Analysis](07-multi-agent-analysis.md)** - Understand agent collaboration
- **[Document Generator](06-document-generator.md)** - Use agents for test plan generation
- **[Model Selection](11-model-selection.md)** - Choose right models

---

See [FAQ](13-faq.md) for agent questions
