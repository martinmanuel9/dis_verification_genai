###############################################################################
# Windows Post-Installation Script
# Runs after MSI installation completes
###############################################################################

param(
    [string]$InstallDir = "$env:ProgramFiles\DIS Verification GenAI"
)

$ErrorActionPreference = "Continue"  # Don't exit on errors, show them and continue

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-ErrorMsg {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

Write-Host ""
Write-Host "════════════════════════════════════════════════════════════════"
Write-Host "  DIS Verification GenAI installed successfully!"
Write-Host "════════════════════════════════════════════════════════════════"
Write-Host ""

# Check if Docker is running
$dockerRunning = $false
try {
    $null = docker info 2>&1
    if ($LASTEXITCODE -eq 0) {
        $dockerRunning = $true
    }
} catch {
    $dockerRunning = $false
}

if (-not $dockerRunning) {
    Write-Warning "Docker Desktop is not running"
    Write-Info "Please start Docker Desktop before continuing"
    $startDocker = Read-Host "Would you like to start Docker Desktop now? (Y/n)"
    if ($startDocker -ne "n" -and $startDocker -ne "N") {
        Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
        Write-Info "Waiting for Docker to start (this may take a minute)..."
        Start-Sleep -Seconds 30
    }
}

# Interactive environment setup
Write-Host ""
$runSetup = Read-Host "Run interactive environment setup now? (Y/n)"
if ($runSetup -ne "n" -and $runSetup -ne "N") {
    Write-Info "Starting environment setup wizard..."
    & "$InstallDir\scripts\setup-env.ps1" -InstallDir $InstallDir
} else {
    Write-Info "Skipping environment setup. You can run it later with:"
    Write-Host "  powershell -ExecutionPolicy Bypass -File `"$InstallDir\scripts\setup-env.ps1`""
}

Write-Host ""

# Optional: Install and configure Ollama
$ollamaInstalled = Get-Command ollama -ErrorAction SilentlyContinue
if (-not $ollamaInstalled) {
    $installOllama = Read-Host "Install Ollama for local model support? (y/N)"
    if ($installOllama -eq "y" -or $installOllama -eq "Y") {
        Write-Info "Opening Ollama download page..."
        Start-Process "https://ollama.com/download/windows"
        Write-Warning "Please install Ollama and run this script again to pull models"
    }
} else {
    Write-Success "Ollama is already installed."

    # Detect GPU
    Write-Info "Detecting system capabilities..."
    $hasNvidiaGPU = $false
    $hasAMDGPU = $false
    $totalRAM = 0

    try {
        $gpu = Get-WmiObject Win32_VideoController | Select-Object -First 1
        if ($gpu.Name -like "*NVIDIA*") {
            $hasNvidiaGPU = $true
            Write-Info "NVIDIA GPU detected: $($gpu.Name)"
        } elseif ($gpu.Name -like "*AMD*" -or $gpu.Name -like "*Radeon*") {
            $hasAMDGPU = $true
            Write-Info "AMD GPU detected: $($gpu.Name)"
        } else {
            Write-Info "No dedicated GPU detected (CPU only)"
        }

        $ram = Get-WmiObject Win32_ComputerSystem
        $totalRAM = [math]::Round($ram.TotalPhysicalMemory / 1GB)
        Write-Info "System RAM: ${totalRAM}GB"
    } catch {
        Write-Warning "Could not detect system specs"
    }

    $pullModels = Read-Host "Pull/update Ollama models now? (Y/n)"
    if ($pullModels -ne "n" -and $pullModels -ne "N") {
        Write-Info "Pulling recommended models for your system..."
        Write-Host ""

        # Always pull embedding model (small)
        Write-Info "Pulling embedding model: snowflake-arctic-embed2"
        ollama pull snowflake-arctic-embed2

        # Choose LLM based on hardware
        if ($hasNvidiaGPU -or $hasAMDGPU) {
            if ($totalRAM -ge 16) {
                Write-Info "Pulling large model (good GPU + RAM): llama3.1:8b"
                ollama pull llama3.1:8b
            } else {
                Write-Info "Pulling medium model (good GPU, limited RAM): llama3.2:3b"
                ollama pull llama3.2:3b
            }
        } else {
            # CPU only - use smaller models
            Write-Info "Pulling small model (CPU only): llama3.2:1b"
            ollama pull llama3.2:1b
        }

        Write-Success "Ollama models pulled successfully!"
    }
}

Write-Host ""
Write-Host "════════════════════════════════════════════════════════════════"
Write-Host "  Installation Complete!"
Write-Host "════════════════════════════════════════════════════════════════"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Start the services:"
Write-Host "     - Use Start Menu shortcut: 'DIS Verification GenAI'"
Write-Host "     - Or run: cd `"$InstallDir`" && docker compose up -d"
Write-Host ""
Write-Host "  2. Access the web interface:"
Write-Host "     http://localhost:8501"
Write-Host ""
Write-Host "Documentation: $InstallDir\README.md"
Write-Host "Troubleshooting: $InstallDir\INSTALL.md"
Write-Host "═══════════════════════════════════════════════════════════════"
Write-Host ""

# Ask if user wants to build and start now
$startNow = Read-Host "Would you like to build and start the application now? This will take 5-10 minutes. (Y/n)"
if ($startNow -ne "n" -and $startNow -ne "N") {
    Write-Info "Starting DIS Verification GenAI..."
    Set-Location $InstallDir

    # Build Docker images first
    Write-Info "Building Docker images (this may take several minutes on first run)..."
    Write-Host ""
    Write-Info "Step 1/3: Building base dependencies..."
    docker compose build base-poetry-deps

    if ($LASTEXITCODE -ne 0) {
        Write-ErrorMsg "Failed to build base dependencies"
        Write-Warning "You can try building manually with: cd '$InstallDir' && docker compose build"
        pause
        exit 1
    }

    Write-Host ""
    Write-Info "Step 2/3: Building application services..."
    docker compose build

    if ($LASTEXITCODE -ne 0) {
        Write-ErrorMsg "Failed to build application services"
        Write-Warning "You can try building manually with: cd '$InstallDir' && docker compose build"
        pause
        exit 1
    }

    Write-Host ""
    Write-Info "Step 3/3: Starting services..."
    docker compose up -d

    if ($LASTEXITCODE -ne 0) {
        Write-ErrorMsg "Failed to start services"
        Write-Warning "Check Docker logs with: docker compose logs"
        pause
        exit 1
    }

    Write-Host ""
    Write-Info "Waiting for services to initialize..."
    Start-Sleep -Seconds 15

    Write-Success "Application started successfully!"
    Write-Host ""
    Write-Info "Services running:"
    Write-Host "  - Streamlit UI:  http://localhost:8501"
    Write-Host "  - FastAPI:       http://localhost:9020"
    Write-Host "  - ChromaDB:      http://localhost:8000"
    Write-Host ""
    Write-Info "Opening web interface..."
    Start-Process "http://localhost:8501"
}
