# Getting Started with DIS Verification GenAI

Welcome! This guide will help you take your first steps with DIS Verification GenAI, an AI-powered system for analyzing technical documents and generating comprehensive test plans and verification procedures.

## What is DIS Verification GenAI?

DIS Verification GenAI is an intelligent document analysis and test generation system designed for Defense Information Systems (DIS) testing and compliance. It uses advanced AI technology to:

- **Analyze technical documents** and extract requirements automatically
- **Generate comprehensive test plans** from specification documents
- **Create detailed test cards** with step-by-step procedures
- **Answer questions** about your technical documents using AI
- **Provide multi-perspective analysis** through coordinated AI agents

## System Overview

[Screenshot: Main application interface showing all modes]

The application consists of five main modes:

1. **Direct Chat** - Interactive conversation with AI about your documents
2. **AI Agent Simulation** - Run specialized AI agents on documents
3. **Agent & Orchestration Manager** - Create and manage custom AI agents
4. **Document Generator** - Generate test plans and verification procedures
5. **Test Card Viewer** - View and export test cards

## Prerequisites

Before you begin, ensure you have:

- ✅ Successfully installed DIS Verification GenAI (see [Installation & Setup](02-installation-setup.md))
- ✅ Docker and Docker Compose running
- ✅ (Optional) OpenAI API key for cloud models
- ✅ (Optional) Ollama installed for local models

## Your First Steps

### Step 1: Start the Application

**Using the Installer Package:**
1. Open the installed application from your Start Menu (Windows), Applications folder (macOS), or application menu (Linux)
2. The application will automatically start all required services

[Screenshot: Application launcher]

**Using Docker Compose (Manual Installation):**
```bash
# From the project root directory
docker compose up -d
```

**Verify Services are Running:**
```bash
docker compose ps
```

You should see all services in "running" state:
- `streamlit` (Port 8501)
- `fastapi` (Port 9020)
- `postgres` (Port 5432)
- `chromadb` (Port 8000)
- `redis` (Port 6379)
- `celery-worker`

### Step 2: Access the Web Interface

1. Open your web browser
2. Navigate to: `http://localhost:8501`
3. You should see the DIS Verification GenAI home page

[Screenshot: Home page with welcome message and health status]

### Step 3: Check System Health

The application includes a real-time health monitoring sidebar:

1. Look at the **left sidebar** of the interface
2. Verify that all services show **🟢 Healthy** status:
   - FastAPI Backend
   - PostgreSQL Database
   - ChromaDB Vector Store
   - Redis Cache
   - Celery Worker

[Screenshot: Health status sidebar showing all services healthy]

**What if services are unhealthy?**
- See the [Troubleshooting Guide](12-troubleshooting.md) for solutions
- Check Docker logs: `docker compose logs <service-name>`

### Step 4: Select Your AI Model

Before using any features, you need to select an AI model:

1. In the sidebar, locate the **Model Selection** section
2. Choose between:
   - **OpenAI Models** (requires API key) - Best performance, cloud-based
   - **Ollama Models** (local) - Privacy-focused, US-based, no API key needed

[Screenshot: Model selection dropdown with available models]

**For OpenAI Models:**
- Ensure your `.env` file contains: `OPENAI_API_KEY=sk-...`
- Recommended: `gpt-4o` for best results

**For Ollama Models:**
- Ensure Ollama is installed and running
- Models are automatically pulled on first use
- Recommended: `llama3.1:8b` for balanced performance

**Learn more:** [Model Selection Guide](11-model-selection.md)

### Step 5: Try Your First Feature

Let's start with a simple Direct Chat to verify everything works:

1. **Select Direct Chat Mode**
   - In the sidebar, click on **Mode Selection**
   - Choose **Direct Chat**

[Screenshot: Mode selection with Direct Chat highlighted]

2. **Ask a Simple Question**
   - In the chat input box at the bottom, type: "What can you help me with?"
   - Click **Send** or press Enter

[Screenshot: Chat interface with example question]

3. **Review the Response**
   - The AI will respond with information about its capabilities
   - Response time depends on the model (OpenAI: 2-5s, Ollama: 5-15s)

[Screenshot: AI response showing capabilities]

**Congratulations!** You've successfully completed your first interaction with DIS Verification GenAI.

## Next Steps

Now that you have the basics working, here's what to explore next:

### For Test Plan Generation
If your primary goal is to generate test plans from documents:

1. **Upload a Document** → [Document Management Guide](05-document-management.md)
2. **Generate a Test Plan** → [Document Generator Mode](06-document-generator.md)
3. **Export Test Cards** → [Test Card Viewer](08-test-card-viewer.md)

### For Document Analysis
If you want to analyze and ask questions about technical documents:

1. **Upload Documents** → [Document Management Guide](05-document-management.md)
2. **Use Direct Chat with RAG** → [Direct Chat Mode](04-direct-chat.md)
3. **Run Agent Analysis** → [Agent Manager](09-agent-manager.md)

