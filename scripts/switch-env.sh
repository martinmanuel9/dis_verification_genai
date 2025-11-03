#!/bin/bash
# switch-env.sh - Switch between Docker and local environments

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

show_usage() {
    echo "Usage: $0 {docker|local|status}"
    echo ""
    echo "Commands:"
    echo "  docker - Switch to Docker Compose environment (PostgreSQL)"
    echo "  local  - Switch to local/EC2 environment (SQLite)"
    echo "  status - Show current environment configuration"
    echo ""
    echo "Examples:"
    echo "  $0 docker  # Use Docker Compose with PostgreSQL"
    echo "  $0 local   # Use direct Python with SQLite"
    echo "  $0 status  # Check current setup"
}

show_status() {
    echo -e "${BLUE}🔍 Current Environment Status${NC}"
    echo -e "${BLUE}=============================${NC}"
    echo ""
    
    if [ -f .env ]; then
        echo -e "${GREEN}✅ .env file exists${NC}"
        
        # Check database type
        if grep -q "postgresql://" .env 2>/dev/null; then
            echo -e "📊 Database: ${YELLOW}PostgreSQL (Docker)${NC}"
            DB_TYPE="docker"
        elif grep -q "sqlite:///" .env 2>/dev/null; then
            echo -e "📊 Database: ${YELLOW}SQLite (Local)${NC}"
            DB_TYPE="local"
        else
            echo -e "📊 Database: ${RED}Unknown${NC}"
            DB_TYPE="unknown"
        fi
        
        # Check service URLs
        if grep -q "http://.*:.*/" .env 2>/dev/null; then
            if grep -q "localhost" .env 2>/dev/null; then
                echo -e "🌐 Services: ${YELLOW}Localhost URLs${NC}"
            else
                echo -e "🌐 Services: ${YELLOW}Container URLs${NC}"
            fi
        fi
        
        echo ""
        echo -e "${BLUE}📋 Configuration Summary:${NC}"
        if [ "$DB_TYPE" = "docker" ]; then
            echo "  Environment: Docker Compose"
            echo "  Database: PostgreSQL in container"
            echo "  Services: Container network"
            echo "  Usage: docker-compose up"
        elif [ "$DB_TYPE" = "local" ]; then
            echo "  Environment: Direct Python"
            echo "  Database: SQLite file"
            echo "  Services: Localhost"
            echo "  Usage: Start services individually"
        else
            echo "  Environment: Unknown/Custom"
        fi
        
    else
        echo -e "${RED}❌ .env file not found${NC}"
        echo ""
        echo "Available environment files:"
        [ -f .env.docker ] && echo -e "  ${GREEN}✅ .env.docker${NC} (Docker Compose)"
        [ -f .env.local ] && echo -e "  ${GREEN}✅ .env.local${NC} (Local/EC2)"
        
        if [ ! -f .env.docker ] && [ ! -f .env.local ]; then
            echo -e "  ${RED}❌ No environment files found${NC}"
            echo ""
            echo "Run one of:"
            echo "  $0 docker  # Create Docker environment"
            echo "  $0 local   # Create local environment"
        fi
    fi
    echo ""
}

