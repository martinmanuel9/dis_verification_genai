###############################################################################
# Windows Post-Installation Script
# Runs after MSI installation completes
###############################################################################

param(
    [string]$InstallDir = "$env:ProgramFiles\DIS Verification GenAI"
)

$ErrorActionPreference = "Stop"

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
    $pullModels = Read-Host "Pull/update Ollama models now? (y/N)"
    if ($pullModels -eq "y" -or $pullModels -eq "Y") {
        Write-Info "Pulling models (this may take several minutes)..."
        # Check if we have WSL/bash for the script
        if (Get-Command bash -ErrorAction SilentlyContinue) {
            bash "$InstallDir\scripts\pull-ollama-models.sh" auto
        } else {
            Write-Info "Pulling recommended model: llama3.1:8b"
            ollama pull llama3.1:8b
            ollama pull snowflake-arctic-embed2
        }
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

# Ask if user wants to start now
$startNow = Read-Host "Would you like to start the application now? (y/N)"
if ($startNow -eq "y" -or $startNow -eq "Y") {
    Write-Info "Starting DIS Verification GenAI..."
    Set-Location $InstallDir
    docker compose up -d
    Start-Sleep -Seconds 10
    Write-Success "Application started!"
    Write-Info "Opening web interface..."
    Start-Process "http://localhost:8501"
}
