# Windows Installer Debugging Guide

## Recent Simplifications (2025-11-23)

The installer has been simplified to make debugging easier and more transparent.

### 1. .env File Creation - Now Visible and Logged

**Old Approach (Hidden):**
- Complex inline PowerShell in WiX custom action
- No visibility into what was happening
- Hard to debug when it failed

**New Approach (Transparent):**
- Dedicated script: [scripts/create-env.ps1](scripts/create-env.ps1)
- **Visible PowerShell window** shows progress
- **Log file** created at: `%TEMP%\dis-genai-env-creation.log`
- Shows first few lines of created .env for confirmation

**How to Debug:**

1. **During Installation:**
   - Watch for PowerShell window that says "DIS Verification GenAI - .env File Creation"
   - Window stays open - you can see any errors

2. **After Installation:**
   - Check the log file: `C:\Users\<YourName>\AppData\Local\Temp\dis-genai-env-creation.log`
   - Manually run the script to test:
     ```powershell
     cd "C:\Program Files\DIS Verification GenAI"
     .\scripts\create-env.ps1 -InstallDir "C:\Program Files\DIS Verification GenAI" -EnvContent "TEST_VAR=hello"
     ```

3. **Verify .env Created:**
   ```powershell
   Get-Content "C:\Program Files\DIS Verification GenAI\.env"
   ```

### 2. Post-Install Script - Visible Output

**Script:** [scripts/post-install.ps1](scripts/post-install.ps1)

**Wrapper:** [scripts/run-post-install.cmd](scripts/run-post-install.cmd)

The wrapper script keeps the PowerShell window open so you can see:
- Docker build progress
- Ollama model downloads
- Any errors that occur
- Completion status

**How to Debug:**

1. **Run manually:**
   ```cmd
   cd "C:\Program Files\DIS Verification GenAI"
   .\scripts\run-post-install.cmd
   ```

2. **Watch for:**
   - GPU detection results
   - RAM detection
   - Which Ollama model is being pulled
   - Docker build steps (1/3, 2/3, 3/3)
   - Any error messages in red

### 3. Launch Script - Better Error Messages

**Script:** [scripts/launch-app.ps1](scripts/launch-app.ps1)

**Improvements:**
- Clear error if Docker not running
- Clear error if .env file missing
- Clear error if images not built yet
- Helpful guidance on what to do next

**How to Debug:**

1. **Run manually to see errors:**
   ```cmd
   cd "C:\Program Files\DIS Verification GenAI"
   powershell -ExecutionPolicy Bypass -File scripts\launch-app.ps1
   ```

2. **Common errors and fixes:**

   | Error | Fix |
   |-------|-----|
   | "Docker Desktop is not running" | Start Docker Desktop |
   | ".env file not found" | Run "Configure Environment" shortcut |
   | "Docker images not found" | Run "First-Time Setup" shortcut |

## Common Issues and Solutions

### Issue 1: .env File Not Created

**Symptoms:**
- Installation completes but no .env file exists
- launch-app.ps1 shows ".env file not found"

**Debug Steps:**
1. Check the log: `%TEMP%\dis-genai-env-creation.log`
2. Look for lines showing:
   - "Content Length: X characters" - should be > 0
   - "SUCCESS: .env file created" - should see this
3. Check if you pasted content in the installer dialog
4. Try creating manually:
   ```powershell
   cd "C:\Program Files\DIS Verification GenAI"
   Copy-Item .env.template .env
   notepad .env
   ```

### Issue 2: Build Fails During Installation

**Symptoms:**
- Post-install wizard shows errors
- Docker build fails

**Debug Steps:**
1. Watch the PowerShell window output (it stays open)
2. Common issues:
   - Docker not running → Start Docker Desktop
   - Insufficient disk space → Free up space
   - Internet connection issues → Check network
3. Try building manually:
   ```cmd
   cd "C:\Program Files\DIS Verification GenAI"
   docker compose build base-poetry-deps
   docker compose build
   ```

### Issue 3: Services Won't Start

**Symptoms:**
- Launch shortcut fails
- "Failed to start services" error

**Debug Steps:**
1. Check Docker is running: `docker info`
2. Check images exist: `docker images`
3. Check for port conflicts:
   ```cmd
   netstat -ano | findstr ":8501"
   netstat -ano | findstr ":9020"
   netstat -ano | findstr ":8000"
   ```
4. View Docker logs:
   ```cmd
   cd "C:\Program Files\DIS Verification GenAI"
   docker compose logs
   ```

## Manual Installation Steps (If Installer Fails)

If the automated installer is not working, you can set up manually:

1. **Extract Files:**
   - Install the MSI (this extracts files even if scripts fail)
   - Files will be at: `C:\Program Files\DIS Verification GenAI`

2. **Create .env File:**
   ```cmd
   cd "C:\Program Files\DIS Verification GenAI"
   copy .env.template .env
   notepad .env
   ```
   Paste your configuration and save.

3. **Build Images:**
   ```cmd
   docker compose build base-poetry-deps
   docker compose build
   ```

4. **Start Services:**
   ```cmd
   docker compose up -d
   ```

5. **Open Browser:**
   ```cmd
   start http://localhost:8501
   ```

## Getting Help

If you're still having issues:

1. **Collect Logs:**
   - .env creation log: `%TEMP%\dis-genai-env-creation.log`
   - Docker logs: `docker compose logs > docker-logs.txt`
   - Installer log: `C:\Users\<YourName>\AppData\Local\Temp\*.log`

2. **Check File Existence:**
   ```powershell
   Test-Path "C:\Program Files\DIS Verification GenAI\.env"
   Test-Path "C:\Program Files\DIS Verification GenAI\docker-compose.yml"
   Test-Path "C:\Program Files\DIS Verification GenAI\Dockerfile.base"
   ```

3. **Report Issue:**
   - Create GitHub issue with logs attached
   - Include Windows version
   - Include Docker version: `docker --version`
