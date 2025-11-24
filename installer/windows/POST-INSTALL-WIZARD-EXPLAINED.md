# Post-Install Wizard Explained

## What Happens After Installation Completes?

At the end of the MSI installation, you'll see a checkbox:

```
☑ Launch interactive configuration wizard (recommended for first-time users)
```

This checkbox is **checked by default** but users can uncheck it if they want.

## Option 1: User Leaves Checkbox CHECKED (Default)

When the user clicks "Finish" with the checkbox checked, the following happens:

### What Runs
The installer launches: [post-install.ps1](scripts/post-install.ps1)

### What the User Sees

1. **Docker Check**
   ```
   Docker Desktop is not running
   Please start Docker Desktop before continuing
   Would you like to start Docker Desktop now? (Y/n)
   ```
   - If Docker isn't running, offers to start it
   - Waits 30 seconds for Docker to start

2. **Interactive Environment Setup** (Optional)
   ```
   Run interactive environment setup now? (Y/n)
   ```
   - If user chooses **Yes**: Runs [setup-env.ps1](scripts/setup-env.ps1)
     - Prompts for OpenAI API key
     - Prompts for database passwords
     - Prompts for Ollama models
     - Creates/updates .env file interactively

   - If user chooses **No**: Skips to next step

3. **Ollama Installation with Smart Model Selection** (Optional)
   ```
   Install Ollama for local model support? (y/N)
   ```
   - If user chooses **Yes**: Opens Ollama download page in browser
   - If Ollama already installed: Detects GPU and RAM, then recommends models:
     ```
     Pull/update Ollama models now? (Y/n)
     ```

     **Smart Model Selection:**
     - 🖥️ **NVIDIA/AMD GPU + 16GB+ RAM** → `llama3.1:8b` (best quality)
     - 🖥️ **NVIDIA/AMD GPU + <16GB RAM** → `llama3.2:3b` (good balance)
     - 💻 **CPU Only** → `llama3.2:1b` (optimized for CPU)
     - 📦 **Always pulls:** `snowflake-arctic-embed2` (embedding model)

4. **Build and Launch Application** (RECOMMENDED - Default YES)
   ```
   Would you like to build and start the application now? This will take 5-10 minutes. (Y/n)
   ```
   - If user presses **Enter** or chooses **Yes** (DEFAULT):
     - 🔨 Builds Docker images with progress updates:
       - Step 1/3: Building base dependencies (base-poetry-deps)
       - Step 2/3: Building application services (fastapi, streamlit, celery)
       - Step 3/3: Starting all services with `docker compose up -d`
     - ⏱️ **This takes 5-10 minutes** - the wizard waits for completion
     - 🌐 Opens http://localhost:8501 in default browser
     - ✅ **Application is fully ready to use!**

   - If user chooses **No**:
     - Installation complete, wizard exits
     - User must run "First-Time Setup" shortcut later to build images

### Summary
This is the **full guided setup experience** - perfect for first-time users who want help configuring everything.

---

## Option 2: User UNCHECKS the Checkbox

When the user unchecks the box and clicks "Finish":

### What Happens
- Installation completes
- No wizard runs
- User is returned to Windows desktop
- `.env` file was already created from the content they pasted during installation

### What the User Should Do Next

They can launch the application in 3 ways:

**Method 1: Start Menu Shortcut** ⚡ FAST
```
Start Menu → DIS Verification GenAI → DIS Verification GenAI
```
- Runs [launch-app.ps1](scripts/launch-app.ps1)
- Checks for .env file and Docker images
- **Does NOT build** - just starts existing services with `docker compose up -d`
- Opens http://localhost:8501
- ⚡ **Takes ~10 seconds** (fast!)

**Method 2: Desktop Shortcut** (if they created one during install)
```
Double-click "DIS Verification GenAI" on desktop
```
- Same as Method 1

**Method 3: First-Time Setup** 🔨 (If images not built yet)
```
Start Menu → DIS Verification GenAI → First-Time Setup
```
- Runs [post-install.ps1](scripts/post-install.ps1)
- Builds all Docker images (5-10 minutes)
- Pulls Ollama models based on your GPU
- Starts services
- Opens http://localhost:8501

**Method 4: Manual Launch**
```powershell
cd "C:\Program Files\DIS Verification GenAI"
docker compose up -d
start http://localhost:8501
```

### Summary
This is the **manual setup path** - for advanced users who know what they're doing and want to configure things themselves.

---

## Key Files and What They Do

| File | Purpose | When It Runs |
|------|---------|--------------|
| [create-env-from-input.ps1](scripts/create-env-from-input.ps1) | Creates .env from pasted content during install | During MSI installation (automatic) |
| [post-install.ps1](scripts/post-install.ps1) | Interactive first-time setup wizard | After install if checkbox is checked |
| [setup-env.ps1](scripts/setup-env.ps1) | Prompts user for environment variables | Called by post-install.ps1 if user wants help |
| [launch-app.ps1](scripts/launch-app.ps1) | Launches app from shortcuts | When user clicks Start Menu/Desktop shortcut |

---

## What the Checkbox Text Means

**Old Text (Unclear):**
```
☑ Run first-time setup wizard now (recommended)
```
❌ Problem: Users don't know what this wizard does or why they'd skip it

**New Text (Clear):**
```
☑ Launch interactive configuration wizard (recommended for first-time users)
```
✅ Better: Makes it clear this is:
- Interactive (they'll be asked questions)
- For configuration (setting up environment/keys)
- Recommended for first-timers
- Optional (advanced users can skip)

---

## Common User Paths

### Path A: First-Time User (Wants Help)
1. Install MSI
2. Paste .env during install → .env created automatically ✅
3. Leave checkbox checked
4. Follow wizard prompts
5. App builds and launches automatically
6. Done! 🎉

### Path B: Advanced User (Self-Sufficient)
1. Install MSI
2. Paste .env during install → .env created automatically ✅
3. Uncheck the checkbox
4. Click Start Menu shortcut when ready
5. App builds and launches
6. Done! 🎉

### Path C: User Who Skipped .env During Install
1. Install MSI
2. Skip pasting .env → .env.template copied as .env ⚠️
3. Run "Configure Environment" shortcut from Start Menu
4. Fill in API keys interactively
5. Click Start Menu shortcut
6. App builds and launches
7. Done! 🎉

---

## Troubleshooting

**Problem: "Docker is not running"**
- Solution: Start Docker Desktop first, then run the shortcut again

**Problem: ".env file not found"**
- Solution: Run "Configure Environment" from Start Menu
- Or manually copy .env.template to .env and edit it

**Problem: "Failed to build base dependencies"**
- Solution: Check Docker has enough resources (8GB RAM minimum)
- Check internet connection (needs to download Python packages)

**Problem: Application won't start after build**
- Solution: Run `docker compose logs` to see error messages
- Common issues: Port conflicts (8501, 9020 already in use)

---

## Next Steps

After installation, users should:

1. ✅ Launch the application (via shortcut or wizard)
2. ✅ Navigate to http://localhost:8501
3. ✅ Upload documents and start testing!

That's it! The wizard makes first-time setup easy while giving power users the option to skip it.
