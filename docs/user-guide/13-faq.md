# Frequently Asked Questions (FAQ)

## General Questions

### What is DIS Verification GenAI?

DIS Verification GenAI is an AI-powered system that analyzes technical documents and automatically generates comprehensive test plans, test procedures, and verification documents for Defense Information Systems.

### Is this tool approved for classified information?

When using **Ollama local models only**, all processing happens on your infrastructure with no external communication. For classified use, deploy in an air-gapped environment with Ollama models exclusively. Never use OpenAI models with classified information.

### How much does it cost?

The application itself is **free and open source**. Costs depend on:
- **OpenAI models**: Pay per use (~$0.50 per test plan with gpt-4o)
- **Ollama models**: FREE (uses your hardware)
- **Infrastructure**: Your Docker host (can run on existing servers)

### Can I use this offline?

**Yes**, with Ollama models. The application can run completely offline:
1. Install using offline installer
2. Use only Ollama models
3. No internet required after initial setup

## Installation & Setup

### What are the system requirements?

**Minimum**: 4-core CPU, 8 GB RAM, 50 GB disk
**Recommended**: 8-core CPU, 16 GB RAM, 100 GB SSD
**For Ollama**: Add 8 GB RAM per model

See [Installation Guide](02-installation-setup.md) for details.

### Which operating systems are supported?

- Windows 10/11 (64-bit)
- macOS 11+ (Intel and Apple Silicon)
- Linux (Ubuntu 20.04+, Debian 11+, RHEL 8+, Fedora 35+)

### Do I need Docker?

**Yes**, Docker is required. The application runs as Docker containers for:
- Easy installation
- Consistent environment
- Service isolation
- Easy updates

### Do I need an OpenAI API key?

**No**, if you use Ollama local models. You only need an API key if you want to use OpenAI's GPT models (gpt-4o, etc.).

Get a key at: https://platform.openai.com/api-keys

### How do I get an OpenAI API key?

1. Go to https://platform.openai.com/signup
2. Create account (or sign in)
3. Add payment method (required for API access)
4. Go to https://platform.openai.com/api-keys
5. Click "Create new secret key"
6. Copy key (starts with `sk-`)
7. Add to `.env` file: `OPENAI_API_KEY=sk-...`

### Can I upgrade from a previous version?

**Yes**:
```bash
# Pull latest version
git pull origin main

# Rebuild containers
docker compose down
docker compose pull
docker compose up -d
```

See [CHANGELOG.md](../../CHANGELOG.md) for version changes.

## Using the Application

### Which AI model should I use?

**Best overall**: `gpt-4o` (OpenAI) - highest quality
**Best local**: `llama3.1:8b` (Ollama) - good quality, private
**Fastest**: `gpt-4o-mini` (OpenAI) - quick, affordable
**Most private**: Any Ollama model - fully local

See [Model Selection Guide](11-model-selection.md) for detailed comparison.

### How long does test plan generation take?

**Typical times**:
- Small docs (10-20 pages): 5-10 minutes
- Medium docs (50-100 pages): 15-30 minutes
- Large docs (200+ pages): 30-60 minutes

Depends on:
- Document size
- Analysis depth (Quick/Standard/Deep)
- Model used (OpenAI faster than Ollama)
- Hardware (especially for Ollama)

### Can I cancel a long-running generation?

**Yes**, click the **Cancel** button during generation. The process will stop and any partial results are discarded.

### What document formats are supported?

**Fully supported**:
- PDF (.pdf) - most common
- Word (.docx)
- Plain text (.txt)

**Maximum size**: 100 MB per file

### Will scanned PDFs work?

**Depends**. If the PDF has been OCR'd (text is selectable), yes. If it's just scanned images with no OCR, text extraction will fail. Consider OCR'ing documents first with tools like Adobe Acrobat.

### How accurate is the AI?

**Very good but not perfect**. AI models (especially gpt-4o) are highly accurate but can:
- Miss subtle requirements
- Misinterpret ambiguous language
- Generate overly creative or incorrect tests

**Always review AI-generated content** before use. AI is a tool to accelerate work, not replace human expertise.

### Can I edit the generated test plans?

