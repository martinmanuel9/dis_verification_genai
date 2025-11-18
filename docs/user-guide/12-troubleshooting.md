# Troubleshooting Guide

Common issues and solutions for DIS Verification GenAI.

## Quick Diagnostics

### Check System Health

1. Look at sidebar health indicators
2. All services should be 🟢 green
3. If any are 🔴 red or 🟡 yellow, see below

### Check Logs

```bash
# View all logs
docker compose logs

# Specific service
docker compose logs streamlit
docker compose logs fastapi
docker compose logs postgres
docker compose logs chromadb
docker compose logs celery-worker

# Follow logs in real-time
docker compose logs -f <service-name>
```

## Installation Issues

### Docker Won't Start

**Problem**: Cannot start Docker containers

**Solutions**:
```bash
# Check Docker is running
docker ps

# If not:
sudo systemctl start docker  # Linux
# or start Docker Desktop (Windows/macOS)

# Check Docker Compose version
docker compose version  # Should be 2.20.0+

# Restart all services
docker compose restart
```

### Port Already in Use

**Problem**: Error: "Port 8501 already in use"

**Solutions**:
```bash
# Find what's using the port
sudo lsof -i :8501  # Linux/macOS
netstat -ano | findstr :8501  # Windows

# Either:
# 1. Stop the conflicting service
# 2. Change port in docker-compose.yml:
#    ports:
#      - "8502:8501"  # Use 8502 instead
```

### Services Won't Start

**Problem**: Containers exit immediately

**Solutions**:
```bash
# Check specific service logs
docker compose logs <service-name>

# Common issues:
# - Missing .env file → Run scripts/setup-env.sh
# - Permissions → Check file ownership
# - Out of memory → Increase Docker memory limit
# - Disk full → Free up space

# Restart fresh
docker compose down
docker compose up -d
```

## Application Issues

### Cannot Access Web Interface

**Problem**: Browser shows "Unable to connect"

**Solutions**:

1. **Check Streamlit is running**:
   ```bash
   docker compose ps streamlit
   # Should show "Up" status
   ```

2. **Check correct URL**:
   - Should be: `http://localhost:8501`
   - NOT: `https://` or `127.0.0.1`

3. **Check firewall**:
   ```bash
   # Linux
   sudo ufw allow 8501

   # Windows - Add firewall rule for port 8501
   ```

4. **Restart Streamlit**:
   ```bash
   docker compose restart streamlit
   ```

### Blank Page or Loading Forever

**Problem**: Page loads but shows nothing

**Solutions**:

1. **Clear browser cache**:
   - Press `Ctrl+Shift+R` (Windows/Linux)
   - Press `Cmd+Shift+R` (macOS)

2. **Try different browser**:
   - Chrome, Firefox, Edge all supported
   - Private/incognito mode

3. **Check JavaScript enabled**:
   - Required for Streamlit

4. **Check browser console** (F12):
   - Look for errors
   - Report if found

### Services Show Unhealthy

**Problem**: Health indicator shows 🔴 or 🟡

**PostgreSQL Unhealthy**:
```bash
# Check PostgreSQL logs
docker compose logs postgres

# Restart PostgreSQL
docker compose restart postgres

# If still failing, reset database:
docker compose down postgres
docker volume rm dis_verification_genai_postgres_data
docker compose up -d postgres
# WARNING: This deletes all data!
```

**ChromaDB Unhealthy**:
```bash
# Check ChromaDB logs
docker compose logs chromadb

# Restart ChromaDB
docker compose restart chromadb

# Clear ChromaDB data if needed:
rm -rf ./chroma_data
docker compose restart chromadb
```

**Redis Unhealthy**:
```bash
docker compose restart redis
```

**Celery Worker Unhealthy**:
```bash
# Check Celery logs
docker compose logs celery-worker

# Restart worker
docker compose restart celery-worker
```

## Model Issues

### OpenAI API Errors

**Problem**: "Invalid API key" or "Rate limit exceeded"

**Solutions**:

1. **Check API key**:
   ```bash
   # View your .env file
   cat .env | grep OPENAI_API_KEY
   
   # Should start with: sk-
   # Get key from: https://platform.openai.com/api-keys
   ```

