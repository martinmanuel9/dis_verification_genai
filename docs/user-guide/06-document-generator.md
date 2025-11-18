# Document Generator Mode

Generate comprehensive test plans and verification procedures from technical documents using multi-agent AI analysis.

## Overview

Document Generator Mode uses multiple AI agents working together to:

- **Extract requirements** from specification documents
- **Generate test cases** based on requirements
- **Create detailed test procedures** with step-by-step instructions
- **Identify contradictions** and gaps in requirements
- **Produce formatted outputs** (Markdown, Word documents)

[Screenshot: Document Generator interface]

## How It Works

### Multi-Agent System

```
                    Your Document
                         ↓
        ┌────────────────┼────────────────┐
        ↓                ↓                ↓
   Actor Agent 1   Actor Agent 2   Actor Agent 3
   (Requirements)  (Test Cases)    (Procedures)
        ↓                ↓                ↓
        └────────────────┼────────────────┘
                         ↓
                  Critic Agent
              (Validates & Refines)
                         ↓
              Contradiction Agent
            (Finds Conflicts & Gaps)
                         ↓
                 Final Test Plan
```

**Agent Roles**:

1. **Actor Agents** (3-5 agents)
   - Analyze document from different perspectives
   - Extract requirements, test scenarios
   - Propose test procedures
   - Work independently in parallel

2. **Critic Agent**
   - Reviews actor outputs
   - Validates completeness
   - Refines and consolidates
   - Ensures consistency

3. **Contradiction Agent**
   - Identifies conflicting requirements
   - Finds gaps in coverage
   - Highlights ambiguities
   - Suggests resolutions

## Getting Started

### Step 1: Upload Document

First, upload the specification document:

1. Go to **📁 Files** page
2. Upload your document (PDF or DOCX)
3. Wait for processing to complete

See [Document Management](05-document-management.md) for details.

### Step 2: Select Document Generator Mode

1. In sidebar, select **Mode**: **📄 Document Generator**
2. Interface changes to show document selector

[Screenshot: Document Generator mode selected]

### Step 3: Choose Document

Select which document to analyze:

```
Select Document: [Technical_Spec_v2.pdf ▼]

Document Info:
• Filename: Technical_Spec_v2.pdf
• Pages: 87
• Size: 4.2 MB
• Uploaded: 2025-11-18 14:30
• Status: ✓ Processed
• Chunks: 234

[Document Preview ▼]
```

[Screenshot: Document selection with preview]

### Step 4: Configure Generation

Choose analysis options:

**Analysis Depth**:
```
○ Quick Analysis (5-10 min)
  • 2 actor agents
  • Basic critic review
  • Essential test cases only

● Standard Analysis (15-30 min)
  • 3 actor agents
  • Full critic review
  • Comprehensive test coverage
  • Contradiction detection

○ Deep Analysis (30-60 min)
  • 5 actor agents
  • Multi-round critic review
  • Exhaustive test coverage
  • Full contradiction analysis
  • Gap identification
```

**Agent Configuration**:
```
Active Agents:
☑ Actor Agent 1 - Requirements Extraction
☑ Actor Agent 2 - Test Scenario Generation
☑ Actor Agent 3 - Procedure Development
☑ Critic Agent - Validation & Refinement
☑ Contradiction Agent - Conflict Detection
☐ Custom Agent - [Select from library]

AI Model: [gpt-4o ▼]
Temperature: [0.3 ▼] (more deterministic for testing)
```

**Output Options**:
```
☑ Generate Test Plan (Markdown)
☑ Generate Test Cards (Word .docx)
☑ Generate Requirements Matrix (CSV)
☑ Generate Coverage Report (PDF)
☐ Include Agent Debate Transcript
```

[Screenshot: Configuration panel with all options]

### Step 5: Start Generation

1. Review your settings
2. Click **🚀 Generate Test Plan**
3. Confirmation dialog appears:

```
┌─────────────────────────────────────────┐
│ Generate Test Plan                      │
├─────────────────────────────────────────┤
│ Document: Technical_Spec_v2.pdf         │
│ Analysis: Standard (est. 15-30 min)     │
│ Agents: 5 agents                        │
│ Model: gpt-4o                           │
│ Estimated cost: ~$0.50                  │
│                                         │
│ This will analyze 87 pages and generate │
│ a comprehensive test plan.              │
│                                         │
│ [Cancel]              [Start Generation]│
└─────────────────────────────────────────┘
```

4. Click **Start Generation**

### Step 6: Monitor Progress

[Screenshot: Progress indicator with detailed status]

