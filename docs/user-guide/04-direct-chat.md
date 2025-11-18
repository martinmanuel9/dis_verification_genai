# Direct Chat Mode

Direct Chat Mode provides an interactive conversation interface where you can chat with AI models about your documents or general topics.

## Table of Contents

1. [Overview](#overview)
2. [Getting Started with Direct Chat](#getting-started-with-direct-chat)
3. [Chat Without Documents](#chat-without-documents)
4. [RAG-Enhanced Chat](#rag-enhanced-chat-with-documents)
5. [Advanced Features](#advanced-features)
6. [Best Practices](#best-practices)
7. [Common Use Cases](#common-use-cases)
8. [Troubleshooting](#troubleshooting)

## Overview

Direct Chat Mode allows you to:

- **Chat with AI models** using OpenAI GPT or local Ollama models
- **Ask questions about documents** using RAG (Retrieval Augmented Generation)
- **Get cited responses** with sources from your document collection
- **Save conversation history** for future reference
- **Switch models** mid-conversation
- **Export chat transcripts** for documentation

[Screenshot: Direct Chat interface overview]

## Getting Started with Direct Chat

### Step 1: Select Direct Chat Mode

1. Open the application (`http://localhost:8501`)
2. In the sidebar, locate **Mode Selection**
3. Select **🗨️ Direct Chat**

[Screenshot: Mode selection with Direct Chat highlighted]

The main content area will change to show the chat interface.

### Step 2: Choose Your AI Model

1. In the sidebar, find **Model Selection**
2. Choose from:
   - **OpenAI Models**: gpt-4o (recommended), gpt-5, etc.
   - **Ollama Models**: llama3.1:8b (recommended), phi3:mini, etc.

[Screenshot: Model selector showing available models]

**Model Recommendations**:
- **Best Quality**: `gpt-4o` (OpenAI)
- **Best Local**: `llama3.1:8b` (Ollama)
- **Fastest**: `gpt-4o-mini` (OpenAI)
- **Most Private**: Any Ollama model (runs locally)

See [Model Selection Guide](11-model-selection.md) for detailed comparisons.

### Step 3: Configure Chat Settings (Optional)

In the sidebar, expand **Settings**:

**Temperature** (Creativity):
```
[────────●─────────────] 0.7
0.0                    2.0
```
- **Low (0.0-0.3)**: Factual, deterministic responses
- **Medium (0.4-0.8)**: Balanced (default: 0.7)
- **High (0.9-2.0)**: Creative, varied responses

**Max Tokens** (Response Length):
```
[────────●─────────────] 2000
100                   4000
```
- Controls maximum response length
- Higher = longer, more detailed responses

### Step 4: Start Chatting

Simply type your message in the input box at the bottom and press Enter or click Send.

[Screenshot: Chat input box with example message]

## Chat Without Documents

Use Direct Chat for general questions without document context.

### Example Conversations

**Example 1: General Knowledge**

[Screenshot: General knowledge chat]

```
You: What are the key principles of test-driven development?

AI: Test-driven development (TDD) follows these core principles:

1. Write Tests First: Create test cases before implementing features
2. Red-Green-Refactor Cycle:
   • Red: Write a failing test
   • Green: Write minimal code to pass
   • Refactor: Improve code while keeping tests passing
3. Small Iterations: Make incremental changes
4. Continuous Testing: Run tests frequently
5. Design Through Testing: Let tests guide architecture

Benefits include better code quality, clearer requirements,
and easier refactoring.
```

**Example 2: Technical Assistance**

```
You: How do I configure Docker Compose for multi-stage builds?

AI: To use multi-stage builds in Docker Compose:

1. Create a Dockerfile with multiple FROM statements:

```dockerfile
# Build stage
FROM node:18 AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Production stage
FROM node:18-alpine
WORKDIR /app
COPY --from=builder /app/dist ./dist
CMD ["node", "dist/index.js"]
```

2. Reference in docker-compose.yml:

```yaml
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
      target: builder  # Optional: specify stage
    ports:
      - "3000:3000"
```

This creates smaller production images while keeping build dependencies separate.
```

**Example 3: Code Review**

```
You: Can you review this Python function for potential issues?

def process_users(users):
    result = []
    for user in users:
        if user['active']:
            result.append(user['name'].upper())
    return result

AI: Here are potential issues with this function:

1. **No Input Validation**: Missing checks for:
   • users being None or not a list
   • Missing 'active' or 'name' keys

2. **Unsafe Dictionary Access**: Will raise KeyError if keys missing
   • Use .get() method with defaults

3. **No Type Hints**: Function signature unclear

4. **Inefficient**: List comprehension would be more Pythonic

**Improved Version**:

```python
def process_users(users: list[dict]) -> list[str]:
    """
    Extract uppercase names of active users.

    Args:
        users: List of user dictionaries with 'active' and 'name' keys

    Returns:
        List of uppercase user names for active users
    """
    if not users or not isinstance(users, list):
        return []

    return [
        user.get('name', '').upper()
        for user in users
        if isinstance(user, dict) and user.get('active', False)
    ]
```

**Improvements**:
• Type hints for clarity
• Input validation
• Safe dictionary access with .get()
• List comprehension for efficiency
• Docstring for documentation
```

### Message Features

**While Chatting**:

1. **Multi-line Messages**: Press `Shift + Enter` for new lines
2. **Edit Previous**: Press `↑` to edit your last message
3. **Copy Response**: Click 📋 on any AI message
4. **Regenerate**: Click 🔄 to get a different response
5. **Rate Response**: Click 👍 or 👎 to provide feedback

[Screenshot: Message with action buttons]

## RAG-Enhanced Chat (With Documents)

RAG (Retrieval Augmented Generation) allows the AI to answer questions based on your uploaded documents.

### How RAG Works

```
Your Question
     ↓
[Vector Database Search]
     ↓
Retrieve Relevant Chunks (top 3-5)
     ↓
[AI Model] ← Question + Retrieved Chunks
     ↓
Response with Citations
```

### Step 1: Upload Documents

Before using RAG, you need documents in the system:

1. Go to **📁 Files** page (sidebar or top menu)
2. Upload documents (see [Document Management](05-document-management.md))
3. Wait for processing to complete

[Screenshot: File upload interface]

### Step 2: Select Document Collection

Back in Direct Chat mode:

1. Look for **Collection Selection** above the chat
2. Choose a collection from the dropdown:
   ```
   Collection: [Technical Specifications ▼]

   Contains: 5 documents, 234 chunks
   Last updated: 2025-11-18 14:30
   ```

[Screenshot: Collection selection dropdown]

**What are Collections?**
- Groups of related documents
- Stored together in ChromaDB vector database
- Allow focused searches within specific document sets

### Step 3: Enable RAG Mode

1. Toggle **Use RAG** switch to ON
   ```
   Use RAG (Document Search): ☑
   ```

2. Configure RAG settings (optional):
   ```
   Number of Results: [5  ▼] (1-10)
   Score Threshold:  [0.5 ▼] (0.0-1.0)
   Include Metadata: ☑
   ```

[Screenshot: RAG settings panel]

**RAG Settings Explained**:
- **Number of Results**: How many document chunks to retrieve
  - More = more context but slower
  - Typical: 3-5
- **Score Threshold**: Minimum relevance score (0-1)
  - Higher = only very relevant chunks
  - Lower = more chunks but less relevant
  - Typical: 0.3-0.7
- **Include Metadata**: Show page numbers, document names

### Step 4: Ask Document Questions

Now ask questions about your documents:

[Screenshot: RAG chat with citations]

```
You: What are the system requirements mentioned in the specification?

AI: Based on the Technical Specification document, the system
requirements are:

Hardware Requirements:
• Minimum 16 GB RAM
• 8-core CPU (x86_64 architecture)
• 500 GB SSD storage
• Gigabit network interface

Software Requirements:
• Ubuntu 20.04 LTS or later
• Docker 24.0.0+
• Python 3.10+
• PostgreSQL 15+

Environmental Requirements:
• Operating temperature: 10-35°C
• Humidity: 20-80% non-condensing
• Uninterruptible power supply (UPS) recommended

Sources:
📄 Technical_Spec_v2.pdf
   • Page 12, Section 3.2 (score: 0.92)
   • Page 13, Section 3.3 (score: 0.87)
   • Page 15, Section 3.5 (score: 0.81)
```

**Notice the Citations**:
- Each source shows: document name, page number, relevance score
- Click on citations to view the exact text
- Higher score = more relevant to your question

### Advanced RAG Questions

**Comparative Questions**:
```
You: How do the requirements in version 1 differ from version 2?

AI: [Compares multiple documents in the collection]
```

**Summarization**:
```
You: Summarize the main test procedures described in section 5.

AI: [Summarizes relevant sections across pages]
```

**Extraction**:
```
You: Extract all mentioned IP addresses and port numbers.

AI: Based on the network configuration section:

IP Addresses:
• Management Interface: 192.168.1.100
• Data Interface: 10.0.0.50
• Gateway: 192.168.1.1

Port Numbers:
• API Server: 9020
• Web Interface: 8501
• Database: 5432
• Redis Cache: 6379

Sources: [Citations provided]
```

## Advanced Features

### Conversation Management

**Save Conversation**:
1. Click **💾 Save** button above chat
2. Enter a name for the conversation
3. Conversation saved to database

**Load Previous Conversation**:
1. Click **📁 Load** button
2. Select from list of saved conversations
3. Conversation history loads in chat

**Export Conversation**:
1. Click **⬇️ Export** button
2. Choose format:
   - Markdown (.md)
   - JSON (.json)
   - PDF (.pdf)
3. Download file

[Screenshot: Conversation management buttons]

### Multi-Turn Context

The AI maintains context across multiple messages:

```
You: What is the maximum operating temperature?

AI: The maximum operating temperature is 35°C according to the
environmental requirements.

You: What happens if it exceeds that?

AI: If the operating temperature exceeds 35°C, the specification
states that:
1. System performance may degrade
2. Automatic thermal throttling will engage
3. Critical components may shut down if temperature reaches 40°C
4. Warranty may be voided

This is to protect the hardware from heat damage.

[AI remembered we were discussing temperature from previous message]
```

### Follow-up Questions

Use follow-up questions to dig deeper:

```
You: What are the backup procedures?

AI: [Provides overview of backup procedures]

You: Can you elaborate on the incremental backup process?

AI: [Focuses specifically on incremental backups]

You: What's the retention policy for those backups?

AI: [Provides retention policy details]
```

### Source Verification

**View Source Text**:
1. Click on a citation in the response
2. A popup shows the exact text from the document
3. See surrounding context

[Screenshot: Source text popup]

```
┌─────────────────────────────────────────────┐
│ Source: Technical_Spec_v2.pdf (Page 12)     │
├─────────────────────────────────────────────┤
│ 3.2 Hardware Requirements                   │
│                                             │
│ The system shall meet the following         │
│ minimum hardware requirements:              │
│                                             │
│ • Minimum 16 GB RAM (32 GB recommended)    │
│ • 8-core CPU with AVX2 support             │
│ • 500 GB SSD storage (1 TB recommended)    │
│ • Gigabit network interface                │
│                                             │
│ For production deployments, the            │
│ recommended specifications should be used.  │
│                                             │
│ [Close]                                     │
└─────────────────────────────────────────────┘
```

### Streaming Responses

Enable **Streaming** in settings to see responses as they're generated:

```
Settings:
☑ Enable Streaming

[Watch AI type response in real-time]
```

**Benefits**:
- See responses faster
- Get feedback immediately
- Cancel long responses early

### Token Usage Tracking

Enable **Show Token Count** to monitor API usage:

```
Settings:
☑ Show Token Count

---

AI Response: [Message content]

Tokens: 234 (Input: 123, Output: 111)
Estimated Cost: $0.0047
```

**Useful For**:
- Monitoring OpenAI API costs
- Optimizing prompt length
- Understanding model efficiency

## Best Practices

### Writing Effective Prompts

**Be Specific**:
```
❌ "Tell me about the system"
✓ "What are the system's network security requirements?"
```

**Provide Context**:
```
❌ "Is this compliant?"
✓ "Does the proposed architecture comply with the security
   requirements in section 4.2?"
```

**Ask One Thing at a Time**:
```
❌ "What are the requirements, test procedures, and acceptance
   criteria?"
✓ "What are the functional requirements in section 3?"
[Then in follow-up]: "What test procedures verify these
requirements?"
```

**Use Clear Language**:
```
❌ "Gimme the deets on the specs"
✓ "Please summarize the technical specifications"
```

### Optimizing RAG Performance

**Right Number of Results**:
- Simple questions: 3 results
- Complex questions: 5-7 results
- Very broad questions: 8-10 results

**Adjust Score Threshold**:
- If getting irrelevant results: Increase threshold (0.6-0.8)
- If getting too few results: Decrease threshold (0.3-0.5)

**Collection Organization**:
- Group related documents together
- Separate unrelated topics into different collections
- Keep collections focused (< 50 documents)

### Managing Long Conversations

**Reset When Needed**:
- Click **🗑️ Clear Chat** to start fresh
- Prevents context confusion
- Reduces token usage

**Save Important Conversations**:
- Use **💾 Save** regularly
- Name conversations descriptively
- Export key conversations for records

## Common Use Cases

### 1. Requirements Analysis

**Extract Requirements**:
```
You: List all functional requirements from the specification.

AI: [Provides numbered list of requirements with citations]
```

**Verify Compliance**:
```
You: Does the proposed design meet requirement 3.4.2?

AI: [Analyzes design docs against requirements with citations]
```

### 2. Test Planning

**Identify Test Cases**:
```
You: What test cases are needed to verify the authentication
system?

AI: [Suggests test cases based on requirements]
```

**Understand Test Procedures**:
```
You: Explain the test procedure for network failover testing.

AI: [Provides step-by-step explanation from test plan]
```

### 3. Technical Research

**Find Specifications**:
```
You: What encryption algorithms are specified for data at rest?

AI: [Extracts specific algorithm requirements with citations]
```

**Compare Versions**:
```
You: What changed between version 1.0 and 2.0 of the API?

AI: [Compares documents and lists changes]
```

### 4. Documentation Assistance

**Clarify Technical Terms**:
```
You: What does "fail-safe mode" mean in this context?

AI: [Defines term based on document usage with examples]
```

**Find Related Information**:
```
You: Where else in the document is database replication discussed?

AI: [Lists all relevant sections with page numbers]
```

## Troubleshooting

### No Results from RAG

**Problem**: RAG returns "No relevant documents found"

**Solutions**:
1. **Lower score threshold**: Try 0.3 instead of 0.7
2. **Increase number of results**: Try 10 instead of 5
3. **Rephrase question**: Use different keywords
4. **Check collection**: Ensure documents are uploaded and processed
5. **Verify document content**: Document might not contain that information

### Irrelevant Results

**Problem**: RAG returns unrelated document chunks

**Solutions**:
1. **Increase score threshold**: Try 0.7 instead of 0.3
2. **Be more specific**: Add details to your question
3. **Check collection**: Might have wrong documents
4. **Review chunks**: Click citations to verify relevance

### Slow Responses

**Problem**: AI takes too long to respond

**Solutions**:
1. **Switch to faster model**: Use `gpt-4o-mini` or `llama3.2:3b`
2. **Reduce context**: Lower number of RAG results
3. **Check system health**: Sidebar should show all green
4. **Reduce max tokens**: Lower max response length
5. **For Ollama**: Ensure GPU is being used (if available)

### Inconsistent Answers

**Problem**: AI gives different answers to same question

**Solutions**:
1. **Lower temperature**: Set to 0.0-0.3 for deterministic responses
2. **Be more specific**: Provide clearer context
3. **Check sources**: Different chunks might be retrieved
4. **Provide examples**: Show desired output format

### Context Not Maintained

**Problem**: AI forgets previous messages

**Solutions**:
1. **Check session**: Ensure not in new session
2. **Reference explicitly**: "As you mentioned earlier..."
3. **Token limit**: Very long conversations might truncate
4. **Clear and restart**: If conversation too long

### Citations Missing

**Problem**: No source citations in responses

**Solutions**:
1. **Enable RAG**: Ensure "Use RAG" is toggled ON
2. **Check settings**: "Include Metadata" should be enabled
3. **Verify collection**: Collection must be selected
4. **Model support**: Ensure model supports citations

## Next Steps

Now that you understand Direct Chat:

- **[Document Management](05-document-management.md)** - Upload and organize documents
- **[Document Generator](06-document-generator.md)** - Generate comprehensive test plans
- **[Multi-Agent Analysis](07-multi-agent-analysis.md)** - Use multiple AI perspectives
- **[Model Selection Guide](11-model-selection.md)** - Choose the best model for your needs

---

**Need more help?** See the [FAQ](13-faq.md) or [Troubleshooting Guide](12-troubleshooting.md).
