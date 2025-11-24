###############################################################################
# Launch Script for DIS Verification GenAI
# Builds and starts the application
###############################################################################

param(
    [string]$InstallDir = "$env:ProgramFiles\DIS Verification GenAI"
)

$ErrorActionPreference = "Continue"

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-ErrorMsg {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

Write-Host ""
Write-Host "════════════════════════════════════════════════════════════════"
Write-Host "  DIS Verification GenAI - Launcher"
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
    Write-ErrorMsg "Docker Desktop is not running!"
    Write-Info "Please start Docker Desktop and try again."
    Write-Host ""
    Write-Host "Press any key to exit..."
    $null = $host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
    exit 1
}

Write-Success "Docker is running"
Set-Location $InstallDir

# Check if images exist
$imagesExist = $false
try {
    $images = docker images --format "{{.Repository}}" | Select-String -Pattern "base-poetry-deps|fastapi|streamlit"
    if ($images) {
        $imagesExist = $true
    }
} catch {
    $imagesExist = $false
}

if (-not $imagesExist) {
    Write-Info "First-time setup detected. Building Docker images..."
    Write-Host ""
    Write-Info "Step 1/3: Building base dependencies (this may take 5-10 minutes)..."
    docker compose build base-poetry-deps

    if ($LASTEXITCODE -ne 0) {
        Write-ErrorMsg "Failed to build base dependencies"
        Write-Host ""
        Write-Host "Press any key to exit..."
        $null = $host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
        exit 1
    }

    Write-Host ""
    Write-Info "Step 2/3: Building application services..."
    docker compose build

    if ($LASTEXITCODE -ne 0) {
        Write-ErrorMsg "Failed to build application services"
        Write-Host ""
        Write-Host "Press any key to exit..."
        $null = $host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
        exit 1
    }

    Write-Success "Images built successfully!"
} else {
    Write-Info "Docker images already exist. Starting services..."
}

Write-Host ""
Write-Info "Step 3/3: Starting services..."
docker compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-ErrorMsg "Failed to start services"
    Write-Info "Check logs with: docker compose logs"
    Write-Host ""
    Write-Host "Press any key to exit..."
    $null = $host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
    exit 1
}

Write-Host ""
Write-Info "Waiting for services to initialize..."
Start-Sleep -Seconds 10

Write-Host ""
Write-Success "Application started successfully!"
Write-Host ""
Write-Info "Services running:"
Write-Host "  - Streamlit UI:  http://localhost:8501"
Write-Host "  - FastAPI:       http://localhost:9020"
Write-Host "  - ChromaDB:      http://localhost:8000"
Write-Host ""
Write-Info "Opening web interface in your browser..."
Start-Process "http://localhost:8501"

Write-Host ""
Write-Host "The application is now running in the background."
Write-Host "To stop the services, use the 'Stop Services' shortcut"
Write-Host "or run: docker compose down"
Write-Host ""
Write-Host "Press any key to close this window..."
$null = $host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
