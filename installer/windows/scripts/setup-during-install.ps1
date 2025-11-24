###############################################################################
# Setup Script for WiX Installer
# Runs as deferred custom action with MSI logging
# All output goes to MSI log which is displayed in the progress dialog
###############################################################################

param(
    [string]$InstallDir = "$env:ProgramFiles\DIS Verification GenAI",
    [string]$EnvFilePath = ""
)

# Use Write-Host for MSI logging - it will appear in the installer progress
function Write-Log {
    param([string]$Message)
    Write-Host "CustomAction: $Message"
    Start-Sleep -Milliseconds 100  # Brief pause so MSI can capture output
}

function Write-Progress-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "CustomAction: =========================================="
    Write-Host "CustomAction: $Message"
    Write-Host "CustomAction: =========================================="
    Write-Host ""
}

try {
    Write-Progress-Step "STEP 1/5: Environment Configuration"

    $envFile = Join-Path $InstallDir ".env"

    # Verify .env file exists (REQUIRED)
    if (-not (Test-Path $envFile)) {
        Write-Log "ERROR: .env file not found at: $envFile"
        Write-Log "The .env file is REQUIRED for the application to function"
        Write-Log "Installation cannot continue without a valid .env file"
        throw ".env file is missing - this should have been copied during installation"
    }

    # Validate .env file has content
    $envContent = Get-Content $envFile -Raw
    if (-not $envContent -or $envContent.Trim().Length -eq 0) {
        Write-Log "ERROR: .env file is empty"
        Write-Log "The .env file must contain valid configuration"
        throw ".env file is empty"
    }

    Write-Log ".env file verified successfully at: $envFile"
    $lineCount = (Get-Content $envFile | Measure-Object -Line).Lines
    Write-Log ".env file contains $lineCount lines of configuration"
    Write-Log "Step 1/5 Complete"

    ###########################################################################
    # STEP 2: Check Docker
    ###########################################################################
    Write-Progress-Step "STEP 2/5: Docker Verification"

    $dockerRunning = $false
    try {
        $null = docker info 2>&1
        if ($LASTEXITCODE -eq 0) {
            $dockerRunning = $true
            Write-Log "Docker is running"
        }
    } catch {
        $dockerRunning = $false
    }

    if (-not $dockerRunning) {
        Write-Log "WARNING: Docker is not running"
        Write-Log "You'll need to start Docker and run 'First-Time Setup' after installation"
        Write-Log "Step 2/5 Skipped (Docker not available)"
    } else {
        Write-Log "Step 2/5 Complete"
    }

    ###########################################################################
    # STEP 3: Detect System
    ###########################################################################
    Write-Progress-Step "STEP 3/5: System Hardware Detection"

    $hasGPU = $false
    $totalRAM = 0
    $recommendedModel = ""

    try {
        # Detect GPU
        $gpus = Get-WmiObject Win32_VideoController
        foreach ($gpu in $gpus) {
            if ($gpu.Name -like "*NVIDIA*" -or $gpu.Name -like "*AMD*" -or $gpu.Name -like "*Radeon*") {
                $hasGPU = $true
                Write-Log "GPU detected: $($gpu.Name)"
            }
        }

        if (-not $hasGPU) {
            Write-Log "No dedicated GPU detected (CPU mode)"
        }

        # Detect RAM
        $ram = Get-WmiObject Win32_ComputerSystem
        $totalRAM = [math]::Round($ram.TotalPhysicalMemory / 1GB)
        Write-Log "System RAM: ${totalRAM}GB"

        # Determine recommended model
        if ($hasGPU -and $totalRAM -ge 16) {
            $recommendedModel = "llama3.1:8b"
        } elseif ($hasGPU) {
            $recommendedModel = "llama3.2:3b"
        } else {
            $recommendedModel = "llama3.2:1b"
        }

        Write-Log "Recommended model: $recommendedModel"
    } catch {
        Write-Log "Could not detect system specs: $($_.Exception.Message)"
        $recommendedModel = "llama3.2:1b"
    }

    Write-Log "Step 3/5 Complete"

    ###########################################################################
    # STEP 4: Download Models (if Ollama available and Docker running)
    ###########################################################################
    Write-Progress-Step "STEP 4/5: AI Model Download"

    $ollamaInstalled = Get-Command ollama -ErrorAction SilentlyContinue

    if (-not $ollamaInstalled) {
        Write-Log "Ollama not installed - skipping model download"
        Write-Log "Install Ollama from: https://ollama.com/download/windows"
        Write-Log "Then run 'First-Time Setup' from Start Menu"
        Write-Log "Step 4/5 Skipped (Ollama not available)"
    } elseif (-not $dockerRunning) {
        Write-Log "Docker not running - skipping model download"
        Write-Log "Run 'First-Time Setup' from Start Menu after starting Docker"
        Write-Log "Step 4/5 Skipped (Docker not available)"
    } else {
        Write-Log "Downloading AI models (this may take 5-10 minutes)..."

        # Download embedding model
        Write-Log "Downloading embedding model: snowflake-arctic-embed2"
        ollama pull snowflake-arctic-embed2 2>&1 | ForEach-Object { Write-Log $_ }

        # Download LLM model
        Write-Log "Downloading LLM model: $recommendedModel"
        ollama pull $recommendedModel 2>&1 | ForEach-Object { Write-Log $_ }

        Write-Log "Step 4/5 Complete"
    }

    ###########################################################################
    # STEP 5: Build Docker Images
    ###########################################################################
    Write-Progress-Step "STEP 5/5: Building Docker Containers"

    if (-not $dockerRunning) {
        Write-Log "Docker not running - skipping build"
        Write-Log "Run 'First-Time Setup' from Start Menu after starting Docker"
        Write-Log "Step 5/5 Skipped (Docker not available)"
    } else {
        Set-Location $InstallDir

        # Build base dependencies
        Write-Log "Building base dependencies (this may take 5-10 minutes)..."
        Write-Log "Running: docker compose build base-poetry-deps"
        docker compose build base-poetry-deps 2>&1 | ForEach-Object { Write-Log $_ }

        if ($LASTEXITCODE -ne 0) {
            Write-Log "ERROR: Failed to build base dependencies"
            Write-Log "You can retry by running 'First-Time Setup' from Start Menu"
        } else {
            Write-Log "Base dependencies built successfully"

            # Build application services
            Write-Log "Building application services (this may take 5-10 minutes)..."
            Write-Log "Running: docker compose build"
            docker compose build 2>&1 | ForEach-Object { Write-Log $_ }

            if ($LASTEXITCODE -ne 0) {
                Write-Log "ERROR: Failed to build application services"
                Write-Log "You can retry by running 'First-Time Setup' from Start Menu"
            } else {
                Write-Log "Application services built successfully"
                Write-Log "Step 5/5 Complete"
            }
        }
    }

    Write-Progress-Step "Installation Complete!"
    Write-Log "All setup steps finished"
    Write-Log "You can now launch the application from the Start Menu"

    exit 0

} catch {
    Write-Log "ERROR: $($_.Exception.Message)"
    Write-Log "Stack trace: $($_.ScriptStackTrace)"
    Write-Log "You can retry setup by running 'First-Time Setup' from Start Menu"
    exit 1
}
