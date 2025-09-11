#!/bin/bash
# backup_data.sh - Backup all persistent data volumes

BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "Creating backups in: $BACKUP_DIR"

# Backup PostgreSQL
echo "Backing up PostgreSQL..."
docker compose exec -T postgres pg_dump -U ${DB_USERNAME:-postgres} ${DB_NAME:-dis_verification} > "$BACKUP_DIR/postgres_backup.sql"

# Backup ChromaDB (copy entire volume)
echo "Backing up ChromaDB..."
docker run --rm -v dis_verification_genai_chromadata:/data -v "$PWD/$BACKUP_DIR:/backup" alpine tar czf /backup/chromadata.tar.gz -C /data .

# Backup Redis 
echo "Backing up Redis..."
docker run --rm -v dis_verification_genai_redis-data:/data -v "$PWD/$BACKUP_DIR:/backup" alpine tar czf /backup/redis-data.tar.gz -C /data .

# Backup Ollama models (optional - these are large)
echo "Backing up Ollama models..."
docker run --rm -v dis_verification_genai_ollama_models:/data -v "$PWD/$BACKUP_DIR:/backup" alpine tar czf /backup/ollama_models.tar.gz -C /data .

echo "Backup completed in: $BACKUP_DIR"
echo "Files created:"
ls -la "$BACKUP_DIR"