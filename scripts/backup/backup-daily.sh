#!/bin/bash
# Daily Incremental Backup Script
# Scheduled to run daily at 2 AM via cron
# Usage: ./backup-daily.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/local-llm-webapp}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$BACKUP_DIR/logs/backup-daily_$TIMESTAMP.log"

# Create backup and log directories
mkdir -p "$BACKUP_DIR/daily"
mkdir -p "$BACKUP_DIR/logs"

echo "========================================" | tee -a "$LOG_FILE"
echo "Daily Incremental Backup - $TIMESTAMP" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Database credentials from environment or .env file
if [ -f "$PROJECT_ROOT/backend/.env" ]; then
    source "$PROJECT_ROOT/backend/.env"
fi

DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_NAME="${POSTGRES_DB:-llm_webapp}"
DB_USER="${POSTGRES_USER:-postgres}"
DB_PASSWORD="${POSTGRES_PASSWORD}"

# Export password for pg_dump
export PGPASSWORD="$DB_PASSWORD"

# Step 1: Incremental Database Backup
echo "Step 1: Database incremental backup..." | tee -a "$LOG_FILE"
DB_BACKUP_FILE="$BACKUP_DIR/daily/db_incremental_$TIMESTAMP.sql"

pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    --format=plain \
    --no-owner \
    --no-privileges \
    --file="$DB_BACKUP_FILE" 2>> "$LOG_FILE"

if [ $? -eq 0 ]; then
    DB_SIZE=$(du -h "$DB_BACKUP_FILE" | cut -f1)
    echo "✓ Database backup completed: $DB_BACKUP_FILE ($DB_SIZE)" | tee -a "$LOG_FILE"
else
    echo "ERROR: Database backup failed" | tee -a "$LOG_FILE"
    exit 1
fi

# Compress database backup
gzip "$DB_BACKUP_FILE"
echo "✓ Database backup compressed: ${DB_BACKUP_FILE}.gz" | tee -a "$LOG_FILE"

# Step 2: Incremental Document Backup (rsync)
echo "" | tee -a "$LOG_FILE"
echo "Step 2: Document incremental backup..." | tee -a "$LOG_FILE"

DOCUMENT_SOURCE="$PROJECT_ROOT/backend/uploads"
DOCUMENT_BACKUP="$BACKUP_DIR/daily/documents_$TIMESTAMP"

if [ -d "$DOCUMENT_SOURCE" ]; then
    rsync -av --link-dest="$BACKUP_DIR/daily/latest" \
        "$DOCUMENT_SOURCE/" \
        "$DOCUMENT_BACKUP/" 2>> "$LOG_FILE"

    if [ $? -eq 0 ]; then
        DOC_SIZE=$(du -sh "$DOCUMENT_BACKUP" | cut -f1)
        echo "✓ Document backup completed: $DOCUMENT_BACKUP ($DOC_SIZE)" | tee -a "$LOG_FILE"

        # Update symlink to latest backup
        ln -sfn "$DOCUMENT_BACKUP" "$BACKUP_DIR/daily/latest"
    else
        echo "ERROR: Document backup failed" | tee -a "$LOG_FILE"
        exit 1
    fi
else
    echo "⚠ Document directory not found: $DOCUMENT_SOURCE" | tee -a "$LOG_FILE"
fi

# Step 3: Backup logs
echo "" | tee -a "$LOG_FILE"
echo "Step 3: Application logs backup..." | tee -a "$LOG_FILE"

LOG_SOURCE="$PROJECT_ROOT/backend/logs"
LOG_BACKUP="$BACKUP_DIR/daily/logs_$TIMESTAMP"

if [ -d "$LOG_SOURCE" ]; then
    cp -r "$LOG_SOURCE" "$LOG_BACKUP" 2>> "$LOG_FILE"
    tar -czf "${LOG_BACKUP}.tar.gz" -C "$BACKUP_DIR/daily" "logs_$TIMESTAMP" 2>> "$LOG_FILE"
    rm -rf "$LOG_BACKUP"
    echo "✓ Logs backup completed: ${LOG_BACKUP}.tar.gz" | tee -a "$LOG_FILE"
fi

# Step 4: Summary
echo "" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "Backup Summary:" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "Database: ${DB_BACKUP_FILE}.gz" | tee -a "$LOG_FILE"
echo "Documents: $DOCUMENT_BACKUP" | tee -a "$LOG_FILE"
echo "Logs: ${LOG_BACKUP}.tar.gz" | tee -a "$LOG_FILE"
echo "Total size: $(du -sh $BACKUP_DIR/daily | cut -f1)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "Backup completed successfully at $(date)" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

# Cleanup: Keep only last 7 days of daily backups
find "$BACKUP_DIR/daily" -name "db_incremental_*.sql.gz" -mtime +7 -delete 2>> "$LOG_FILE"
find "$BACKUP_DIR/daily" -type d -name "documents_*" -mtime +7 -exec rm -rf {} + 2>> "$LOG_FILE"
find "$BACKUP_DIR/daily" -name "logs_*.tar.gz" -mtime +7 -delete 2>> "$LOG_FILE"

echo "✓ Old backups cleaned up (7+ days)" | tee -a "$LOG_FILE"

# Unset password
unset PGPASSWORD

exit 0