switch_to_docker() {
    echo -e "${BLUE}🐳 Switching to Docker Compose environment${NC}"
    
    if [ -f .env.docker ]; then
        cp .env.docker .env
        echo -e "${GREEN}✅ Copied .env.docker to .env${NC}"
    else
        echo -e "${YELLOW}⚠️  .env.docker not found, creating basic Docker configuration...${NC}"
        cat > .env << 'EOF'
# Docker Environment Configuration
OPEN_AI_API_KEY=your-openai-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here
CASELAW_API_KEY=your-caselaw-api-key-here
SERPAPI_KEY=your-serpapi-key-here
SEARCHAPI_KEY=your-searchapi-key-here
HUGGINGFACE_API_KEY=your-huggingface-api-key-here
HUGGINGFACE_VISION_MODEL=Salesforce/blip-image-captioning-base
LANGCHAIN_API_KEY=your-langchain-api-key-here
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=pr-internal-courtroom-93

# Database (PostgreSQL in Docker)
DATABASE_URL=postgresql://g3nA1-user:m0re-g3nA1-s3cr3t@postgres:5432/rag_memory
DB_USERNAME=g3nA1-user
DB_PASSWORD=m0re-g3nA1-s3cr3t
DB_HOST=postgres
DB_PORT=5432
DB_NAME=rag_memory

# Service URLs (Docker containers)
FASTAPI_URL=http://fastapi:9020
CHROMA_URL=http://chromadb:8020
CHROMADB_PERSIST_DIRECTORY=/app/chroma_db_data
REDIS_URL=redis://redis:6379/0
REDIS_HOST=redis
REDIS_PORT=6379

# Application
REQUEST_TIMEOUT=600
LLM_TIMEOUT=300
IMAGES_STORAGE_DIR=./stored_images
EOF
    fi
    
    echo ""
    echo -e "${YELLOW}📋 Docker Environment Active${NC}"
    echo "  Database: PostgreSQL (container)"
    echo "  Services: Container network"
    echo ""
    echo -e "${BLUE}💡 Usage:${NC}"
    echo "  docker-compose up          # Start all services"
    echo "  docker-compose up -d       # Start in background"
    echo "  docker-compose down        # Stop all services"
    echo "  docker-compose logs -f     # View logs"
    echo ""
    echo -e "${YELLOW}🔧 Don't forget to configure your API keys in .env${NC}"
}

switch_to_local() {
    echo -e "${BLUE}🏠 Switching to local/EC2 environment${NC}"
    
    if [ -f .env.local ]; then
        cp .env.local .env
        echo -e "${GREEN}✅ Copied .env.local to .env${NC}"
    else
        echo -e "${YELLOW}⚠️  .env.local not found, creating basic local configuration...${NC}"
        cat > .env << 'EOF'
# Local/EC2 Environment Configuration
OPEN_AI_API_KEY=your-openai-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here
CASELAW_API_KEY=your-caselaw-api-key-here
SERPAPI_KEY=your-serpapi-key-here
SEARCHAPI_KEY=your-searchapi-key-here
HUGGINGFACE_API_KEY=your-huggingface-api-key-here
HUGGINGFACE_VISION_MODEL=Salesforce/blip-image-captioning-base
LANGCHAIN_API_KEY=your-langchain-api-key-here
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=pr-internal-courtroom-93

# Database (SQLite)
DATABASE_URL=sqlite:///./data/app.db

# Service URLs (localhost)
FASTAPI_URL=http://localhost:9020
CHROMA_URL=http://localhost:8020
CHROMADB_PERSIST_DIRECTORY=./data/chroma
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379

# Application
REQUEST_TIMEOUT=600
LLM_TIMEOUT=300
LOG_LEVEL=INFO
IMAGES_STORAGE_DIR=./stored_images
EOF
    fi
    
    # Create data directories
    mkdir -p data/chroma
    mkdir -p logs
    mkdir -p stored_images
    
    echo ""
    echo -e "${YELLOW}📋 Local Environment Active${NC}"
    echo "  Database: SQLite (./data/app.db)"
    echo "  Services: Localhost URLs"
    echo ""
    echo -e "${BLUE}💡 Usage:${NC}"
    echo "  Local development:"
    echo "    cd src/chromadb && python chromadb_main.py &"
    echo "    cd src/fastapi && python main.py &"
    echo "    cd src/streamlit && streamlit run Home.py"
    echo ""
    echo "  EC2 deployment:"
    echo "    cd infrastructure/ec2-simple"
    echo "    ./deploy.sh && ./deploy-code.sh"
    echo ""
    echo -e "${YELLOW}🔧 Don't forget to configure your API keys in .env${NC}"
}

case "$1" in
    docker)
        switch_to_docker
        ;;
    local)
        switch_to_local
        ;;
    status)
        show_status
        ;;
    *)
        show_usage
        exit 1
        ;;
esac