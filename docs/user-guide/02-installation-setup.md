# Installation & Setup Guide

This comprehensive guide covers all installation methods and configuration options for DIS Verification GenAI.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation Methods](#installation-methods)
3. [Package Installer Installation (Recommended)](#package-installer-installation-recommended)
4. [Manual Docker Installation](#manual-docker-installation)
5. [Configuration](#configuration)
6. [Verification](#verification)
7. [Advanced Setup](#advanced-setup)
8. [Troubleshooting Installation](#troubleshooting-installation)

## System Requirements

### Minimum Requirements

| Component | Requirement |
|-----------|-------------|
| **CPU** | 4 cores (x86_64 architecture) |
| **RAM** | 8 GB (16 GB recommended) |
| **Storage** | 50 GB available disk space |
| **OS** | Windows 10/11, macOS 11+, Ubuntu 20.04+, RHEL 8+ |
| **Docker** | Docker 24.0.0+ |
| **Docker Compose** | Docker Compose 2.20.0+ |

### Recommended Requirements

| Component | Recommendation |
|-----------|----------------|
| **CPU** | 8+ cores with AVX2 support |
| **RAM** | 16-32 GB |
| **Storage** | 100 GB SSD |
| **GPU** | NVIDIA GPU with 8GB+ VRAM (for Ollama) |
| **Network** | Stable internet connection (for OpenAI models) |

### Operating System Support

#### Windows
- ✅ Windows 10 (64-bit, build 1809+)
- ✅ Windows 11 (64-bit)
- ✅ Windows Server 2019/2022
- **Package Format**: MSI installer

#### macOS
- ✅ macOS 11 (Big Sur)
- ✅ macOS 12 (Monterey)
- ✅ macOS 13 (Ventura)
- ✅ macOS 14 (Sonoma)
- ✅ macOS 15 (Sequoia)
- **Package Format**: DMG installer
- **Architecture**: Intel (x86_64) and Apple Silicon (arm64)

#### Linux
- ✅ Ubuntu 20.04, 22.04, 24.04 LTS
- ✅ Debian 11, 12
- ✅ RHEL 8, 9
- ✅ CentOS Stream 8, 9
- ✅ Fedora 35+
- ✅ Rocky Linux 8, 9
- ✅ AlmaLinux 8, 9
- **Package Formats**: DEB (Debian/Ubuntu) and RPM (RHEL/Fedora)

## Installation Methods

DIS Verification GenAI offers three installation methods:

| Method | Best For | Difficulty | Time |
|--------|----------|------------|------|
| **Package Installer** | End users, production | Easy | 5-10 min |
| **Manual Docker** | Developers, customization | Medium | 15-30 min |
| **Source Build** | Contributors, advanced users | Hard | 30-60 min |

## Package Installer Installation (Recommended)

The easiest way to install DIS Verification GenAI with fully automated setup.

### Step 1: Download the Installer

1. Visit the [GitHub Releases](https://github.com/yourusername/dis_verification_genai/releases) page
2. Download the appropriate installer for your platform:
   - **Windows**: `DIS-Verification-GenAI-1.0.7-win64.msi`
   - **macOS**: `DIS-Verification-GenAI-1.0.7.dmg`
   - **Linux (Debian/Ubuntu)**: `dis-verification-genai_1.0.7_amd64.deb`
   - **Linux (RHEL/Fedora)**: `dis-verification-genai-1.0.7-1.x86_64.rpm`

[Screenshot: GitHub releases page with download options]

### Step 2: Run the Installer

#### Windows Installation

1. **Run the MSI installer**
   - Double-click `DIS-Verification-GenAI-1.0.7-win64.msi`
   - Click **Yes** on the User Account Control prompt

[Screenshot: Windows installer welcome screen]

2. **Follow the Installation Wizard**
   - Click **Next** on the welcome screen
   - Accept the license agreement
   - Choose installation directory (default: `C:\Program Files\DIS Verification GenAI`)
   - Click **Install**

[Screenshot: Windows installation progress]

3. **Wait for Automated Setup**
   The installer will automatically:
   - ✓ Install application files
   - ✓ Check Docker Desktop installation
   - ✓ Install Ollama (if selected)
   - ✓ Pull required Ollama models
   - ✓ Generate `.env` configuration file
   - ✓ Start Docker services
   - ✓ Create Start Menu shortcuts

[Screenshot: Automated setup progress]

4. **Complete Installation**
   - Click **Finish**
   - The application will launch automatically

**Post-Installation:**
- **Start Menu**: Look for "DIS Verification GenAI"
- **Desktop**: Shortcut created automatically
- **Uninstall**: Via Windows Settings > Apps

#### macOS Installation

1. **Mount the DMG**
   - Double-click `DIS-Verification-GenAI-1.0.7.dmg`
   - A new window will open

[Screenshot: macOS DMG window]

2. **Install the Application**
   - Drag the **DIS Verification GenAI** icon to the **Applications** folder
   - Wait for the copy to complete

3. **First Launch**
   - Open **Applications** folder
   - Double-click **DIS Verification GenAI**
   - Click **Open** when macOS asks for confirmation (first launch only)

[Screenshot: macOS security prompt]

4. **Automated Setup Runs**
   - The setup script will run in Terminal
   - Follow any prompts for Docker, Ollama installation
   - Enter your password if requested (for system dependencies)

[Screenshot: macOS Terminal setup]

5. **Access the Application**
   - Browser will open automatically to `http://localhost:8501`

**Post-Installation:**
- **Launchpad**: Look for "DIS Verification GenAI"
- **Applications Folder**: Standard macOS app
- **Uninstall**: Drag to Trash from Applications folder

#### Linux Installation (Debian/Ubuntu)

1. **Install the DEB package**
   ```bash
   # Download the package
   wget https://github.com/yourusername/dis_verification_genai/releases/download/v1.0.7/dis-verification-genai_1.0.7_amd64.deb

   # Install with dpkg
   sudo dpkg -i dis-verification-genai_1.0.7_amd64.deb

   # Fix dependencies if needed
   sudo apt-get install -f
   ```

[Screenshot: Terminal showing installation progress]

2. **Run Post-Install Setup**
   The package automatically runs setup scripts that:
   - ✓ Install Docker and Docker Compose (if needed)
   - ✓ Configure Docker permissions
   - ✓ Install Ollama (optional)
   - ✓ Generate configuration files
   - ✓ Start services

3. **Start the Application**
   ```bash
   # Start all services
   dis-verification-genai start

   # Or use the desktop launcher
   # Look in Applications menu under "Development"
   ```

**Post-Installation:**
- **Installed to**: `/opt/dis-verification-genai`
- **Config**: `~/.config/dis-verification-genai/`
- **Data**: `~/.local/share/dis-verification-genai/`
- **Uninstall**: `sudo apt remove dis-verification-genai`

#### Linux Installation (RHEL/Fedora/CentOS)

1. **Install the RPM package**
   ```bash
   # Download the package
   wget https://github.com/yourusername/dis_verification_genai/releases/download/v1.0.7/dis-verification-genai-1.0.7-1.x86_64.rpm

   # Install with dnf (Fedora) or yum (RHEL/CentOS)
   sudo dnf install dis-verification-genai-1.0.7-1.x86_64.rpm
   # OR
   sudo yum install dis-verification-genai-1.0.7-1.x86_64.rpm
   ```

2. **Complete Setup**
   Follow the same steps as Debian/Ubuntu above

**Post-Installation:**
- **Installed to**: `/opt/dis-verification-genai`
- **Uninstall**: `sudo dnf remove dis-verification-genai`

## Manual Docker Installation

For developers or users who want more control over the installation.

### Step 1: Install Prerequisites

#### Install Docker

**Windows:**
1. Download [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
2. Run the installer
3. Restart your computer
4. Verify: `docker --version` in PowerShell

**macOS:**
1. Download [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)
2. Drag to Applications
3. Launch Docker Desktop
4. Verify: `docker --version` in Terminal

**Linux:**
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker

# Verify
docker --version
docker compose version
```

#### Install Git

```bash
# Windows (via winget)
winget install Git.Git

# macOS
brew install git

# Linux
sudo apt-get install git  # Debian/Ubuntu
sudo dnf install git      # Fedora/RHEL
```

### Step 2: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/dis_verification_genai.git
cd dis_verification_genai

# Checkout the latest stable version
git checkout v1.0.7
```

### Step 3: Run Setup Script

The setup script will guide you through configuration:

**Linux/macOS:**
```bash
chmod +x scripts/setup-env.sh
./scripts/setup-env.sh
```

**Windows:**
```powershell
# Use Git Bash or WSL
bash scripts/setup-env.sh
```

[Screenshot: Setup script interactive prompts]

The script will ask:

1. **OpenAI API Key** (optional)
   - Enter your key or press Enter to skip
   - Get a key from: https://platform.openai.com/api-keys

2. **Install Ollama?** (recommended for local models)
   - `y` to install automatically
   - `n` if you'll install manually

3. **Pull Ollama Models?** (if Ollama is installed)
   - `y` to download models now
   - `n` to download later

4. **GPU Acceleration?** (Linux only with NVIDIA GPU)
   - `y` if you have NVIDIA GPU with drivers installed
   - `n` for CPU-only mode

### Step 4: Review Configuration

The setup script creates a `.env` file. Review and customize if needed:

```bash
# Edit the configuration
nano .env
# or
vim .env
```

Key settings (see [Configuration](#configuration) section below for details).

### Step 5: Start the Application

```bash
# Start all services in detached mode
docker compose up -d

# Watch the logs (optional)
docker compose logs -f
```

[Screenshot: Docker Compose startup logs]

### Step 6: Verify Installation

```bash
# Check service status
docker compose ps

# Should show all services as "running"
```

Access the application at: `http://localhost:8501`

## Configuration

### Environment Variables (.env file)

The `.env` file contains all configuration. Here are the key variables:

#### AI Model Configuration

```bash
# OpenAI API Key (required for GPT models)
OPENAI_API_KEY=sk-your-api-key-here

# Ollama Configuration (for local models)
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_ENABLED=true

# LangSmith Tracing (optional - for debugging)
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=your-langsmith-key
LANGCHAIN_PROJECT=dis-verification-genai
```

#### Database Configuration

```bash
# PostgreSQL
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-secure-password-here
POSTGRES_DB=dis_verification_db
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# ChromaDB (Vector Database)
CHROMA_HOST=chromadb
CHROMA_PORT=8000
CHROMA_PERSIST_DIRECTORY=./chroma_data

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
```

#### Application Configuration

```bash
# API Configuration
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=9020
API_URL=http://fastapi:9020

# Streamlit Configuration
STREAMLIT_PORT=8501

# Celery Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

#### Security Configuration

```bash
# Security Settings
SECRET_KEY=your-secret-key-here-change-this
ALLOWED_ORIGINS=http://localhost:8501,http://localhost:9020

# File Upload Limits
MAX_UPLOAD_SIZE=100  # MB
```

### Ollama Model Configuration

Ollama models are configured in `src/llm_config/llm_config.py`. Available US-based models:

```python
OLLAMA_MODELS = {
    "llama3.2:1b": "Meta (California) - 1B parameters",
    "llama3.2:3b": "Meta (California) - 3B parameters",
    "llama3.1:8b": "Meta (California) - 8B parameters (Recommended)",
    "phi3:mini": "Microsoft (Washington) - 3.8B parameters",
}
```

To pull all models:
```bash
./scripts/pull-ollama-models.sh
```

### Docker Compose Configuration

Customize `docker-compose.yml` for advanced scenarios:

**Enable GPU for Ollama (Linux with NVIDIA GPU):**
```yaml
# Uncomment in docker-compose.yml
services:
  # ... other services ...
  # Ollama runs on host for GPU access
  # See docker-compose.yml for configuration
```

**Adjust Resource Limits:**
```yaml
services:
  fastapi:
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
        reservations:
          cpus: '2.0'
          memory: 4G
```

**Port Conflicts:**
If default ports are in use, modify:
```yaml
services:
  streamlit:
    ports:
      - "8502:8501"  # Change host port
```

## Verification

### Verify All Services Are Running

```bash
# Check Docker containers
docker compose ps

# Expected output: All services "Up" and "healthy"
NAME                STATUS
streamlit           Up (healthy)
fastapi             Up (healthy)
postgres            Up (healthy)
chromadb            Up (healthy)
redis               Up (healthy)
celery-worker       Up
```

### Test Web Interface

1. Open browser to `http://localhost:8501`
2. Check sidebar health status - all should be 🟢 green
3. Try sending a chat message

[Screenshot: Healthy application interface]

### Test API Directly

```bash
# Test FastAPI health endpoint
curl http://localhost:9020/health

# Expected response:
{
  "status": "healthy",
  "version": "1.0.7",
  "services": {
    "postgres": "healthy",
    "chromadb": "healthy",
    "redis": "healthy"
  }
}
```

### Test Ollama (if installed)

```bash
# Check Ollama is running
ollama list

# Test a model
ollama run llama3.1:8b "Hello, how are you?"
```

## Advanced Setup

### Installing Additional Ollama Models

```bash
# Pull specific models
ollama pull llama3.1:8b
ollama pull phi3:mini

# List installed models
ollama list
```

### Configuring GPU Acceleration

**For NVIDIA GPUs on Linux:**

1. Install NVIDIA Container Toolkit:
   ```bash
   distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
   curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
   curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

   sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
   sudo systemctl restart docker
   ```

2. Verify GPU is detected:
   ```bash
   docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
   ```

3. Ollama will automatically use GPU when available

### Setting Up Development Environment

For developers who want to modify the code:

```bash
# Install Python dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run linting
ruff check .
black --check .
mypy .
```

### Configuring Reverse Proxy

For production deployments behind nginx or Apache:

**Nginx Configuration:**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://localhost:9020;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Backup and Restore

**Backup Data:**
```bash
# Backup PostgreSQL database
docker compose exec postgres pg_dump -U postgres dis_verification_db > backup.sql

# Backup ChromaDB data
tar -czf chroma_backup.tar.gz ./chroma_data

# Backup configuration
cp .env env_backup
```

**Restore Data:**
```bash
# Restore PostgreSQL
docker compose exec -T postgres psql -U postgres dis_verification_db < backup.sql

# Restore ChromaDB
tar -xzf chroma_backup.tar.gz

# Restore configuration
cp env_backup .env
```

## Troubleshooting Installation

### Docker Issues

**Problem: "Cannot connect to Docker daemon"**
```bash
# Linux: Ensure Docker service is running
sudo systemctl start docker

# Ensure user is in docker group
sudo usermod -aG docker $USER
newgrp docker

# Windows/macOS: Start Docker Desktop
```

**Problem: Port already in use**
```bash
# Find what's using the port
sudo lsof -i :8501  # Linux/macOS
netstat -ano | findstr :8501  # Windows

# Either stop the conflicting service or change ports in docker-compose.yml
```

### Ollama Issues

**Problem: "Ollama not found"**
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Or download from: https://ollama.com/download
```

**Problem: Models downloading very slowly**
```bash
# Use multiple concurrent downloads
OLLAMA_MAX_LOADED_MODELS=3 ./scripts/pull-ollama-models.sh
```

### Permission Issues

**Linux: Docker permission denied**
```bash
sudo usermod -aG docker $USER
newgrp docker
```

**macOS: "App is damaged and can't be opened"**
```bash
# Remove quarantine attribute
xattr -d com.apple.quarantine "/Applications/DIS Verification GenAI.app"
```

### Database Issues

**Problem: PostgreSQL fails to start**
```bash
# Check logs
docker compose logs postgres

# Reset database (WARNING: Deletes all data)
docker compose down -v
docker compose up -d
```

**Problem: ChromaDB connection errors**
```bash
# Restart ChromaDB service
docker compose restart chromadb

# Check ChromaDB logs
docker compose logs chromadb
```

### Memory Issues

**Problem: Out of memory errors**

1. Increase Docker memory limit:
   - Docker Desktop → Settings → Resources → Memory → Increase to 8GB+

2. Use smaller models:
   - Switch from `llama3.1:8b` to `llama3.2:3b` or `phi3:mini`

3. Reduce concurrent workers:
   ```yaml
   # In docker-compose.yml
   celery-worker:
     command: celery -A src.fastapi.celery_app worker --concurrency=2
   ```

### Installation Logs

**View installer logs:**

- **Windows**: `%TEMP%\DIS-Verification-GenAI-Setup.log`
- **macOS**: `~/Library/Logs/DIS-Verification-GenAI/install.log`
- **Linux**: `/var/log/dis-verification-genai/install.log`

## Next Steps

After successful installation:

1. **Get Started**: [Getting Started Guide](01-getting-started.md)
2. **Learn the Interface**: [UI Overview](03-ui-overview.md)
3. **Upload Documents**: [Document Management](05-document-management.md)
4. **Generate Test Plans**: [Document Generator](06-document-generator.md)

## Support

If you continue to have installation issues:

- **Check the FAQ**: [Frequently Asked Questions](13-faq.md)
- **Troubleshooting Guide**: [Troubleshooting](12-troubleshooting.md)
- **GitHub Issues**: Report problems at the issue tracker
- **Logs**: Always include relevant logs when reporting issues

---

**Successfully installed?** Head to the [Getting Started Guide](01-getting-started.md) to start using the application!