2. **Update API key**:
   ```bash
   # Edit .env file
   nano .env
   # or
   vim .env
   
   # Set: OPENAI_API_KEY=sk-your-actual-key
   
   # Restart services
   docker compose restart
   ```

3. **Rate limit**:
   - Wait a few minutes
   - Upgrade OpenAI plan
   - Use slower model (gpt-4o-mini)

4. **Billing**:
   - Check OpenAI account has credits
   - Add payment method if needed

### Ollama Not Working

**Problem**: "Cannot connect to Ollama" or "Model not found"

**Solutions**:

1. **Check Ollama is running**:
   ```bash
   curl http://localhost:11434/api/tags
   # Should return list of models
   ```

2. **Start Ollama**:
   ```bash
   # Linux/macOS
   ollama serve
   
   # Windows - start Ollama application
   ```

3. **Pull missing model**:
   ```bash
   ollama pull llama3.1:8b
   ollama list  # Verify downloaded
   ```

4. **Check Ollama URL in .env**:
   ```
   OLLAMA_BASE_URL=http://host.docker.internal:11434
   ```

### Model Responses Are Slow

**Problem**: Taking too long to respond

**Solutions**:

1. **For OpenAI**:
   - Use faster model (gpt-4o-mini, gpt-5-nano)
   - Check internet connection
   - Try during off-peak hours

2. **For Ollama**:
   - Use smaller model (llama3.2:3b instead of llama3.1:8b)
   - Enable GPU acceleration
   - Close other applications
   - Increase Docker memory limit

3. **Enable GPU** (Linux with NVIDIA):
   ```bash
   # Check GPU available
   nvidia-smi
   
   # Ollama will auto-use GPU if available
   # Check Ollama logs:
   ollama run llama3.1:8b "test"
   # Should say "using GPU"
   ```

## Document Processing Issues

### Upload Fails

**Problem**: Document won't upload

**Solutions**:

1. **Check file size**:
   - Maximum: 100 MB
   - Compress large PDFs if needed

2. **Check file format**:
   - Supported: PDF, DOCX, TXT
   - NOT supported: Images, scanned PDFs without OCR

3. **Check disk space**:
   ```bash
   df -h  # Linux/macOS
   ```

4. **Check logs**:
   ```bash
   docker compose logs fastapi | grep -i upload
   ```

### Processing Stuck

**Problem**: Document processing never completes

**Solutions**:

1. **Check Celery worker**:
   ```bash
   docker compose logs celery-worker
   ```

2. **Restart Celery**:
   ```bash
   docker compose restart celery-worker
   ```

3. **Cancel and retry**:
   - Delete document
   - Re-upload

4. **Try smaller document first**:
   - Test with 1-2 pages
   - Ensures system working

### Images Not Extracted

**Problem**: PDF images missing in processed document

**Solutions**:

1. **Check vision model configured**:
   - Need OpenAI API key OR
   - Ollama with llava model

2. **For Ollama vision**:
   ```bash
   ollama pull llava
   ```

