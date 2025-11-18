# User Interface Overview

This guide provides a comprehensive overview of the DIS Verification GenAI user interface, helping you navigate and understand all interface components.

## Table of Contents

1. [Interface Layout](#interface-layout)
2. [Sidebar Components](#sidebar-components)
3. [Main Content Area](#main-content-area)
4. [Navigation](#navigation)
5. [Common UI Patterns](#common-ui-patterns)
6. [Keyboard Shortcuts](#keyboard-shortcuts)
7. [Responsive Design](#responsive-design)

## Interface Layout

The application uses a consistent layout across all modes:

[Screenshot: Full interface with labeled sections]

```
┌──────────────────────────────────────────────────────────┐
│  DIS Verification GenAI - v1.0.7          [Health Status]│
├─────────────┬────────────────────────────────────────────┤
│             │                                            │
│   Sidebar   │         Main Content Area                  │
│             │                                            │
│  • Mode     │    (Changes based on selected mode)        │
│  • Model    │                                            │
│  • Health   │                                            │
│  • Session  │                                            │
│             │                                            │
│             │                                            │
│             │                                            │
│             │                                            │
├─────────────┴────────────────────────────────────────────┤
│  Footer: Version | Documentation | GitHub                │
└──────────────────────────────────────────────────────────┘
```

## Sidebar Components

The left sidebar provides access to all key controls and settings.

### 1. Mode Selection

[Screenshot: Mode selection dropdown expanded]

**Location**: Top of sidebar
**Purpose**: Switch between different application modes

**Available Modes**:

```
🗨️ Direct Chat
   Interactive chat with AI models

🤖 AI Agent Simulation
   Run specialized agents on documents

⚙️ Agent & Orchestration Manager
   Create and manage custom AI agents

📄 Document Generator
   Generate test plans from documents

📋 Test Card Viewer
   View and export test cards
```

**How to Use**:
1. Click the **Mode** dropdown
2. Select your desired mode
3. The main content area updates immediately

**Tips**:
- Mode selection persists across sessions
- Each mode has distinct features and layout
- Health checks remain visible in all modes

### 2. Model Selection

[Screenshot: Model dropdown showing OpenAI and Ollama options]

**Location**: Below mode selection
**Purpose**: Choose which AI model to use

**OpenAI Models** (requires API key):
```
GPT-5 Series:
├─ gpt-5.1          [Most Advanced]
├─ gpt-5
├─ gpt-5-mini
└─ gpt-5-nano       [Fastest]

GPT-4 Series:
├─ gpt-4.1
├─ gpt-4
├─ gpt-4o           [Recommended]
├─ gpt-4o-mini      [Cost-Effective]
└─ gpt-4-turbo

GPT-3.5:
└─ gpt-3.5-turbo    [Legacy]

Reasoning Models:
├─ o1
├─ o1-mini
└─ o3-mini
```

**Ollama Models** (local, US-based):
```
Meta (California):
├─ llama3.1:8b      [Recommended]
├─ llama3.2:3b
└─ llama3.2:1b

Microsoft (Washington):
└─ phi3:mini

Embeddings:
└─ snowflake-arctic-embed:latest
```

**Model Indicator**:
- 🌐 = Cloud model (OpenAI)
- 🏠 = Local model (Ollama)
- ⚡ = Fast response
- 🎯 = High accuracy
- 💰 = Cost-effective

**Tips**:
- Model changes take effect immediately
- Local models require Ollama installation
- Each model has different speed/quality tradeoffs
- See [Model Selection Guide](11-model-selection.md) for detailed comparison

### 3. Health Monitoring

[Screenshot: Health status panel showing all services]

**Location**: Middle of sidebar
**Purpose**: Real-time system health monitoring

**Monitored Services**:

```
🟢 FastAPI Backend
   Status: Healthy
   Response: 45ms

🟢 PostgreSQL Database
   Status: Healthy
   Connections: 12/100

🟢 ChromaDB Vector Store
   Status: Healthy
   Collections: 5

🟢 Redis Cache
   Status: Healthy
   Memory: 45MB/2GB

🟢 Celery Worker
   Status: Healthy
   Tasks: 3 queued
```

**Status Indicators**:
- 🟢 **Healthy** - Service operating normally
- 🟡 **Degraded** - Service slow or struggling
- 🔴 **Unhealthy** - Service unavailable
- ⚪ **Unknown** - Cannot determine status

**What to Do When Unhealthy**:
1. Check the specific service logs
2. Restart the service: `docker compose restart <service>`
3. See [Troubleshooting Guide](12-troubleshooting.md)

**Auto-Refresh**: Updates every 30 seconds automatically

### 4. Session Information

[Screenshot: Session panel showing current session details]

**Location**: Below health monitoring
**Purpose**: Track current work session

**Displayed Information**:
```
Session ID: abc123def456
Started: 2025-11-18 14:30:22
Duration: 45 minutes
Messages: 23
Model: gpt-4o
```

**Session Features**:
- **Auto-save**: All conversations saved automatically
- **Session History**: Access past sessions from Database Manager
- **Export**: Download session data as JSON
- **Clear**: Start a new session (doesn't delete history)

### 5. Settings & Configuration

[Screenshot: Settings expanded panel]

**Location**: Bottom of sidebar
**Purpose**: Adjust application settings

**Available Settings**:

**Temperature** (AI Creativity):
```
[────────●─────────────] 0.7
0.0                    2.0
Precise              Creative
```
- **0.0-0.3**: Deterministic, factual responses
- **0.4-0.7**: Balanced (default: 0.7)
- **0.8-1.5**: Creative, varied responses
- **1.6-2.0**: Very creative, unpredictable

**Max Tokens** (Response Length):
```
[────────●─────────────] 2000
100                   4000
Short                 Long
```
- **100-500**: Brief answers
- **500-2000**: Standard responses (default)
- **2000-4000**: Detailed explanations

**RAG Settings** (when using document chat):
- **Number of Results**: How many document chunks to retrieve (1-10)
- **Score Threshold**: Minimum relevance score (0.0-1.0)
- **Include Metadata**: Show document sources

**Advanced**:
- **Enable Streaming**: Show responses as they generate
- **Show Token Count**: Display usage statistics
- **Enable Citations**: Include source references
- **Debug Mode**: Show detailed logs

## Main Content Area

The main content area changes based on the selected mode. Here are common components:

### Chat Interface (Direct Chat Mode)

[Screenshot: Chat interface with messages]

**Components**:

1. **Message History**
   ```
   ┌─────────────────────────────────────┐
   │ You: What is this document about?   │
   │ 14:23                               │
   └─────────────────────────────────────┘

   ┌─────────────────────────────────────┐
   │ AI: This document describes...      │
   │ 14:23 | gpt-4o | 234 tokens         │
   │                                     │
   │ Sources:                            │
   │ • doc.pdf (page 3, score: 0.89)    │
   └─────────────────────────────────────┘
   ```

2. **Input Box**
   - Bottom of screen
   - Expandable (shift+enter for new line)
   - Character counter
   - Send button (or press Enter)

3. **Message Actions**
   - 📋 Copy message
   - 🔄 Regenerate response
   - 👍/👎 Rate response
   - 📎 View sources

### Document Generator (Test Plan Mode)

[Screenshot: Document generator interface]

**Components**:

1. **Document Selection**
   ```
   Select Document:  [Dropdown: Available Documents ▼]

   Document Preview:
   ├─ Filename: Technical_Spec_v2.pdf
   ├─ Pages: 87
   ├─ Size: 4.2 MB
   ├─ Uploaded: 2025-11-18 13:45
   └─ Status: Processed ✓
   ```

2. **Generation Options**
   ```
   Analysis Type:
   ○ Quick Analysis (5-10 min)
   ● Standard Analysis (15-30 min)
   ○ Deep Analysis (30-60 min)

   Agent Configuration:
   ☑ Actor Agent 1 (Requirements Extraction)
   ☑ Actor Agent 2 (Test Case Generation)
   ☑ Critic Agent (Validation)
   ☑ Contradiction Agent (Conflict Detection)

   Output Format:
   ☑ Test Plan (Markdown)
   ☑ Test Cards (Word)
   ☑ Requirements Matrix (CSV)
   ```

3. **Progress Indicator**
   ```
   Generating Test Plan...

   ██████████████████░░░░ 70%

   Current Phase: Critic Agent Analysis
   Elapsed: 12m 34s
   Estimated Remaining: 5m 26s

   Completed:
   ✓ Document Processing
   ✓ Actor Agent 1 Analysis
   ✓ Actor Agent 2 Analysis
   ▶ Critic Agent Analysis (In Progress)
   ⏳ Contradiction Detection (Pending)
   ⏳ Final Report Generation (Pending)
   ```

4. **Results Display**
   - Tabbed interface for different outputs
   - Download buttons
   - Preview pane
   - Edit capabilities

### File Upload Component

[Screenshot: File upload interface]

**Used In**: Document Management, Document Generator

**Features**:
```
┌──────────────────────────────────────────┐
│  Drag and drop files here                │
│  or click to browse                      │
│                                          │
│  Supported formats:                      │
│  • PDF (.pdf)                           │
│  • Word (.docx)                         │
│  • Text (.txt)                          │
│                                          │
│  Maximum size: 100 MB                    │
└──────────────────────────────────────────┘

Uploading: Technical_Spec.pdf
██████████████████░░░░ 75% (3.1 MB / 4.2 MB)

Processing...
✓ File validation
✓ Text extraction
▶ Image extraction (12/45 images)
⏳ Vector embedding
⏳ Database storage
```

**Upload States**:
- ⬆️ Uploading (with progress bar)
- 🔄 Processing (extracting text, images)
- ⚙️ Embedding (creating vectors)
- ✅ Complete
- ❌ Error (with reason)

### Data Tables

[Screenshot: Database manager table view]

**Used In**: Database Manager, Session History

**Features**:
```
┌────┬──────────┬────────────┬──────────┬─────────┐
│ ID │ Name     │ Date       │ Size     │ Actions │
├────┼──────────┼────────────┼──────────┼─────────┤
│ 1  │ Doc1.pdf │ 2025-11-18 │ 4.2 MB   │ ⋮ ⋯ 🗑  │
│ 2  │ Doc2.pdf │ 2025-11-17 │ 2.1 MB   │ ⋮ ⋯ 🗑  │
└────┴──────────┴────────────┴──────────┴─────────┘

Showing 2 of 45 entries
[◀ Previous] [1] [2] [3] ... [9] [Next ▶]
```

**Table Features**:
- **Sortable Columns**: Click headers to sort
- **Filtering**: Search box above table
- **Pagination**: Navigate large datasets
- **Bulk Actions**: Select multiple rows
- **Row Actions**:
  - ⋮ View details
  - ⋯ Edit
  - 🗑 Delete
  - ⬇️ Download
  - 📋 Copy

## Navigation

### Primary Navigation

**Mode Switching**:
1. Use sidebar Mode dropdown
2. Click directly on mode name
3. Keyboard: `Alt + 1-5` (mode numbers)

**Page Navigation**:
- Use browser back/forward (maintains state)
- Sidebar links remain accessible
- Session persists across navigation

### Breadcrumb Navigation

[Screenshot: Breadcrumb trail]

In some modes, you'll see breadcrumbs:
```
Home > Document Generator > Technical_Spec.pdf > Results
```

Click any level to navigate back.

### Quick Access Menu

[Screenshot: Quick access toolbar]

**Location**: Top right corner

```
[🔍 Search] [📁 Files] [⚙️ Settings] [❓ Help]
```

- **🔍 Search**: Global search (Ctrl+K)
- **📁 Files**: Quick file picker
- **⚙️ Settings**: Application settings
- **❓ Help**: Context-sensitive help

## Common UI Patterns

### Confirmation Dialogs

[Screenshot: Confirmation dialog]

**Before Destructive Actions**:
```
┌────────────────────────────────────┐
│  Delete Document?                  │
│                                    │
│  Are you sure you want to delete   │
│  "Technical_Spec.pdf"?             │
│                                    │
│  This action cannot be undone.     │
│                                    │
│  [Cancel]         [Delete]         │
└────────────────────────────────────┘
```

### Toast Notifications

[Screenshot: Toast notification examples]

**Success**:
```
✓ Document uploaded successfully
```

**Warning**:
```
⚠ Service degraded - responses may be slow
```

**Error**:
```
✗ Failed to connect to database
  [View Details] [Retry]
```

**Info**:
```
ℹ Processing will take approximately 15 minutes
```

**Location**: Top right, auto-dismiss after 5 seconds

### Loading States

**Spinner** (short tasks):
```
⌛ Loading...
```

**Progress Bar** (long tasks):
```
Processing Document...
██████████░░░░░░░░░░ 50%
```

**Skeleton Screens** (page loads):
```
████████░░░░░░░░
████░░░░░░░░░░░░
```

### Form Validation

**Real-time Validation**:
```
Email Address *
[user@example.com          ]
✓ Valid email address

API Key *
[sk-123                    ]
✗ API key must start with 'sk-' and be 48 characters
```

**Required Fields**: Marked with asterisk (*)
**Optional Fields**: Marked with (optional)

### Expandable Sections

**Collapsible Panels**:
```
▼ Advanced Settings
  ├─ Temperature: 0.7
  ├─ Max Tokens: 2000
  └─ Enable Streaming: Yes

▶ Debug Information
  (Click to expand)
```

Click the arrow (▼/▶) to toggle.

## Keyboard Shortcuts

### Global Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + K` (⌘K on Mac) | Global search |
| `Ctrl + /` | Show keyboard shortcuts |
| `Esc` | Close modal/dialog |
| `F5` | Refresh page |
| `Ctrl + Shift + R` | Hard refresh (clear cache) |

### Chat Interface

| Shortcut | Action |
|----------|--------|
| `Enter` | Send message |
| `Shift + Enter` | New line in message |
| `Ctrl + L` | Clear chat history |
| `↑` | Edit last message |
| `Ctrl + C` | Copy last AI response |

### Document Generator

| Shortcut | Action |
|----------|--------|
| `Ctrl + G` | Start generation |
| `Ctrl + S` | Save draft |
| `Ctrl + E` | Export results |
| `Esc` | Cancel generation |

### Navigation

| Shortcut | Action |
|----------|--------|
| `Alt + 1` | Direct Chat mode |
| `Alt + 2` | AI Agent Simulation |
| `Alt + 3` | Agent Manager |
| `Alt + 4` | Document Generator |
| `Alt + 5` | Test Card Viewer |
| `Ctrl + H` | Home page |

### Accessibility

| Shortcut | Action |
|----------|--------|
| `Tab` | Next interactive element |
| `Shift + Tab` | Previous interactive element |
| `Space` | Activate button/checkbox |
| `Ctrl + +` | Increase font size |
| `Ctrl + -` | Decrease font size |
| `Ctrl + 0` | Reset font size |

**Screen Reader Support**: Full ARIA labels and semantic HTML

## Responsive Design

The interface adapts to different screen sizes:

### Desktop (1920x1080+)
- Full sidebar visible
- Multi-column layouts
- All features accessible

[Screenshot: Desktop view]

### Laptop (1366x768)
- Collapsible sidebar
- Single column layouts
- Optimized spacing

[Screenshot: Laptop view]

### Tablet (768x1024)
- Hamburger menu for sidebar
- Touch-optimized buttons
- Responsive tables

[Screenshot: Tablet view]

### Mobile (< 768px)
**Limited Support**: Core features accessible but optimized for desktop use

## Customization

### Theme

**Light Theme** (default):
```
Background: White
Text: Dark gray
Accents: Blue
```

**Dark Theme** (coming soon):
```
Background: Dark gray
Text: Light gray
Accents: Blue
```

**Change Theme**: Settings > Appearance > Theme

### Layout Density

**Comfortable** (default):
- Standard spacing
- Larger touch targets

**Compact**:
- Reduced spacing
- More content visible

**Change Density**: Settings > Appearance > Density

### Font Size

**Adjustable Sizes**:
- Small (12px)
- Medium (14px) - default
- Large (16px)
- Extra Large (18px)

**Change Size**: Settings > Appearance > Font Size
Or use: `Ctrl + +/-`

## Tips for Efficient Navigation

1. **Learn Keyboard Shortcuts**: Saves significant time
2. **Use Quick Access Menu**: Fastest way to common tasks
3. **Pin Frequently Used Documents**: In File Manager
4. **Customize Sidebar**: Hide unused sections
5. **Use Search**: `Ctrl+K` finds anything quickly
6. **Bookmark Important Views**: Browser bookmarks work well
7. **Multi-Tab Workflow**: Open different modes in separate tabs

## Accessibility Features

- ♿ **Screen Reader Compatible**: Full ARIA support
- 🎨 **High Contrast Mode**: For visual impairments
- ⌨️ **Keyboard Navigation**: Full app accessible without mouse
- 🔤 **Adjustable Text**: Increase font size up to 18px
- 🎯 **Focus Indicators**: Clear visual focus states
- 📱 **Touch Support**: Large touch targets for tablets

## Next Steps

Now that you understand the interface:

- **[Direct Chat Mode](04-direct-chat.md)** - Learn interactive chat
- **[Document Management](05-document-management.md)** - Upload and organize documents
- **[Document Generator](06-document-generator.md)** - Generate test plans

---

**Questions about the interface?** Check the [FAQ](13-faq.md) or [Troubleshooting Guide](12-troubleshooting.md).
