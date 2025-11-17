# Installer Fixes - Complete Cross-Platform Automation

## Overview

This document describes the comprehensive fixes applied to all installers (DEB, RPM, Windows MSI, macOS DMG) to address three critical issues:

1. **Source code not being installed**
2. **Environment variables not being created**
3. **Ollama models not being pulled**

## Summary of Changes

### All Installers Now:
- ✅ Include complete source code (`src/` directory with all Python modules)
- ✅ Include all scripts with proper permissions
- ✅ Run interactive environment setup wizard (`setup-env.sh` or `.ps1`)
- ✅ Offer to install Ollama for local model support
- ✅ Offer to auto-pull recommended Ollama models based on hardware
- ✅ Include verification script to check installation
- ✅ Create proper `.env` file with configured credentials

---

## 1. Debian/Ubuntu (.deb) Installer

### Files Modified:
- `installer/linux/DEBIAN/postinst` - Enhanced post-installation script
- `installer/build-local.sh` - Added verification and error handling

### New Features:

#### Post-Installation Script (`postinst`)
The DEB installer now:
1. **Automatically runs environment setup wizard** after installation
2. **Prompts to install Ollama** if not present
3. **Auto-pulls models** with GPU detection (llama3.1:8b, phi3:mini, etc.)
4. **Creates systemd service** for auto-start capability

#### Build Process
- Verifies all required files exist before copying
- Validates copied files after staging
- Ensures critical scripts are executable

### Installation Flow:
```bash
sudo dpkg -i dis-verification-genai_1.0.0_amd64.deb

# Interactive prompts:
# 1. Run environment setup? (Y/n) → Configures .env with API keys
# 2. Install Ollama? (y/N) → Downloads and installs Ollama
# 3. Pull models? (y/N) → Auto-detects GPU and pulls optimal models

sudo systemctl start dis-verification-genai
```

---

## 2. RHEL/CentOS/Fedora (.rpm) Installer

### Files Created/Modified:
- `installer/linux/rpm-postinst.sh` - New RPM post-install script
- `installer/build-local.sh` - Enhanced RPM spec file generation

### New Features:

#### RPM Spec File
The spec file now includes:
- `%post` section that runs `rpm-postinst.sh`
- `%preun` section to stop services before removal
- `%postun` section to clean up systemd service
- Complete description and metadata

#### Post-Installation
Identical functionality to DEB:
- Interactive environment setup
- Ollama installation offer
- Auto-pull models with GPU detection
- Systemd service creation

### Installation Flow:
```bash
sudo rpm -i dis-verification-genai-1.0.0.x86_64.rpm

# Same interactive prompts as DEB
# Automatically creates /opt/dis-verification-genai with all files
```

---

## 3. Windows (.msi) Installer

### Files Created/Modified:
- `installer/windows/Product.wxs` - Complete rewrite with WiX harvesting
- `installer/windows/scripts/setup-env.ps1` - PowerShell environment wizard
- `installer/windows/scripts/post-install.ps1` - PowerShell post-install automation
- `installer/windows/build-msi.ps1` - Automated MSI build script

### New Architecture:

#### WiX Installer (`Product.wxs`)
The new WiX configuration:
- Uses `heat.exe` to automatically harvest ALL files from staging directory
- Includes complete `src/` directory tree
- Includes all scripts (both .sh and .ps1 versions)
- Creates shortcuts with proper arguments
- Runs `post-install.ps1` after installation completes

#### PowerShell Setup Script (`setup-env.ps1`)
Interactive wizard that:
- Backs up existing `.env` if present
- Prompts for OpenAI API key
- Offers to configure Ollama models
- Generates secure database password
- Configures LangSmith tracing (optional)
- Creates complete `.env` file

#### PowerShell Post-Install Script (`post-install.ps1`)
Automation that:
- Checks if Docker Desktop is running
- Offers to start Docker Desktop
- Runs environment setup wizard
- Offers to download/install Ollama
- Pulls recommended models (llama3.1:8b, etc.)
- Offers to start services immediately
- Opens web interface when ready

#### Build Script (`build-msi.ps1`)
Automated build process:
1. Verifies WiX Toolset is installed
2. Creates staging directory with all source files
3. Runs `heat.exe` to harvest file tree
4. Compiles `.wxs` files with `candle.exe`
5. Links to create final `.msi` with `light.exe`