3. **Check if PDF has extractable images**:
   - Some PDFs have embedded images
   - Some PDFs have image backgrounds (can't extract)

4. **Review logs**:
   ```bash
   docker compose logs fastapi | grep -i image
   ```

## RAG (Document Search) Issues

### No Results Found

**Problem**: RAG search returns no results

**Solutions**:

1. **Lower score threshold**:
   - Try 0.3 instead of 0.7

2. **Increase number of results**:
   - Try 10 instead of 5

3. **Rephrase question**:
   - Use keywords from document
   - Be more specific

4. **Check collection selected**:
   - Correct collection chosen?
   - Documents actually in collection?

5. **Check document processed**:
   - Go to Files page
   - Verify status is "Processed"

### Results Not Relevant

**Problem**: Search returns wrong content

**Solutions**:

1. **Increase score threshold**:
   - Try 0.7 instead of 0.3

2. **Be more specific**:
   - Add context to question
   - Use exact phrases from document

3. **Check chunking strategy**:
   - Reprocess with different strategy
   - Try section-based instead of page-based

4. **Verify embeddings**:
   - Check ChromaDB has vectors:
   ```bash
   docker compose logs chromadb
   ```

## Test Plan Generation Issues

### Generation Fails

**Problem**: Test plan generation stops with error

**Solutions**:

1. **Check model accessible**:
   - For OpenAI: Valid API key, credits available
   - For Ollama: Model downloaded, service running

2. **Check document processed**:
   - Document must be fully processed first
   - Check Files page status

3. **Try simpler analysis**:
   - Use "Quick" instead of "Deep"
   - Fewer agents

4. **Check logs**:
   ```bash
   docker compose logs fastapi | grep -i generation
   docker compose logs celery-worker
   ```

5. **Reduce document size**:
   - Try with smaller document
   - Split large documents

### Poor Quality Output

**Problem**: Generated test plan is inadequate

**Solutions**:

1. **Use better model**:
   - Switch to gpt-4o from gpt-4o-mini
   - Avoid gpt-3.5-turbo

2. **Improve source document**:
   - Ensure clear structure
   - Explicit requirements
   - No scanned images without OCR

3. **Adjust temperature**:
   - Lower for factual extraction (0.2-0.3)
   - Higher for creative tests (0.6-0.7)

4. **Use more agents**:
   - Try "Standard" or "Deep" analysis
   - Add specialized agents

5. **Iterative refinement**:
   - Review output
   - Run refinement with feedback

## Database Issues

### Cannot Connect to Database

**Problem**: PostgreSQL connection errors

**Solutions**:

```bash
# Check PostgreSQL running
docker compose ps postgres

# Check logs
docker compose logs postgres

# Restart PostgreSQL
docker compose restart postgres

# If still failing:
docker compose down postgres
docker volume rm dis_verification_genai_postgres_data
docker compose up -d postgres
# WARNING: Deletes all data!
```

### Database Full

**Problem**: "Disk quota exceeded" or similar

**Solutions**:

1. **Check disk space**:
   ```bash
   df -h
   docker system df
   ```

2. **Clean up**:
   ```bash
   # Remove unused Docker resources
   docker system prune -a
   
   # Remove old documents from app
   # Use Database Manager → Clean Up
   ```

3. **Increase allocation**:
   - Docker Desktop → Settings → Resources → Disk Size

### Vector Database Issues

**Problem**: ChromaDB errors

**Solutions**:

```bash
# Restart ChromaDB
docker compose restart chromadb

# Clear ChromaDB data
rm -rf ./chroma_data
docker compose restart chromadb
# WARNING: Deletes all vectors!

# Reprocess documents
# Go to Files page → Select documents → Reprocess
```

## Performance Issues

### System Slow

**Problem**: Everything is slow

**Solutions**:

1. **Check system resources**:
   ```bash
   # Linux
   htop
   # or
   docker stats
   ```

2. **Increase Docker resources**:
   - Docker Desktop → Settings → Resources
   - RAM: 8 GB minimum (16 GB recommended)
   - CPU: 4 cores minimum

3. **Close other applications**:
   - Free up RAM
   - Free up CPU

4. **Use faster models**:
   - gpt-4o-mini instead of gpt-4o
   - llama3.2:3b instead of llama3.1:8b

5. **Reduce concurrent tasks**:
   - Don't run multiple generations simultaneously

### High Memory Usage

**Problem**: Running out of RAM

**Solutions**:

1. **Restart services**:
   ```bash
   docker compose restart
   ```

2. **Use smaller models**:
   - llama3.2:1b or phi3:mini

3. **Reduce workers**:
   ```yaml
   # In docker-compose.yml
   celery-worker:
     command: celery worker --concurrency=2
   ```

4. **Limit cached data**:
   - Clear Redis: `docker compose exec redis redis-cli FLUSHALL`

## Getting More Help

### Collect Debug Information

Before reporting issues:

```bash
# System info
docker --version
docker compose version
uname -a  # Linux/macOS
systeminfo  # Windows

# Service status
docker compose ps

# Recent logs
docker compose logs --tail=100 > logs.txt

# Error messages (copy exact text)
```

### Report an Issue

1. GitHub Issues: [Report a Bug](https://github.com/yourusername/dis_verification_genai/issues)
2. Include:
   - Exact error message
   - Steps to reproduce
   - Debug information above
   - Screenshots if applicable

### Community Resources

- Documentation: This guide!
- FAQ: [Frequently Asked Questions](13-faq.md)
- GitHub Discussions: Ask questions
- Quick Start: [QUICKSTART.md](../../QUICKSTART.md)

---

**Still stuck?** Review the [FAQ](13-faq.md) or report an issue on GitHub.