```
Generating Test Plan...

Overall Progress: ██████████████████░░░░ 70%
Elapsed: 12m 34s | Remaining: ~5m 26s

Current Phase: Critic Agent Analysis
━━━━━━━━━━━━━━━━━━━━░░░░ 85%

Completed Phases:
✓ Document Loading (23 seconds)
✓ Actor Agent 1 - Requirements (4m 15s)
  → Extracted 127 requirements
✓ Actor Agent 2 - Test Scenarios (5m 02s)
  → Generated 89 test scenarios
✓ Actor Agent 3 - Procedures (3m 47s)
  → Created 89 test procedures
▶ Critic Agent - Validation (in progress)
  → Reviewed 62/89 test cases
⏳ Contradiction Agent (pending)
⏳ Final Report Generation (pending)

[Cancel Generation]
```

**You can**:
- Minimize and work on other tasks
- Close browser (generation continues)
- View live agent outputs
- Cancel if needed

### Step 7: Review Results

When complete, results display in tabs:

[Screenshot: Results tabbed interface]

```
┌─────────────────────────────────────────┐
│ ✓ Generation Complete (Total: 18m 42s) │
├─────────────────────────────────────────┤
│ [Test Plan] [Test Cards] [Requirements] │
│ [Coverage] [Agent Outputs] [Issues]     │
└─────────────────────────────────────────┘
```

## Understanding the Results

### Test Plan Tab

[Screenshot: Test plan view]

Shows the complete generated test plan:

```markdown
# Test Plan: Technical_Spec_v2.pdf

## 1. Executive Summary
[AI-generated overview of testing scope and objectives]

## 2. Requirements Coverage
### 2.1 Functional Requirements
- REQ-001: User Authentication
  - Test Cases: TC-001, TC-002, TC-003
  - Priority: Critical
  - Status: To be tested

### 2.2 Non-Functional Requirements
[...]

## 3. Test Scenarios
### TS-001: User Login Flow
**Objective**: Verify user can authenticate successfully
**Prerequisites**:
- Test user account exists
- System is accessible
**Test Cases**: TC-001, TC-002, TC-003

[... continues with all scenarios ...]

## 4. Test Procedures
[Detailed step-by-step procedures]

## 5. Acceptance Criteria
[Pass/fail criteria for each test]
```

**Actions**:
- 📋 Copy to clipboard
- ⬇️ Download as Markdown
- ✏️ Edit inline
- 📊 View coverage matrix

### Test Cards Tab

[Screenshot: Test cards list]

Individual test cards ready for execution:

```
Test Card TC-001: User Login Success

Objective:
Verify that valid users can successfully authenticate

Prerequisites:
• Test environment is running
• Test user credentials available
• Database is populated with test data

Test Procedure:
Step 1: Navigate to login page
  Expected: Login form is displayed

Step 2: Enter valid username "testuser1"
  Expected: Username field accepts input

Step 3: Enter valid password "Test123!"
  Expected: Password field masked

Step 4: Click "Login" button
  Expected: User redirected to dashboard

Step 5: Verify user name displayed in header
  Expected: "Welcome, testuser1" shown

Pass Criteria:
☐ All steps completed successfully
☐ User successfully authenticated
☐ Dashboard loads within 2 seconds
☐ No error messages displayed

Fail Criteria:
☐ Any step fails
☐ Error message displayed
☐ Redirect does not occur
☐ Session not established

Test Data:
• Username: testuser1
• Password: Test123!

References:
• Requirement: REQ-AUTH-001 (page 23)
• Design: Architecture_Doc.pdf (section 4.2)
```

**Actions**:
- ⬇️ Export all as Word (.docx)
- ⬇️ Export individual cards
- ✏️ Edit test steps
- ✅ Mark as executed

### Requirements Matrix Tab

[Screenshot: Requirements traceability matrix]

CSV/Table showing requirement-to-test mapping:

| Req ID | Requirement | Source | Test Cases | Coverage | Priority |
|--------|-------------|--------|------------|----------|----------|
| REQ-001 | User Auth | p.23 | TC-001, TC-002 | 100% | Critical |
| REQ-002 | Data Encrypt | p.34 | TC-015, TC-016 | 100% | High |
| REQ-003 | Audit Log | p.45 | TC-028 | 50% | Medium |

**Coverage Metrics**:
```
Overall Coverage: 94%

By Priority:
• Critical: 100% (12/12 requirements)
• High:     96% (24/25 requirements)
• Medium:   85% (34/40 requirements)
• Low:      70% (14/20 requirements)

Untested Requirements: 6
• REQ-034: Data retention (Low priority)
• REQ-067: Print functionality (Low priority)
[...]
```

### Coverage Report Tab

Visual coverage analysis:

[Screenshot: Coverage charts and graphs]

- Pie chart: Requirements by priority
- Bar chart: Coverage by section
- Heatmap: Test density across document
- Gap analysis: Untested areas