### Installation Flow:
```powershell
# Double-click dis-verification-genai-1.0.0.msi

# Installer shows GUI wizard
# After files are copied, runs post-install.ps1:

# Interactive prompts (PowerShell):
# 1. Run environment setup? (Y/n) → PowerShell wizard for .env
# 2. Install Ollama? (y/N) → Opens download page
# 3. Pull models? (y/N) → Pulls llama3.1:8b
# 4. Start now? (y/N) → Launches Docker Compose + opens browser

# Creates shortcuts:
# - Start Menu > DIS Verification GenAI
# - Start Menu > Configure Environment
# - Start Menu > Stop Services
```

### Building Windows Installer:
```powershell
cd installer\windows
.\build-msi.ps1

# Output: dist\dis-verification-genai-1.0.0.msi
```

---

## 4. macOS (.dmg) Installer

### Files Modified:
- `installer/build-local.sh` - Enhanced launcher scripts in DMG

### New Features:

#### Smart Launcher Script
The macOS launcher now:
1. **Checks if `.env` exists** on first launch
2. **Opens Terminal with setup wizard** if not configured
3. **Verifies Docker is running** before starting services
4. **Prompts to start Docker** if not running
5. **Auto-starts services** and opens browser

#### Setup Script Launcher
Added dedicated "Setup" script that:
- Opens Terminal with environment setup wizard
- Guides through API key configuration
- Configures database and services

### Installation Flow:
```bash
# Open dis-verification-genai-1.0.0.dmg
# Drag "DIS Verification GenAI.app" to Applications

# First launch:
# - Opens Terminal with setup wizard
# - Configures .env file
# - Ready to use

# Subsequent launches:
# - Checks Docker is running
# - Starts services automatically
# - Opens http://localhost:8501
```

---

## New Scripts for All Platforms

### 1. Installation Verification Script
**Location:** `scripts/verify-installation.sh`

Comprehensive check that verifies:
- ✅ Installation directory exists
- ✅ All source code files present
- ✅ Environment configured (.env file)
- ✅ Docker and Docker Compose installed
- ✅ Ollama installed (optional)
- ✅ Models pulled (optional)
- ✅ Systemd service configured (Linux)
- ✅ Containers running
- ✅ Network ports accessible

**Usage:**
```bash
# Linux
sudo /opt/dis-verification-genai/scripts/verify-installation.sh

# macOS
cd "/Applications/DIS Verification GenAI.app/Contents/Resources"
./scripts/verify-installation.sh

# Windows (WSL/Git Bash)
cd "C:\Program Files\DIS Verification GenAI"
bash scripts/verify-installation.sh
```

### 2. Environment Setup Script
**Location:**
- Linux/macOS: `scripts/setup-env.sh`
- Windows: `installer/windows/scripts/setup-env.ps1`

Interactive wizard for:
- OpenAI API key configuration
- Ollama model selection
- Database password generation
- LangSmith tracing setup

Can be re-run anytime to reconfigure.

---

## File Manifest - What Gets Installed

All installers now include:

### Application Code
```
/opt/dis-verification-genai/  (or C:\Program Files\DIS Verification GenAI\)
├── src/
│   ├── fastapi/           # Complete FastAPI backend
│   │   ├── api/
│   │   ├── db/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── tasks/
│   ├── streamlit/         # Complete Streamlit UI
│   │   └── components/
│   └── llm_config/        # LLM configuration
```

### Scripts
```
├── scripts/
│   ├── setup-env.sh                # Environment configuration wizard (Linux/macOS)
│   ├── setup-env.ps1               # Environment configuration wizard (Windows)
│   ├── verify-installation.sh      # Installation verification
│   ├── install-ollama.sh           # Ollama installer
│   ├── pull-ollama-models.sh       # Model downloader with GPU detection
│   ├── start.sh                    # Service starter
│   ├── stop.sh                     # Service stopper
│   ├── backup.sh                   # Database backup
│   ├── restore.sh                  # Database restore
│   └── validation.sh               # System validation
```

### Configuration Files
```
├── docker-compose.yml              # Docker orchestration
├── .env                            # Environment variables (configured during install)
├── .env.template                   # Template for reference
├── VERSION                         # Version number
├── README.md                       # User documentation
├── INSTALL.md                      # Installation guide
└── CHANGELOG.md                    # Version history
```

---

## Upgrade Path for Existing Installations

If you already installed a version without these fixes:

