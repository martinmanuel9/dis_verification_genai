# Test Card Viewer

View, edit, and export individual test cards for manual test execution.

## Overview

Test Card Viewer provides an interface to:
- View generated test cards
- Edit test procedures
- Mark test execution status
- Export to Word documents
- Track test results

[Screenshot: Test Card Viewer interface]

## Accessing Test Cards

### From Document Generator

After generating a test plan:
1. Click **Test Cards** tab in results
2. See list of all generated test cards
3. Click any card to view/edit

### From Test Card Viewer Mode

1. Select Mode: **📋 Test Card Viewer**
2. Choose test plan from dropdown
3. Browse all test cards

## Test Card Structure

Each test card contains:

```
┌──────────────────────────────────────┐
│ TC-001: User Login Success           │
├──────────────────────────────────────┤
│ Status: [Not Started ▼]              │
│ Priority: Critical                   │
│ Requirement: REQ-AUTH-001            │
│                                      │
│ OBJECTIVE:                           │
│ Verify valid users can authenticate  │
│                                      │
│ PREREQUISITES:                       │
│ • System running                     │
│ • Test user exists                   │
│                                      │
│ TEST PROCEDURE:                      │
│ 1. Navigate to login page            │
│ 2. Enter username "testuser1"        │
│ 3. Enter password "Test123!"         │
│ 4. Click Login button                │
│ 5. Verify dashboard loads            │
│                                      │
│ EXPECTED RESULTS:                    │
│ • Login successful                   │
│ • Dashboard displayed                │
│ • No errors shown                    │
│                                      │
│ PASS CRITERIA:                       │
│ ☐ All steps completed                │
│ ☐ Dashboard loads < 2s               │
│                                      │
│ TEST DATA:                           │
│ Username: testuser1                  │
│ Password: Test123!                   │
│                                      │
│ REFERENCES:                          │
│ • Spec: Technical_Spec.pdf (p.23)    │
│                                      │
│ [Edit] [Execute] [Export] [Delete]  │
└──────────────────────────────────────┘
```

## Editing Test Cards

### Edit Mode

1. Click **✏️ Edit** on test card
2. Modify any section
3. Click **💾 Save** when done

[Screenshot: Test card in edit mode]

**Editable Sections**:
- Objective
- Prerequisites  
- Test steps
- Expected results
- Pass/fail criteria
- Test data
- Notes

### Add Test Steps

```
TEST PROCEDURE:
1. Navigate to login page
2. Enter username "testuser1"
   [+ Add Step Below]
3. Enter password "Test123!"
```

Click **+ Add Step Below** to insert new steps.

### Reorder Steps

Drag steps to reorder:

```
TEST PROCEDURE:
☰ 1. Navigate to login page
☰ 2. Enter username
☰ 3. Enter password
```

Grab the ☰ handle and drag.

### Delete Steps

Click **✕** next to step to remove.

## Executing Tests

### Mark Execution Status

```
Status: [Not Started ▼]

Options:
• Not Started
• In Progress
• Passed
• Failed
• Blocked
• Skipped
```

### Record Results

During execution, check off criteria:

```
PASS CRITERIA:
☑ All steps completed
☑ Dashboard loads < 2s
☑ No error messages

FAIL CRITERIA:
☐ Any step fails
☐ Timeout occurs
```

### Add Execution Notes

```
EXECUTION NOTES:

Date: 2025-11-18
Tester: John Doe
Environment: Test Lab 3

Results:
Step 1: ✓ Passed
Step 2: ✓ Passed
Step 3: ✓ Passed
Step 4: ✓ Passed - Loaded in 1.2s
Step 5: ✓ Passed

Overall: PASSED
```

### Attach Evidence

Upload screenshots or logs:

```
EVIDENCE:
📎 login_success.png (245 KB)
📎 browser_console.log (12 KB)

[+ Attach File]
```

## Export Options

### Export Single Card

```
Export Test Card: TC-001

Format: [Word (.docx) ▼]

Template: [Standard Test Card ▼]

☑ Include execution notes
☑ Include attachments
☐ Include requirement details

[Export]
```

### Export Multiple Cards

1. Select test cards (checkboxes)
2. Click **Export Selected**
3. Choose format and template
4. Download ZIP file

### Export All Cards

```
Export All Test Cards

Format: [Word (.docx) ▼]

Output:
● Single document (all cards)
○ Separate files (one per card)
○ Excel spreadsheet

[Export All]
```

## Organizing Test Cards