### Agent Outputs Tab

See what each agent analyzed:

[Screenshot: Agent outputs with expandable sections]

```
▼ Actor Agent 1 - Requirements Extraction

Extracted 127 requirements from document:

Functional Requirements (87):
1. The system SHALL provide user authentication (page 23)
2. The system SHALL encrypt data at rest (page 34)
3. The system SHALL maintain audit logs (page 45)
[...]

Non-Functional Requirements (40):
1. Response time SHALL be < 2 seconds (page 67)
2. System SHALL support 1000 concurrent users (page 68)
[...]

▼ Actor Agent 2 - Test Scenario Generation
[...]

▼ Critic Agent - Validation Notes
[...]
```

**Useful for**:
- Understanding AI reasoning
- Debugging issues
- Learning from analysis
- Refining prompts

### Issues Tab

Problems and contradictions found:

[Screenshot: Issues list with severity indicators]

```
🔴 Critical Issues (2)

ISSUE-001: Contradictory Requirements
• REQ-023 (page 34): "System SHALL encrypt using AES-256"
• REQ-089 (page 78): "System SHALL use RSA-2048 encryption"
→ Recommendation: Clarify encryption algorithm or specify
  different algorithms for different data types

ISSUE-002: Missing Acceptance Criteria
• REQ-045 (page 56): "System SHALL be user-friendly"
→ Recommendation: Define measurable usability criteria


🟡 Warnings (5)

WARN-001: Ambiguous Requirement
• REQ-067 (page 71): "System SHALL respond quickly"
→ Recommendation: Specify numeric response time requirement

WARN-002: Incomplete Specification
• Section 4.3 mentions "backup procedures" but provides no details
→ Recommendation: Add backup requirements specification


🔵 Informational (8)

INFO-001: Coverage Gap
• Section 7 (Monitoring) has no testable requirements
→ Recommendation: Consider if monitoring needs test coverage
```

## Customizing Generation

### Custom Agents

Create specialized agents for your domain:

1. Go to **Agent & Orchestration Manager**
2. Click **Create Agent**
3. Configure:

```
Agent Name: Security Requirements Analyst

Role: Identify all security-related requirements and
      generate security-focused test cases

Prompt Template:
"""
Analyze the provided document focusing on security requirements.

Extract:
1. Authentication requirements
2. Authorization requirements
3. Data protection requirements
4. Security testing requirements

For each requirement, generate:
- Positive test cases (valid security scenarios)
- Negative test cases (attack scenarios)
- Boundary test cases (edge cases)

Format as structured test procedures.
"""

Model: gpt-4o
Temperature: 0.2
```

4. Save agent
5. Add to Document Generator agent configuration

See [Agent Manager](09-agent-manager.md) for full details.

### Agent Sets

Pre-configured agent groups for common scenarios:

```
Available Agent Sets:

• Standard Test Generation (default)
  └─ Balanced approach for most documents

• Security-Focused Analysis
  └─ Emphasizes security testing

• Performance Testing Focus
  └─ Generates performance test scenarios

• Compliance Validation
  └─ Maps requirements to compliance standards

• API Testing
  └─ Specialized for API specifications

[Create Custom Agent Set]
```

**Use Agent Set**:
1. In Document Generator configuration
2. Select **Agent Set**: [Security-Focused Analysis ▼]
3. Agents automatically configured

### Output Templates

Customize output formatting:

```
Output Template: [Standard Test Plan ▼]

Available Templates:
• Standard Test Plan (Markdown)
• IEEE 829 Format
• MIL-STD-498 Format
• Agile Test Plan
• Custom Template

[Edit Template] [Create New]
```

**Template Variables**:
- `{document_name}` - Source document
- `{generation_date}` - When generated
- `{requirements_count}` - Number of requirements
- `{test_count}` - Number of test cases
- Custom fields

## Advanced Features

### Iterative Refinement

Improve results through multiple passes:

1. Review initial generation
2. Click **🔄 Refine Results**
3. Provide feedback:

```
Refinement Instructions:

☑ Increase test coverage for Section 4.2
☑ Add more negative test cases
☑ Focus on edge cases for authentication
☐ Generate performance test scenarios

Additional Notes:
[Pay special attention to the data validation
requirements on pages 45-52. The current test cases
don't cover all boundary conditions mentioned.]

[Start Refinement]
```

4. Agents re-analyze with your guidance
5. Updated results merge with original

### Comparative Analysis

Compare multiple document versions:

```
Compare Documents:
Base: Technical_Spec_v1.0.pdf
Compare: Technical_Spec_v2.0.pdf

Analysis Type:
☑ New requirements
☑ Modified requirements
☑ Removed requirements
☑ Impact on existing tests
☑ Generate new test cases for changes

[Start Comparison]
```