### Option 1: Reinstall
```bash
# Linux (DEB)
sudo dpkg --purge dis-verification-genai
sudo dpkg -i dis-verification-genai_1.0.0_amd64.deb

# Linux (RPM)
sudo rpm -e dis-verification-genai
sudo rpm -i dis-verification-genai-1.0.0.x86_64.rpm

# Windows
# Uninstall via "Add or Remove Programs"
# Install new MSI

# macOS
# Delete app from Applications
# Install new DMG
```

### Option 2: Manual Fix for Existing Installation

If you want to keep your current installation:

```bash
# Clone the repository to get the latest scripts
git clone https://github.com/martinmanuel9/dis_verification_genai.git /tmp/genai

# Copy missing files to installation
sudo cp -r /tmp/genai/src/* /opt/dis-verification-genai/src/
sudo cp -r /tmp/genai/scripts/* /opt/dis-verification-genai/scripts/

# Run setup wizard
sudo /opt/dis-verification-genai/scripts/setup-env.sh

# Optional: Install Ollama and pull models
sudo /opt/dis-verification-genai/scripts/install-ollama.sh
/opt/dis-verification-genai/scripts/pull-ollama-models.sh auto
```

---

## Building All Installers

### Prerequisites
- **Linux:** `dpkg-deb`, `rpmbuild` (for RPM)
- **macOS:** `hdiutil` (built-in)
- **Windows:** WiX Toolset 3.11+

### Build Commands

```bash
# Build all on Linux
cd /path/to/dis_verification_genai
./installer/build-local.sh all

# Build DEB only
./installer/build-local.sh deb

# Build RPM only
./installer/build-local.sh rpm

# Build macOS DMG (on macOS only)
./installer/build-local.sh dmg
```

```powershell
# Build Windows MSI (on Windows only)
cd installer\windows
.\build-msi.ps1
```

### Output
All installers are created in `dist/`:
- `dist/dis-verification-genai_1.0.0_amd64.deb`
- `dist/dis-verification-genai-1.0.0.x86_64.rpm`
- `dist/dis-verification-genai-1.0.0.dmg`
- `dist/dis-verification-genai-1.0.0.msi`

---

## Testing Checklist

### After Installation, Verify:

#### ✅ Source Code
```bash
# Should see Python files
ls /opt/dis-verification-genai/src/fastapi/
ls /opt/dis-verification-genai/src/streamlit/
```

#### ✅ Environment Variables
```bash
# Should show configured values
cat /opt/dis-verification-genai/.env | grep OPENAI_API_KEY
cat /opt/dis-verification-genai/.env | grep DB_PASSWORD
```

#### ✅ Ollama Models (if installed)
```bash
ollama list
# Should show: llama3.1:8b, snowflake-arctic-embed2, etc.
```

#### ✅ Services Running
```bash
# Linux
sudo systemctl status dis-verification-genai
docker compose ps

# Windows/macOS
docker compose ps
```

#### ✅ Web Interface
```bash
curl http://localhost:8501
# Should return HTML

curl http://localhost:9020/health
# Should return {"status":"ok"}
```

---

## Troubleshooting

### Source code missing after install
**Symptom:** `/opt/dis-verification-genai/src/` is empty or missing

**Solution:**
```bash
# Rebuild installer with verification
./installer/build-local.sh deb

# Or manually copy from repository
sudo cp -r src /opt/dis-verification-genai/
```

### Environment not configured
**Symptom:** `.env` file is empty or has placeholders

**Solution:**
```bash
sudo /opt/dis-verification-genai/scripts/setup-env.sh
```

### Ollama models not pulled
**Symptom:** `ollama list` shows no models

**Solution:**
```bash
/opt/dis-verification-genai/scripts/pull-ollama-models.sh auto
```

### Windows post-install script doesn't run
**Symptom:** No prompts after MSI installation

**Solution:**
```powershell
# Run manually
cd "C:\Program Files\DIS Verification GenAI"
powershell -ExecutionPolicy Bypass -File scripts\post-install.ps1
```

---

## Summary

All installers now provide:
- **Complete installation** - All source code, scripts, and dependencies
- **Automated setup** - Interactive wizards for configuration
- **Ollama integration** - Optional local model support with auto-pull
- **Verification tools** - Scripts to validate installation
- **Cross-platform parity** - Same experience on Linux, Windows, macOS

The installation process is now fully automated from download to first use, with no manual file copying or environment configuration required.
