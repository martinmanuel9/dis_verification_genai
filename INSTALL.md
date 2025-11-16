# Installation Guide

## Table of Contents
- [System Requirements](#system-requirements)
- [Quick Start](#quick-start)
- [Windows Installation](#windows-installation)
- [Linux Installation](#linux-installation)
- [macOS Installation](#macos-installation)
- [Post-Installation Configuration](#post-installation-configuration)
- [Updating](#updating)
- [Uninstallation](#uninstallation)
- [Troubleshooting](#troubleshooting)

## System Requirements

### Minimum Requirements
- **CPU:** 4 cores
- **RAM:** 8 GB
- **Disk Space:** 50 GB available
- **Operating Systems:**
  - Windows 10/11 (64-bit)
  - Ubuntu 20.04+ / Debian 11+
  - RHEL 8+ / CentOS 8+ / Fedora 35+
  - macOS 11 (Big Sur) or later

### Required Software
- **Docker:** 24.0.0 or later
- **Docker Compose:** 2.20.0 or later

### Optional (for local model support)
- **Ollama:** Latest version
- **NVIDIA GPU:** For accelerated inference (optional)
- **NVIDIA Docker:** For GPU support in containers

## Quick Start

### 1. Download Installer

Download the appropriate installer for your operating system from the [Releases](https://github.com/martinmanuel9/dis_verification_genai/releases) page:

- **Windows:** `dis-verification-genai-{version}.msi`
- **Ubuntu/Debian:** `dis-verification-genai_{version}_amd64.deb`
- **RHEL/CentOS/Fedora:** `dis-verification-genai-{version}.x86_64.rpm`
- **macOS:** `dis-verification-genai-{version}.dmg`

### 2. Verify Download (Optional but Recommended)

```bash
# Download checksums file
wget https://github.com/martinmanuel9/dis_verification_genai/releases/download/v{version}/checksums-sha256.txt

# Verify checksum
sha256sum -c checksums-sha256.txt --ignore-missing
```

### 3. Install

Follow the platform-specific instructions below.

---

## Windows Installation

### Prerequisites

1. **Install Docker Desktop for Windows**
   - Download from: https://www.docker.com/products/docker-desktop
   - Minimum version: 24.0.0
   - Ensure WSL 2 is enabled

2. **Verify Docker is Running**
   ```powershell
   docker --version
   docker compose version
   ```

### Installation Steps

1. **Run Prerequisites Check (Optional)**
   ```powershell
   # Download and run the check script
   .\installer\windows\scripts\check_prerequisites.ps1
   ```

2. **Install via MSI**
   - Double-click `dis-verification-genai-{version}.msi`
   - Follow the installation wizard
   - Choose installation directory (default: `C:\Program Files\DIS Verification GenAI`)
   - Optionally create desktop shortcut

3. **Configure Environment**
   - Navigate to installation directory
   - Copy `.env.template` to `.env`
   - Edit `.env` with your API keys:
     ```
     OPENAI_API_KEY=your-key-here
     ```

4. **Start Services**
   ```powershell
   cd "C:\Program Files\DIS Verification GenAI"
   docker compose up -d
   ```

5. **Access Web Interface**
   - Open browser to: http://localhost:8501

### Post-Installation (Windows)

**Create Desktop Shortcut:**
The installer creates shortcuts in:
- Start Menu: `DIS Verification GenAI`
- Desktop: `DIS Verification GenAI` (if selected)

**Enable Auto-Start (Optional):**
```powershell
# Create scheduled task to start on login
schtasks /create /tn "DIS Verification GenAI" /tr "docker compose -f 'C:\Program Files\DIS Verification GenAI\docker-compose.yml' up -d" /sc onlogon
```

---

## Linux Installation

### Debian/Ubuntu

#### Prerequisites

1. **Install Docker**
   ```bash
   # Add Docker's official GPG key
   sudo apt-get update
   sudo apt-get install ca-certificates curl
   sudo install -m 0755 -d /etc/apt/keyrings
   sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
   sudo chmod a+r /etc/apt/keyrings/docker.asc

   # Add Docker repository
   echo \
     "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
     $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
     sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

   # Install Docker
   sudo apt-get update
   sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
   ```

2. **Verify Docker**
   ```bash
   sudo docker --version
   sudo docker compose version
   ```

#### Installation Steps

1. **Run Prerequisites Check**
   ```bash
   chmod +x installer/scripts/check_prerequisites.sh
   ./installer/scripts/check_prerequisites.sh
   ```

2. **Install DEB Package**
   ```bash
   sudo dpkg -i dis-verification-genai_{version}_amd64.deb
   # Install any missing dependencies
   sudo apt-get install -f
   ```

3. **Configure Environment**
   ```bash
   sudo /opt/dis-verification-genai/scripts/setup-env.sh
   ```

4. **Start Services**
   ```bash
   sudo systemctl start dis-verification-genai
   sudo systemctl status dis-verification-genai
   ```

5. **Enable Auto-Start (Optional)**
   ```bash
   sudo systemctl enable dis-verification-genai
   ```

6. **Access Web Interface**
   - Open browser to: http://localhost:8501

### RHEL/CentOS/Fedora

#### Prerequisites

1. **Install Docker**
   ```bash
   # Add Docker repository
   sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo

   # Install Docker
   sudo dnf install docker-ce docker-ce-cli containerd.io docker-compose-plugin

   # Start Docker
   sudo systemctl start docker
   sudo systemctl enable docker
   ```

#### Installation Steps

1. **Install RPM Package**
   ```bash
   sudo rpm -i dis-verification-genai-{version}.x86_64.rpm
   ```

2. **Follow Post-Install Steps**
   Same as Debian/Ubuntu steps 3-6 above.

---

## macOS Installation

### Prerequisites

1. **Install Docker Desktop for Mac**
   - Download from: https://www.docker.com/products/docker-desktop
   - Minimum version: 24.0.0
   - Install and start Docker Desktop

2. **Verify Docker**
   ```bash
   docker --version
   docker compose version
   ```

### Installation Steps

1. **Run Prerequisites Check**
   ```bash
   chmod +x installer/scripts/check_prerequisites.sh
   ./installer/scripts/check_prerequisites.sh
   ```

2. **Install DMG**
   - Open `dis-verification-genai-{version}.dmg`
   - Drag `DIS Verification GenAI.app` to Applications folder
   - Eject DMG

3. **Configure Environment**
   ```bash
   # Open terminal in application directory
   cd "/Applications/DIS Verification GenAI.app/Contents/Resources"

   # Run setup wizard
   ./scripts/setup-env.sh
   ```

4. **Start Application**
   - Double-click `DIS Verification GenAI.app` in Applications
   - Or via terminal:
     ```bash
     cd "/Applications/DIS Verification GenAI.app/Contents/Resources"
     docker compose up -d
     ```

5. **Access Web Interface**
   - Open browser to: http://localhost:8501

---

## Post-Installation Configuration

### 1. Configure API Keys

Edit the `.env` file in your installation directory:

#### For Cloud Models (OpenAI)
```bash
OPENAI_API_KEY=sk-...your-key-here
```

#### For LangSmith Tracing (Optional)
```bash
LANGCHAIN_API_KEY=lsv2_pt_...your-key-here
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=your-project-name
```

### 2. Install Ollama for Local Models (Optional)

**Linux:**
```bash
sudo /opt/dis-verification-genai/scripts/install-ollama.sh
```

**macOS:**
```bash
brew install ollama
# Or download from https://ollama.com/download/mac
```

**Windows:**
- Download from: https://ollama.com/download/windows
- Install and start Ollama

### 3. Pull Recommended Models

**Auto-detect GPU and pull optimal models:**
```bash
# Linux/macOS
/opt/dis-verification-genai/scripts/pull-ollama-models.sh auto

# Windows
cd "C:\Program Files\DIS Verification GenAI\scripts"
.\pull-ollama-models.sh auto
```

**Or manually pull specific models:**
```bash
ollama pull llama3.1:8b
ollama pull llama3.2:3b
ollama pull phi3:mini
ollama pull snowflake-arctic-embed2
```

### 4. Verify Installation

**Check all services are running:**
```bash
# Linux/macOS
docker compose ps

# Windows
cd "C:\Program Files\DIS Verification GenAI"
docker compose ps
```

You should see 6 services running:
- `fastapi` - REST API backend
- `streamlit` - Web UI
- `postgres` - Database
- `chromadb` - Vector store
- `redis` - Cache
- `celery-worker` - Background tasks

**Test the web interface:**
- Navigate to: http://localhost:8501
- You should see the DIS Verification GenAI home page

---

## Updating

### Check Current Version

**Linux:**
```bash
cat /opt/dis-verification-genai/VERSION
```

**Windows:**
```powershell
Get-Content "C:\Program Files\DIS Verification GenAI\VERSION"
```

**macOS:**
```bash
cat "/Applications/DIS Verification GenAI.app/Contents/Resources/VERSION"
```

### Update to New Version

1. **Stop Current Services**
   ```bash
   # Linux
   sudo systemctl stop dis-verification-genai

   # Windows/macOS
   docker compose down
   ```

2. **Backup Data (Recommended)**
   ```bash
   # Linux
   sudo cp -r /var/lib/dis-verification-genai /var/lib/dis-verification-genai.backup

   # Windows
   docker compose exec postgres pg_dump -U g3nA1-user rag_memory > backup.sql

   # macOS
   docker compose exec postgres pg_dump -U g3nA1-user rag_memory > backup.sql
   ```

3. **Install New Version**
   - Download new installer
   - Install over existing installation
   - Installer will preserve your `.env` configuration and data

4. **Restart Services**
   ```bash
   # Linux
   sudo systemctl start dis-verification-genai

   # Windows/macOS
   docker compose up -d
   ```

---

## Uninstallation

### Windows

1. **Stop Services**
   ```powershell
   cd "C:\Program Files\DIS Verification GenAI"
   docker compose down
   ```

2. **Uninstall via Control Panel**
   - Open "Add or Remove Programs"
   - Find "DIS Verification GenAI"
   - Click "Uninstall"

3. **Remove Data (Optional)**
   ```powershell
   # Remove Docker volumes
   docker volume rm genai_postgres_data genai_chroma_data genai_hf_cache genai_redis_data
   ```

### Linux

1. **Stop Services**
   ```bash
   sudo systemctl stop dis-verification-genai
   sudo systemctl disable dis-verification-genai
   ```

2. **Uninstall Package**
   ```bash
   # Debian/Ubuntu
   sudo dpkg --purge dis-verification-genai

   # RHEL/CentOS/Fedora
   sudo rpm -e dis-verification-genai
   ```

3. **Remove Data (If Prompted)**
   The uninstaller will ask if you want to remove data at `/var/lib/dis-verification-genai`

### macOS

1. **Stop Services**
   ```bash
   cd "/Applications/DIS Verification GenAI.app/Contents/Resources"
   docker compose down
   ```

2. **Remove Application**
   - Drag `DIS Verification GenAI.app` to Trash
   - Empty Trash

3. **Remove Data (Optional)**
   ```bash
   rm -rf ~/Library/Application\ Support/DIS\ Verification\ GenAI
   docker volume rm genai_postgres_data genai_chroma_data genai_hf_cache genai_redis_data
   ```

---

## Troubleshooting

### Services Won't Start

**Check Docker is running:**
```bash
docker info
```

**Check port conflicts:**
```bash
# Linux/macOS
sudo lsof -i :8501
sudo lsof -i :9020

# Windows
netstat -ano | findstr :8501
netstat -ano | findstr :9020
```

**View service logs:**
```bash
docker compose logs -f
```

### Can't Access Web Interface

1. **Verify services are running:**
   ```bash
   docker compose ps
   ```

2. **Check Streamlit logs:**
   ```bash
   docker compose logs streamlit
   ```

3. **Try accessing directly:**
   ```bash
   curl http://localhost:8501
   ```

### Database Connection Errors

**Check PostgreSQL is running:**
```bash
docker compose ps postgres
docker compose logs postgres
```

**Verify credentials in `.env`:**
```bash
grep DB_PASSWORD .env
```

### Ollama Models Not Available

1. **Check Ollama is running:**
   ```bash
   curl http://localhost:11434/api/tags
   ```

2. **Verify Ollama configuration:**
   ```bash
   # Linux
   sudo systemctl status ollama

   # Check listening address
   ps aux | grep ollama
   ```

3. **Pull models if missing:**
   ```bash
   ./scripts/pull-ollama-models.sh auto
   ```

### Permission Denied Errors (Linux)

**Add user to docker group:**
```bash
sudo usermod -aG docker $USER
# Log out and back in for changes to take effect
```

### Out of Disk Space

**Check disk usage:**
```bash
df -h
docker system df
```

**Clean up Docker:**
```bash
docker system prune -a --volumes
```

### Get Help

- **Documentation:** https://github.com/martinmanuel9/dis_verification_genai
- **Issues:** https://github.com/martinmanuel9/dis_verification_genai/issues
- **Email:** support@example.com

---

## Next Steps

After successful installation:

1. **Read the User Guide:** See `README.md` for feature documentation
2. **Upload Test Documents:** Use the Upload Documents tab
3. **Generate Test Plans:** Navigate to Document Generator
4. **Explore AI Features:** Try AI Simulation and Chat
5. **Configure Models:** Select between cloud and local models based on your needs

Enjoy using DIS Verification GenAI!