**Output Shows**:
- What changed between versions
- Which tests need updates
- New tests needed
- Obsolete tests

### Batch Processing

Generate test plans for multiple documents:

```
Batch Document Processing

Selected Documents:
☑ Module_A_Spec.pdf
☑ Module_B_Spec.pdf
☑ Module_C_Spec.pdf
☑ Integration_Spec.pdf

Processing Mode:
● Sequential (one at a time)
○ Parallel (all at once - faster but resource intensive)

[Start Batch Processing]
```

**Useful for**:
- Processing entire project documentation
- Consistent test plan generation
- Bulk updates

## Best Practices

### Document Preparation

For best results, ensure documents have:

✅ **Clear structure**: Sections, headers, numbering
✅ **Explicit requirements**: Use "SHALL", "MUST", "SHOULD"
✅ **Consistent formatting**: Similar sections formatted similarly
✅ **Good quality**: Text is readable, not scanned poorly
✅ **Complete information**: No "TBD" or major gaps

❌ **Avoid**:
- Mixed formatting styles
- Scanned documents with OCR errors
- Incomplete specifications
- Ambiguous language
- Missing sections

### Model Selection

Choose model based on document:

**Simple Documents** (< 50 pages, clear requirements):
- `gpt-4o-mini` (faster, cheaper)
- `llama3.1:8b` (local, good quality)

**Complex Documents** (> 50 pages, intricate requirements):
- `gpt-4o` (best quality)
- `gpt-5` (if available, cutting edge)

**Security/Compliance Documents**:
- `gpt-4o` with low temperature (0.2-0.3)
- Use specialized security agent set

### Temperature Settings

- **0.0-0.3**: Deterministic, strict requirement extraction
- **0.4-0.6**: Balanced (recommended for most cases)
- **0.7-1.0**: Creative test scenario generation

**Recommended**: 0.3 for requirement extraction, 0.6 for test generation

### Review and Validation

**Always review AI-generated content**:

1. ✓ Verify requirements accurately extracted
2. ✓ Check test procedures make sense
3. ✓ Ensure coverage is adequate
4. ✓ Validate references to source documents
5. ✓ Review contradiction findings
6. ✓ Test a few procedures manually

**AI is a tool, not a replacement for human expertise!**

## Troubleshooting

### Generation Fails

**Problem**: Generation stops with error

**Solutions**:
- Check agent logs in Agent Outputs tab
- Verify model is accessible (OpenAI API key valid, Ollama running)
- Try simpler analysis (Quick instead of Deep)
- Reduce document size
- Check disk space and memory

### Poor Quality Results

**Problem**: Generated test plan is inadequate

**Solutions**:
- Use better model (gpt-4o instead of gpt-4o-mini)
- Increase temperature slightly (0.7 instead of 0.3)
- Try Deep Analysis instead of Quick
- Add custom agent for your domain
- Improve source document quality
- Use Iterative Refinement

### Slow Generation

**Problem**: Takes much longer than estimated

**Solutions**:
- Use faster model (gpt-4o-mini, llama3.2:3b)
- Reduce number of agents
- Use Quick Analysis
- For Ollama: ensure GPU is enabled
- Check system resources (CPU, RAM)

### Contradictions Not Found

**Problem**: Contradiction Agent finds nothing but you know there are issues

**Solutions**:
- Rerun with just Contradiction Agent focused
- Increase temperature to 0.7
- Provide examples of contradictions you see
- Use Iterative Refinement with specific guidance

## Export Options

### Export Test Plan

```
Format: [Markdown (.md) ▼]
Options:
☑ Include table of contents
☑ Include agent analysis
☑ Include coverage metrics
☐ Include full document text

[Download]
```

### Export Test Cards

```
Format: [Microsoft Word (.docx) ▼]

Output Style:
● One file with all test cards
○ Separate file per test card
○ Excel spreadsheet format

Template: [Standard Test Card ▼]

[Export All] [Export Selected]
```

### Export Requirements Matrix

```
Format: [CSV ▼]
Columns:
☑ Requirement ID
☑ Requirement Text
☑ Source Page
☑ Test Cases
☑ Coverage %
☑ Priority
☑ Status

[Download]
```

## Next Steps

- **[Test Card Viewer](08-test-card-viewer.md)** - View and execute test cards
- **[Multi-Agent Analysis](07-multi-agent-analysis.md)** - Understand how agents work
- **[Agent Manager](09-agent-manager.md)** - Create custom agents

---

**Need help?** See [Troubleshooting Guide](12-troubleshooting.md) or [FAQ](13-faq.md)