### For Advanced Users
If you want to customize the AI behavior:

1. **Create Custom Agents** → [Agent Manager](09-agent-manager.md)
2. **Configure Multi-Agent Workflows** → [Multi-Agent Analysis](07-multi-agent-analysis.md)
3. **Manage Vector Database** → [Database Manager](10-database-manager.md)

## Common First-Time Questions

**Q: Which AI model should I use?**
- For best accuracy: `gpt-4o` (OpenAI)
- For local/private: `llama3.1:8b` (Ollama)
- For fastest results: `gpt-4o-mini` (OpenAI)

**Q: Do I need an OpenAI API key?**
- No, if you use Ollama local models
- Yes, if you want to use OpenAI's GPT models

**Q: How much does it cost to use OpenAI models?**
- You pay OpenAI directly based on usage
- Typical test plan generation: $0.10 - $0.50 per document
- Direct chat: $0.01 - $0.05 per conversation

**Q: Are my documents secure?**
- With Ollama: All processing happens locally, nothing leaves your machine
- With OpenAI: Documents are sent to OpenAI's API (see their privacy policy)
- All documents are stored locally in your PostgreSQL and ChromaDB databases

**Q: What document formats are supported?**
- PDF (most common)
- DOCX (Microsoft Word)
- TXT (plain text)
- Images are automatically extracted from PDFs

**Q: How long does test plan generation take?**
- Small documents (10-20 pages): 2-5 minutes
- Medium documents (50-100 pages): 5-15 minutes
- Large documents (200+ pages): 15-30 minutes

## Understanding the Interface

### Main Components

[Screenshot: Annotated interface showing all major components]

1. **Sidebar (Left)**
   - Mode selection
   - Model selection
   - Health monitoring
   - Session management

2. **Main Content Area (Center)**
   - Changes based on selected mode
   - Primary workspace for all interactions

3. **Status Bar (Top)**
   - Current mode
   - Selected model
   - Session information

4. **Footer (Bottom)**
   - Version information
   - Documentation links

### Navigation Tips

- **Switch Modes**: Use the sidebar mode selector
- **Change Models**: Use the model dropdown (takes effect immediately)
- **Upload Files**: Look for the file uploader in each mode
- **View History**: Check the session management section
- **Monitor Health**: Always visible in sidebar

## Typical Workflows

### Workflow 1: Generate a Test Plan (Most Common)

```
1. Upload Document → 2. Select Document Generator →
3. Choose Document → 4. Run Generation → 5. Export Results
```

**Time Required**: 5-30 minutes depending on document size

### Workflow 2: Analyze a Document with RAG

```
1. Upload Document → 2. Select Direct Chat →
3. Choose Collection → 4. Ask Questions → 5. Review Citations
```

**Time Required**: 2-10 minutes for setup, then real-time chat

### Workflow 3: Create Custom Agent Workflow

```
1. Select Agent Manager → 2. Create Agents →
3. Configure Agent Set → 4. Run Analysis → 5. Compare Results
```

**Time Required**: 10-20 minutes for setup, then varies by analysis

## Getting Help

If you encounter any issues:

1. **Check the health status** in the sidebar - are all services healthy?
2. **Review the logs**:
   ```bash
   docker compose logs streamlit
   docker compose logs fastapi
   ```
3. **Consult the troubleshooting guide**: [Troubleshooting Guide](12-troubleshooting.md)
4. **Check the FAQ**: [Frequently Asked Questions](13-faq.md)
5. **Report an issue**: Use the GitHub issue tracker

## Learning Resources

- **Quick Start**: [QUICKSTART.md](../../QUICKSTART.md) - 10-minute overview
- **Installation**: [INSTALL.md](../../INSTALL.md) - Detailed setup instructions
- **Changelog**: [CHANGELOG.md](../../CHANGELOG.md) - What's new in each version
- **Technical Docs**: [README.md](../../README.md) - Architecture and development

## Best Practices for New Users

✅ **DO:**
- Start with small documents (< 50 pages) to learn the system
- Use GPT-4o for your first test plan for best results
- Review the generated output carefully
- Keep documents well-structured (clear sections, headers)
- Monitor the health status sidebar

❌ **DON'T:**
- Upload extremely large documents (> 500 pages) on your first try
- Mix multiple unrelated documents in one collection
- Close the browser during long-running operations
- Forget to check model selection before starting
- Ignore error messages or health warnings

## What's Next?

You're now ready to dive deeper into specific features. Choose your path:

- **[Installation & Setup](02-installation-setup.md)** - Configure advanced settings
- **[UI Overview](03-ui-overview.md)** - Master the interface
- **[Direct Chat](04-direct-chat.md)** - Learn interactive chat features
- **[Document Generator](06-document-generator.md)** - Start generating test plans

---

**Ready to generate your first test plan?** Head to the [Document Generator Guide](06-document-generator.md)!