**Yes**, extensively:
- Edit test plans in Markdown
- Edit individual test cards
- Add/remove test steps
- Modify pass/fail criteria
- Export to Word for further editing

### How do I export results?

Multiple export options:
- **Test Plan**: Markdown, PDF
- **Test Cards**: Word (.docx), Excel, individual cards
- **Requirements Matrix**: CSV
- **Full Report**: ZIP with all outputs

See [Document Generator](06-document-generator.md#export-options) for details.

## RAG & Document Search

### What is RAG?

**RAG** = Retrieval Augmented Generation

Instead of just asking the AI, RAG:
1. Searches your documents for relevant content
2. Provides that content to the AI as context
3. AI answers based on your documents
4. Includes citations to sources

**Result**: More accurate, grounded answers with references.

### Why aren't my documents being found in RAG?

Common reasons:
1. **Document not processed**: Check Files page for "Processed" status
2. **Wrong collection selected**: Ensure correct collection chosen
3. **Score threshold too high**: Lower to 0.3-0.5
4. **Question phrasing**: Use keywords from document
5. **Not enough results requested**: Increase to 8-10

See [Troubleshooting RAG](12-troubleshooting.md#rag-document-search-issues).

### How are documents chunked for RAG?

Three strategies:
- **Page-based** (default): One chunk per page
- **Section-based**: One chunk per section/chapter
- **Fixed-size**: Fixed number of tokens per chunk

Page-based works well for most technical documents. See [Document Management](05-document-management.md#chunking-strategies).

### What are collections?

**Collections** are groups of related documents stored together. Like folders, but for semantic search. Create collections for:
- Projects
- Document types
- Time periods
- Topics

## Multi-Agent System

### What are agents?

**Agents** are AI instances with specific roles and prompts. Like having multiple experts review a document:
- Requirements analyst agent
- Test engineer agent
- Security specialist agent
- Review/critic agent

Each provides different perspective, improving overall analysis.

### How many agents should I use?

**Typical**:
- Simple docs: 2-3 agents
- Standard docs: 3-5 agents (default)
- Complex docs: 5-7 agents

**More agents** = better coverage but longer time and higher cost.

### Can I create my own agents?

**Yes**! Go to Agent & Orchestration Manager:
1. Create new agent
2. Define role and purpose
3. Write system prompt
4. Configure model and settings
5. Test and save

See [Agent Manager](09-agent-manager.md) for details.

### What is agent debate?

**Agent debate** is when multiple agents discuss their findings to reach consensus. Like a panel of experts discussing a document. Helps catch misinterpretations and improves accuracy.

Enable in Document Generator settings: **Multi-Round Analysis**

## Performance & Cost

### How can I reduce OpenAI API costs?

1. **Use cheaper models**: gpt-4o-mini instead of gpt-4o
2. **Use local models**: Ollama (free)
3. **Quick analysis**: Instead of Deep
4. **Fewer agents**: 2-3 instead of 5-7
5. **Smaller documents**: Split large docs
6. **Set budget alerts**: In OpenAI dashboard

### Why is Ollama slow?

**Ollama runs on your hardware**. Speed depends on:
- CPU performance
- RAM available
- **GPU** (10-20x faster if you have NVIDIA GPU)

**Solutions**:
- Enable GPU acceleration (Linux)
- Use smaller models (llama3.2:3b)
- Close other applications
- Upgrade hardware

### How do I enable GPU for Ollama?

**Linux with NVIDIA GPU**:
1. Install NVIDIA drivers
2. Install NVIDIA Container Toolkit
3. Ollama automatically uses GPU

See [Installation Guide](02-installation-setup.md#configuring-gpu-acceleration).

**Windows/macOS**: Ollama runs on host (outside Docker) and auto-detects GPU.

### The application is using too much memory

**Solutions**:
1. **Restart services**: `docker compose restart`
2. **Use smaller models**: llama3.2:3b instead of llama3.1:8b
3. **Increase Docker memory**: Docker Desktop → Settings → Resources
4. **Reduce workers**: Edit docker-compose.yml celery concurrency
5. **Clear cache**: Database Manager → Clean Up

## Data & Privacy

### Where is my data stored?

**Locally** in:
- **PostgreSQL**: Chat history, metadata, users
- **ChromaDB**: Document vectors/embeddings
- **File system**: Uploaded documents

**Location** (Docker volumes):
- `./postgres_data/`
- `./chroma_data/`
- Uploaded files in container

### Is my data sent to the cloud?

**Depends on model**:
- **OpenAI models**: Yes, documents and prompts sent to OpenAI API
- **Ollama models**: No, all processing local

### How do I backup my data?

**Automated backup**:
```bash
# Backup script (coming soon)
./scripts/backup.sh
```

**Manual backup**:
```bash
# PostgreSQL
docker compose exec postgres pg_dump -U postgres dis_verification_db > backup.sql

# ChromaDB
tar -czf chroma_backup.tar.gz ./chroma_data

# Uploaded files
tar -czf files_backup.tar.gz ./uploads
```

See [Database Manager](10-database-manager.md#backup-database) for details.

### Can I delete my data?

**Yes**:
- **Documents**: Files page → Select → Delete
- **Chat history**: Database Manager → chat_sessions → Delete
- **Everything**: `docker compose down -v` (deletes all volumes)

**Warning**: Deletion is permanent!

### Is this GDPR compliant?

The application itself doesn't collect user data. Compliance depends on:
- Your deployment (on-premises = full control)
- Model used (Ollama = local, OpenAI = see their policy)
- Your data handling procedures

For GDPR compliance:
- Use Ollama models exclusively
- Deploy on-premises
- Implement access controls
- Document data flows

## Troubleshooting

### Services won't start

See [Troubleshooting: Services Won't Start](12-troubleshooting.md#services-wont-start)

**Quick checks**:
```bash
docker compose ps  # All should show "Up"
docker compose logs  # Check for errors
docker compose restart  # Try restarting
```

### I get "Connection refused" errors

**Check services running**:
```bash
docker compose ps

# Should show:
# streamlit     Up (healthy)
# fastapi       Up (healthy)
# postgres      Up (healthy)
# chromadb      Up (healthy)
# redis         Up (healthy)
# celery-worker Up
```

**Restart if needed**:
```bash
docker compose restart
```

### OpenAI API key not working

**Check key format**:
- Should start with `sk-`
- No extra spaces
- In `.env` file: `OPENAI_API_KEY=sk-...`

**Check billing**:
- OpenAI account has credits
- Payment method added
- Not rate limited

**Test key**:
```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Ollama models not loading

**Check Ollama running**:
```bash
curl http://localhost:11434/api/tags
```

**Pull model**:
```bash
ollama pull llama3.1:8b
ollama list  # Verify
```

**Check URL in .env**:
```
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

See [Troubleshooting: Ollama Issues](12-troubleshooting.md#ollama-not-working).

## Advanced Usage

### Can I run this in production?

**Yes**, but consider:
- Use reverse proxy (nginx) for HTTPS
- Set up authentication
- Monitor resources
- Regular backups
- Set up monitoring/alerting
- Use docker-compose production config

### Can I integrate with other tools?

**Current integrations**:
- LangSmith (optional, for debugging)
- OpenAI API
- Ollama

**Future integrations** (roadmap):
- Jira, TestRail (test management)
- GitHub, GitLab (CI/CD)
- Slack (notifications)

**API available**: FastAPI at `http://localhost:9020/docs`

### Can I contribute to development?

**Yes!** This is open source.

1. Fork the repository
2. Create a feature branch
3. Make changes
4. Add tests
5. Submit pull request

See [README.md](../../README.md) for development setup.

### How do I update to a new version?

```bash
# Pull latest code
git pull origin main

# Rebuild containers
docker compose down
docker compose build
docker compose up -d
```

Check [CHANGELOG.md](../../CHANGELOG.md) for breaking changes.

## Still Have Questions?

- **Documentation**: Browse all [user guides](../README.md)
- **GitHub Issues**: [Report bugs](https://github.com/yourusername/dis_verification_genai/issues)
- **GitHub Discussions**: Ask questions
- **Troubleshooting**: [Comprehensive guide](12-troubleshooting.md)

---

**Question not answered?** Open a GitHub discussion!