### Filter Test Cards

```
Filter By:
☑ Priority: [Critical ▼]
☑ Status: [Not Started ▼]
☐ Requirement: [All ▼]
☐ Tester: [All ▼]

Showing 12 of 89 test cards
```

### Sort Test Cards

Click column headers:
- ID (TC-001, TC-002...)
- Priority (Critical → Low)
- Status (Not Started → Passed)
- Requirement (REQ-001...)

### Group Test Cards

```
Group By: [Requirement ▼]

REQ-AUTH-001: Authentication (5 cards)
├─ TC-001: User Login Success
├─ TC-002: Invalid Password
├─ TC-003: Account Lockout
├─ TC-004: Password Reset
└─ TC-005: Session Timeout

REQ-DATA-001: Data Validation (3 cards)
├─ TC-006: Valid Input
├─ TC-007: Invalid Input
└─ TC-008: Boundary Values
```

## Test Execution Tracking

### Execution Dashboard

[Screenshot: Test execution dashboard]

```
Test Execution Summary

Total Test Cards: 89
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Status Breakdown:
Passed:       45 (51%) ████████████░░░░░░░░░░░░
Failed:        8  (9%) ██░░░░░░░░░░░░░░░░░░░░░░
Blocked:       4  (4%) █░░░░░░░░░░░░░░░░░░░░░░░
In Progress:  12 (13%) ███░░░░░░░░░░░░░░░░░░░░░
Not Started:  20 (23%) █████░░░░░░░░░░░░░░░░░░░

By Priority:
Critical: 12/12 (100%) ████████████
High:     18/25  (72%) ████████░░░░
Medium:   15/40  (38%) ████░░░░░░░░
Low:       0/12   (0%) ░░░░░░░░░░░░

Overall Progress: 51%
```

### Assign Testers

```
Assign Test Cards

Select Cards: [12 selected]
Assign To: [John Doe ▼]

[Assign]
```

### Set Due Dates

```
TC-001: User Login Success
Due Date: [2025-11-25 ▼]
Priority: Critical
Assigned: John Doe
```

## Templates

### Test Card Templates

Create reusable templates:

```
Template: Standard Security Test

OBJECTIVE:
Verify [feature] security controls

PREREQUISITES:
• Security tools configured
• Test accounts available
• Logging enabled

TEST PROCEDURE:
1. [Positive test]
2. [Negative test - injection]
3. [Negative test - bypass]
4. [Boundary test]
5. [Verify logging]

PASS CRITERIA:
☐ Positive test succeeds
☐ Negative tests blocked
☐ Events logged correctly
```

### Apply Template

1. Create new test card
2. Click **Use Template**
3. Select template
4. Fill in placeholders

## Integration Features

### Link to Requirements

```
REQUIREMENTS COVERAGE:
• REQ-AUTH-001 (Primary)
• REQ-AUDIT-005 (Secondary)
• REQ-PERF-002 (Non-functional)

[View Requirement] [Add Requirement]
```

### Link Test Cards

```
RELATED TESTS:
• TC-002: Invalid Login (prerequisite)
• TC-005: Session Management (follows)

[Add Related Test]
```

### Export to Test Management Tools

```
Export To: [Jira ▼]

Options:
• TestRail
• Jira
• Azure DevOps
• qTest
• Excel/CSV

[Configure] [Export]
```

## Best Practices

### Writing Test Steps

✅ **Good Steps**:
```
1. Click the "Save" button in the top-right corner
2. Verify the success message "Data saved successfully" appears
3. Confirm the timestamp updates to current time
```

❌ **Bad Steps**:
```
1. Save
2. Check it worked
3. Look at stuff
```

### Pass/Fail Criteria

Be specific and measurable:

✅ **Good Criteria**:
```
☐ Response time < 2 seconds
☐ All required fields populated
☐ Error logged with severity "WARN"
```

❌ **Bad Criteria**:
```
☐ It works
☐ Looks good
☐ No problems
```

### Test Data

Provide exact values:

✅ **Good Test Data**:
```
Username: testuser1@example.com
Password: SecureP@ss123
Expected Role: Administrator
Expected Permissions: [Read, Write, Delete]
```

❌ **Bad Test Data**:
```
Username: valid username
Password: correct password
```

## Next Steps

- **[Document Generator](06-document-generator.md)** - Generate test cards
- **[Multi-Agent Analysis](07-multi-agent-analysis.md)** - Improve test quality

---

See [FAQ](13-faq.md) for test card questions
