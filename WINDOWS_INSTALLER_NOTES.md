# Windows Installer Notes

## Installation Process

The Windows MSI installer takes a **different approach** than the Linux installers for post-installation automation.

### Why No Automatic Post-Install?

**Technical Limitation:** Windows MSI custom actions run in a restricted context that doesn't support interactive prompts. Since our setup wizard needs user input (API keys, choices, etc.), we can't run it automatically during installation.

**Solution:** We provide **Start Menu shortcuts** that users can run after installation.

---

## What the Installer Does

### 1. Installs All Files ✅

The MSI installer includes and extracts:
- Complete `src/` directory (all Python source code)
- All `scripts/` (both .sh and .ps1 files)
- `docker-compose.yml`
- `.env.template`
- Documentation (README, INSTALL, CHANGELOG)
- All PowerShell helper scripts

**Installation Location:** `C:\Program Files\DIS Verification GenAI\`

### 2. Offers to Run Setup Wizard ✅

At the end of installation, the final dialog shows:
- ✅ Checkbox: **"Run first-time setup wizard now (recommended)"** (checked by default)
- When you click "Finish", if checked, PowerShell opens with the interactive setup wizard
- This automatically configures your .env, offers Ollama installation, pulls models, etc.

**This matches Linux behavior** - setup runs right after installation!

### 3. Creates Start Menu Shortcuts ✅

Four shortcuts are created in Start Menu > DIS Verification GenAI:

#### **DIS Verification GenAI** (Main Launcher)
- Starts Docker Compose services
- Opens web browser to http://localhost:8501
- Use this after setup is complete

#### **First-Time Setup** ⭐ **Run This First!**
- Interactive PowerShell wizard
- Checks Docker is running
- Runs environment configuration
- Offers to install Ollama
- Offers to pull models
- Complete automated setup

#### **Configure Environment**
- Re-runs just the `.env` configuration wizard
- Use if you need to change API keys later
- Does not install Ollama or pull models

#### **Stop Services**
- Stops all Docker containers
- Use before updates or maintenance

---

## First-Time Installation Steps

### After Installing the MSI:

**OPTION 1: Automatic (Recommended)** ⭐

1. **At the end of MSI installation, leave the checkbox checked:**
   ```
   ☑ Run first-time setup wizard now (recommended)
   ```

2. **Click "Finish"**
   - PowerShell window opens automatically
   - Interactive setup wizard runs

**OPTION 2: Manual (if you unchecked the box)**

1. **Click "First-Time Setup" from Start Menu**
   ```
   Start Menu > DIS Verification GenAI > First-Time Setup
   ```

### The Setup Wizard Will:
   - Checks if Docker Desktop is running (offers to start it)
   - Runs environment setup wizard:
     - Enter OpenAI API key (or skip)
     - Choose Ollama models to auto-pull
     - Configure database password
     - Optional: LangSmith tracing
   - Offers to install Ollama (opens download page)
   - Offers to pull recommended models

3. **Launch the Application:**
   ```
   Start Menu > DIS Verification GenAI > DIS Verification GenAI
   ```
   This will start services and open your browser.

---

## Comparison: Windows vs Linux

### Linux (DEB/RPM):
```bash
sudo dpkg -i dis-verification-genai_1.0.0_amd64.deb
# Installation pauses and runs interactive wizard automatically
# Prompts appear in terminal during install
# Everything configured before install completes
```

### Windows (MSI):
```powershell
# Double-click dis-verification-genai-1.0.0.msi
# Installer GUI runs through steps
# Files are copied, shortcuts created
# Final dialog shows checkbox:
#   ☑ Run first-time setup wizard now (recommended)
# Click "Finish"
# PowerShell opens and runs interactive wizard
# Same experience as Linux, just at the END instead of DURING
```

**Both platforms now offer automatic setup!** ✅

---

## Advantages of the Windows Approach

1. **Clean Installation** - MSI completes without blocking
2. **User Control** - Run setup when ready, not forced during install
3. **Re-runnable** - Can run "First-Time Setup" again if needed
4. **Better UX** - PowerShell window shows clear prompts and colors
5. **No Elevation Issues** - Shortcuts run with user's permissions

---

## Silent/Unattended Installation

For enterprise deployments, you can pre-configure the `.env` file:

```powershell
# Install MSI silently
msiexec /i dis-verification-genai-1.0.0.msi /quiet

# Create pre-configured .env
$envContent = @"
OPENAI_API_KEY=sk-your-key-here
DB_PASSWORD=your-secure-password
# ... other settings
"@
Set-Content "C:\Program Files\DIS Verification GenAI\.env" $envContent

# Start services
cd "C:\Program Files\DIS Verification GenAI"
docker compose up -d
```

---

## Troubleshooting

### "First-Time Setup" shortcut does nothing
**Cause:** PowerShell execution policy blocks scripts

**Fix:**
```powershell
# Run PowerShell as Administrator
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

# Or run the script directly:
powershell -ExecutionPolicy Bypass -File "C:\Program Files\DIS Verification GenAI\scripts\post-install.ps1"
```

### Setup wizard closes immediately
**Cause:** Error in script, not enough permissions

**Fix:** Run PowerShell manually to see errors:
```powershell
cd "C:\Program Files\DIS Verification GenAI"
.\scripts\post-install.ps1 -InstallDir "C:\Program Files\DIS Verification GenAI"
```

### Want to run setup again
**Solution:** Just click "First-Time Setup" again, or run:
```powershell
# Re-run complete setup
Start Menu > DIS Verification GenAI > First-Time Setup

# Or just reconfigure .env
Start Menu > DIS Verification GenAI > Configure Environment
```

---

## For Developers: How It Works

### MSI Build Process (GitHub Actions):

1. **Create Staging Directory**
   - Copies all source files
   - Copies scripts (bash + PowerShell)
   - Copies LICENSE.rtf for WiX UI

2. **Harvest Files with heat.exe**
   ```powershell
   heat.exe dir staging -cg ApplicationFiles -var "var.StagingDir" ...
   ```
   Creates `FilesFragment.wxs` with all files

3. **Compile WiX Sources**
   ```powershell
   candle.exe Product_build.wxs -dStagingDir="..." -arch x64
   candle.exe FilesFragment.wxs -dStagingDir="..." -arch x64
   ```

4. **Link to Create MSI**
   ```powershell
   light.exe Product_build.wixobj FilesFragment.wixobj -out dis-verification-genai-1.0.0.msi
   ```

### Why No Custom Actions?

Originally tried to run post-install.ps1 as a WiX custom action, but:
- ❌ ICE77 validation error (scheduling issue)
- ❌ Deferred actions can't show interactive prompts
- ❌ Immediate actions run too early (files not installed yet)
- ❌ Complex property passing for paths

**Better Solution:** Let users run setup via shortcuts when ready.

---

## Summary

The Windows installer **does install all source code and scripts**, but **does not automatically run setup**. Instead, users run the **"First-Time Setup"** shortcut after installation for an interactive configuration experience.

This provides the same functionality as Linux installers, just with an extra manual step that's more appropriate for Windows.
