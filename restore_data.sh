#!/bin/bash
# restore_data.sh - Restore data from backups

if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup_directory>"
    echo "Example: $0 ./backups/20241209_143022"
    exit 1
fi

BACKUP_DIR="$1"

if [ ! -d "$BACKUP_DIR" ]; then
    echo "Error: Backup directory '$BACKUP_DIR' does not exist"
    exit 1
fi

echo "Restoring from: $BACKUP_DIR"
echo "WARNING: This will overwrite existing data!"
read -p "Are you sure? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Restore cancelled"
    exit 0
fi

# Stop containers first
echo "Stopping containers..."
docker compose down

# Restore ChromaDB data
if [ -f "$BACKUP_DIR/chromadata.tar.gz" ]; then
    echo "Restoring ChromaDB data..."
    docker run --rm -v dis_verification_genai_chromadata:/data -v "$PWD/$BACKUP_DIR:/backup" alpine tar xzf /backup/chromadata.tar.gz -C /data
    echo "ChromaDB data restored"
else
    echo "Warning: No ChromaDB backup found"
fi

# Restore Redis data
if [ -f "$BACKUP_DIR/redis-data.tar.gz" ]; then
    echo "Restoring Redis data..."
    docker run --rm -v dis_verification_genai_redis-data:/data -v "$PWD/$BACKUP_DIR:/backup" alpine tar xzf /backup/redis-data.tar.gz -C /data
    echo "Redis data restored"
else
    echo "Warning: No Redis backup found"
fi

# Restore Ollama models
if [ -f "$BACKUP_DIR/ollama_models.tar.gz" ]; then
    echo "Restoring Ollama models..."
    docker run --rm -v dis_verification_genai_ollama_models:/data -v "$PWD/$BACKUP_DIR:/backup" alpine tar xzf /backup/ollama_models.tar.gz -C /data
    echo "Ollama models restored"
else
    echo "Warning: No Ollama models backup found"
fi

# Start containers
echo "Starting containers..."
docker compose up -d

# Restore PostgreSQL data (must be done after containers are running)
if [ -f "$BACKUP_DIR/postgres_backup.sql" ]; then
    echo "Waiting for PostgreSQL to start..."
    sleep 10
    echo "Restoring PostgreSQL data..."
    docker compose exec -T postgres psql -U ${DB_USERNAME:-postgres} -d ${DB_NAME:-dis_verification} < "$BACKUP_DIR/postgres_backup.sql"
    echo "PostgreSQL data restored"
else
    echo "Warning: No PostgreSQL backup found"
fi

echo "Restore completed!"
echo "Containers should be starting up with restored data"