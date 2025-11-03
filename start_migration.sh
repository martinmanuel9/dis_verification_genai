#!/bin/bash

# Position-Aware Image Placement Migration - Quick Start Script
# This script helps you begin the migration process

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   Position-Aware Image Placement Migration - Quick Start  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "MIGRATION_PLAN.md" ]; then
    print_error "MIGRATION_PLAN.md not found. Please run this script from the project root."
    exit 1
fi

print_success "Found MIGRATION_PLAN.md"

# Phase 1: Pre-Migration Checks
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  Phase 1: Pre-Migration Checks"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Check git status
print_status "Checking git status..."
if [ -n "$(git status --porcelain)" ]; then
    print_warning "You have uncommitted changes:"
    git status --short
    echo ""
    read -p "Do you want to commit these changes before starting? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Committing changes..."
        git add .
        read -p "Enter commit message: " commit_msg
        git commit -m "$commit_msg"
        print_success "Changes committed"
    else
        print_warning "Proceeding with uncommitted changes (not recommended)"
    fi
else
    print_success "Working directory is clean"
fi

# Check if we're on a feature branch
current_branch=$(git branch --show-current)
if [ "$current_branch" = "main" ] || [ "$current_branch" = "master" ]; then
    print_warning "You're on the $current_branch branch"
    read -p "Create feature branch 'feature/position-aware-images'? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Creating feature branch..."
        git checkout -b feature/position-aware-images
        print_success "Feature branch created: feature/position-aware-images"
    else
        print_error "Migration should be done on a feature branch. Exiting."
        exit 1
    fi
else
    print_success "On branch: $current_branch"
fi

# Create rollback tag
print_status "Creating rollback tag..."
if git tag | grep -q "pre-position-aware-migration"; then
    print_warning "Tag 'pre-position-aware-migration' already exists"
else
    git tag pre-position-aware-migration
    print_success "Created tag: pre-position-aware-migration"
fi

# Check if new modules exist
echo ""
print_status "Checking for position-aware modules..."

modules=(
    "src/fastapi/services/position_aware_extraction.py"
    "src/fastapi/services/position_aware_chunking.py"
    "src/fastapi/services/position_aware_reconstruction.py"
)

all_modules_exist=true
for module in "${modules[@]}"; do
    if [ -f "$module" ]; then
        print_success "Found: $module"
    else
        print_error "Missing: $module"
        all_modules_exist=false
    fi
done

if [ "$all_modules_exist" = false ]; then
    print_error "Some modules are missing. Please ensure all files from the solution are present."
    exit 1
fi

# Check Docker services
echo ""
print_status "Checking Docker services..."

if command -v docker-compose &> /dev/null; then
    print_success "docker-compose is installed"

    # Check if services are running
    if docker-compose ps | grep -q "Up"; then
        print_success "Docker services are running"
        docker-compose ps
    else
        print_warning "Docker services are not running"
        read -p "Start Docker services now? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_status "Starting Docker services..."
            docker-compose up -d
            sleep 5
            print_success "Docker services started"
        else
            print_warning "Services not running. You'll need to start them before testing."
        fi
    fi
else
    print_error "docker-compose not found. Please install Docker."
    exit 1
fi

# Check for test PDF
echo ""
print_status "Checking for test PDF..."

test_pdfs=$(find . -maxdepth 2 -name "*.pdf" -type f 2>/dev/null | head -5)
if [ -n "$test_pdfs" ]; then
    print_success "Found test PDFs:"
    echo "$test_pdfs"
else
    print_warning "No test PDFs found in current directory"
    print_warning "Please prepare a 2-3 page PDF with images for testing"
fi

# Create backup of key files
echo ""
print_status "Creating backup of files that will be modified..."

backup_dir=".migration_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$backup_dir"

files_to_backup=(
    "src/fastapi/services/document_ingestion_service.py"
    "src/fastapi/api/vectordb_api.py"
)

for file in "${files_to_backup[@]}"; do
    if [ -f "$file" ]; then
        cp "$file" "$backup_dir/"
        print_success "Backed up: $file"
    else
        print_warning "File not found: $file"
    fi
done

print_success "Backup created in: $backup_dir"

# Summary
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  Pre-Migration Summary"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "✅ Git status checked"
echo "✅ Feature branch created/verified"
echo "✅ Rollback tag created"
echo "✅ Position-aware modules verified"
echo "✅ Docker services checked"
echo "✅ Backup created: $backup_dir"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  Next Steps"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "1. Open MIGRATION_PLAN.md and start Phase 1, Step 1.2"
echo "2. Run a baseline test to capture current behavior:"
echo ""
echo "   curl -X POST \"http://localhost:8000/api/vectordb/documents/upload-and-process\" \\"
echo "     -F \"files=@your_test.pdf\" \\"
echo "     -F \"collection_name=baseline_test\" \\"
echo "     -F \"vision_models=enhanced_local\""
echo ""
echo "3. Save the reconstruction output for comparison"
echo "4. Follow MIGRATION_PLAN.md Phase 2 onwards"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  Helpful Commands"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "View logs:"
echo "  docker-compose logs -f fastapi"
echo ""
echo "Restart services:"
echo "  docker-compose restart fastapi"
echo ""
echo "Check git status:"
echo "  git status"
echo ""
echo "Rollback if needed:"
echo "  git checkout pre-position-aware-migration"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""
print_success "Pre-migration setup complete! Ready to begin."
echo ""
read -p "Press Enter to continue..."
