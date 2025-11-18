# Quick Reference Card

## Starting the Application

```bash
# Start all services
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f
```

**Access**: http://localhost:8501

## Common Tasks

### Generate Test Plan

1. Upload document → **Files** page
2. Switch to **Document Generator** mode
3. Select document
4. Choose analysis type (Standard recommended)
5. Click **Generate Test Plan**
6. Wait 15-30 minutes
7. Review results → Export

### Ask Questions About Documents (RAG)

1. Upload documents → **Files** page
2. Switch to **Direct Chat** mode
3. Select collection
4. Toggle **Use RAG** ON
5. Ask questions
6. Review cited sources

### Create Custom Agent

1. Switch to **Agent & Orchestration Manager**
2. Click **Create New Agent**
3. Configure name, role, prompt
4. Select model and temperature
5. Test agent
6. Save

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+K` | Global search |
| `Enter` | Send chat message |
| `Shift+Enter` | New line in chat |
| `Alt+1-5` | Switch modes |
| `Ctrl+/` | Show shortcuts |
| `Esc` | Close dialog |

## Model Quick Picks

| Need | Recommended |
|------|-------------|
| **Best Quality** | gpt-4o |
| **Best Local** | llama3.1:8b |
| **Fastest** | gpt-4o-mini |
| **Most Private** | llama3.1:8b |
| **Cheapest** | llama3.1:8b (free) |

## Temperature Guide

| Value | Use For |
|-------|---------|
| 0.0-0.3 | Factual extraction, requirements |
| 0.4-0.6 | Standard analysis (default) |
| 0.7-0.9 | Creative test scenarios |
| 1.0-2.0 | Brainstorming, alternatives |

## Troubleshooting Quick Fixes

**Service Unhealthy?**
```bash
docker compose restart <service-name>
```

**Slow Responses?**
- Switch to faster model (gpt-4o-mini)
- For Ollama: Use smaller model (llama3.2:3b)
- Check system resources

**OpenAI Error?**
```bash
# Check API key in .env
cat .env | grep OPENAI_API_KEY

# Should start with: sk-
```

**Ollama Not Working?**
```bash
# Check Ollama running
curl http://localhost:11434/api/tags

# Pull model if missing
ollama pull llama3.1:8b
```

**RAG No Results?**
- Lower score threshold to 0.3
- Increase results to 10
- Check document is processed
- Rephrase question

**Processing Stuck?**
```bash
docker compose restart celery-worker
```

## File Locations

| What | Where |
|------|-------|
| **Logs** | `docker compose logs <service>` |
| **Config** | `.env` |
| **Data** | Docker volumes (postgres_data, chroma_data) |
| **Uploads** | Inside containers |
| **Documentation** | `docs/` folder |

## Default Ports

| Service | Port |
|---------|------|
| Streamlit (UI) | 8501 |
| FastAPI (API) | 9020 |
| PostgreSQL | 5432 |
| ChromaDB | 8000 |
| Redis | 6379 |
| Ollama | 11434 |

## Backup Commands

```bash
# Backup PostgreSQL
docker compose exec postgres pg_dump -U postgres dis_verification_db > backup.sql

# Backup ChromaDB
tar -czf chroma_backup.tar.gz ./chroma_data

# Backup config
cp .env env_backup
```

## Typical Workflows

### Test Plan from Scratch

```
1. Upload PDF → Files page (2 min)
2. Wait for processing (5 min)
3. Document Generator mode
4. Select document
5. Standard analysis
6. Generate (20 min)
7. Review & export

Total: ~30 minutes
```

### Document Q&A

```
1. Upload documents → Files (one-time)
2. Direct Chat mode
3. Select collection
4. Enable RAG
5. Ask questions

First time: 10 min setup
After: Real-time Q&A
```

## Cost Estimates (OpenAI)

| Task | Model | Typical Cost |
|------|-------|--------------|
| Test Plan (50 pages) | gpt-4o | $0.50 |
| Test Plan (50 pages) | gpt-4o-mini | $0.15 |
| Chat session (30 msg) | gpt-4o | $0.15 |
| RAG query | gpt-4o | $0.01 |

**Ollama models**: FREE (uses your hardware)

## Getting Help

1. **Check health** → Sidebar indicators
2. **Check logs** → `docker compose logs`
3. **User Guide** → `docs/user-guide/`
4. **FAQ** → `docs/user-guide/13-faq.md`
5. **Troubleshooting** → `docs/user-guide/12-troubleshooting.md`
6. **GitHub Issues** → Report bugs

## Full Documentation

Start here: [docs/README.md](README.md)

---

**Print this page for quick reference!**
