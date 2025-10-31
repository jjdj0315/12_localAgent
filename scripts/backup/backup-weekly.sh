#!/bin/bash
# Weekly Full Backup Script
# Scheduled to run every Sunday via cron
# Usage: ./backup-weekly.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/local-llm-webapp}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
WEEK_NUM=$(date +%U)
LOG_FILE="$BACKUP_DIR/logs/backup-weekly_$TIMESTAMP.log"

# Create backup and log directories
mkdir -p "$BACKUP_DIR/weekly"
mkdir -p "$BACKUP_DIR/logs"

echo "========================================" | tee -a "$LOG_FILE"
echo "Weekly Full Backup - $TIMESTAMP (Week $WEEK_NUM)" | tee -a "$LOG_FILE"
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

# Step 1: Full Database Backup (custom format for faster restore)
echo "Step 1: Database full backup (custom format)..." | tee -a "$LOG_FILE"
DB_BACKUP_FILE="$BACKUP_DIR/weekly/db_full_week${WEEK_NUM}_$TIMESTAMP.dump"

pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    --format=custom \
    --compress=9 \
    --file="$DB_BACKUP_FILE" 2>> "$LOG_FILE"

if [ $? -eq 0 ]; then
    DB_SIZE=$(du -h "$DB_BACKUP_FILE" | cut -f1)
    echo "✓ Database full backup completed: $DB_BACKUP_FILE ($DB_SIZE)" | tee -a "$LOG_FILE"
else
    echo "ERROR: Database backup failed" | tee -a "$LOG_FILE"
    exit 1
fi

# Step 2: Full Document Backup (tar archive)
echo "" | tee -a "$LOG_FILE"
echo "Step 2: Document full backup..." | tee -a "$LOG_FILE"

DOCUMENT_SOURCE="$PROJECT_ROOT/backend/uploads"
DOCUMENT_BACKUP="$BACKUP_DIR/weekly/documents_full_week${WEEK_NUM}_$TIMESTAMP.tar.gz"

if [ -d "$DOCUMENT_SOURCE" ]; then
    tar -czf "$DOCUMENT_BACKUP" -C "$(dirname $DOCUMENT_SOURCE)" "$(basename $DOCUMENT_SOURCE)" 2>> "$LOG_FILE"

    if [ $? -eq 0 ]; then
        DOC_SIZE=$(du -h "$DOCUMENT_BACKUP" | cut -f1)
        echo "✓ Document full backup completed: $DOCUMENT_BACKUP ($DOC_SIZE)" | tee -a "$LOG_FILE"
    else
        echo "ERROR: Document backup failed" | tee -a "$LOG_FILE"
        exit 1
    fi
else
    echo "⚠ Document directory not found: $DOCUMENT_SOURCE" | tee -a "$LOG_FILE"
fi

# Step 3: Full Configuration Backup
echo "" | tee -a "$LOG_FILE"
echo "Step 3: Configuration backup..." | tee -a "$LOG_FILE"

CONFIG_BACKUP="$BACKUP_DIR/weekly/config_week${WEEK_NUM}_$TIMESTAMP.tar.gz"
tar -czf "$CONFIG_BACKUP" \
    -C "$PROJECT_ROOT" \
    backend/.env \
    backend/alembic.ini \
    docker-compose.yml \
    2>> "$LOG_FILE"

if [ $? -eq 0 ]; then
    CONFIG_SIZE=$(du -h "$CONFIG_BACKUP" | cut -f1)
    echo "✓ Configuration backup completed: $CONFIG_BACKUP ($CONFIG_SIZE)" | tee -a "$LOG_FILE"
fi

# Step 4: Application logs full backup
echo "" | tee -a "$LOG_FILE"
echo "Step 4: Application logs full backup..." | tee -a "$LOG_FILE"

LOG_SOURCE="$PROJECT_ROOT/backend/logs"
LOG_BACKUP="$BACKUP_DIR/weekly/logs_full_week${WEEK_NUM}_$TIMESTAMP.tar.gz"

if [ -d "$LOG_SOURCE" ]; then
    tar -czf "$LOG_BACKUP" -C "$(dirname $LOG_SOURCE)" "$(basename $LOG_SOURCE)" 2>> "$LOG_FILE"
    echo "✓ Logs full backup completed: $LOG_BACKUP" | tee -a "$LOG_FILE"
fi

# Step 5: Create verification checksums
echo "" | tee -a "$LOG_FILE"
echo "Step 5: Creating checksums..." | tee -a "$LOG_FILE"

CHECKSUM_FILE="$BACKUP_DIR/weekly/checksums_week${WEEK_NUM}_$TIMESTAMP.sha256"
cd "$BACKUP_DIR/weekly"
sha256sum db_full_week${WEEK_NUM}_$TIMESTAMP.dump > "$CHECKSUM_FILE" 2>> "$LOG_FILE"
sha256sum documents_full_week${WEEK_NUM}_$TIMESTAMP.tar.gz >> "$CHECKSUM_FILE" 2>> "$LOG_FILE"
sha256sum config_week${WEEK_NUM}_$TIMESTAMP.tar.gz >> "$CHECKSUM_FILE" 2>> "$LOG_FILE"
sha256sum logs_full_week${WEEK_NUM}_$TIMESTAMP.tar.gz >> "$CHECKSUM_FILE" 2>> "$LOG_FILE"

echo "✓ Checksums created: $CHECKSUM_FILE" | tee -a "$LOG_FILE"

# Step 6: Summary
echo "" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "Weekly Backup Summary:" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "Database: $DB_BACKUP_FILE" | tee -a "$LOG_FILE"
echo "Documents: $DOCUMENT_BACKUP" | tee -a "$LOG_FILE"
echo "Configuration: $CONFIG_BACKUP" | tee -a "$LOG_FILE"
echo "Logs: $LOG_BACKUP" | tee -a "$LOG_FILE"
echo "Checksums: $CHECKSUM_FILE" | tee -a "$LOG_FILE"
echo "Total size: $(du -sh $BACKUP_DIR/weekly | cut -f1)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "Weekly backup completed successfully at $(date)" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

# Cleanup: Keep minimum 4 weekly full backups (30 days retention)
WEEKLY_BACKUP_COUNT=$(ls -1 "$BACKUP_DIR/weekly"/db_full_week*.dump 2>/dev/null | wc -l)
if [ "$WEEKLY_BACKUP_COUNT" -gt 4 ]; then
    echo "" | tee -a "$LOG_FILE"
    echo "Cleaning up old weekly backups (keeping 4 most recent)..." | tee -a "$LOG_FILE"

    ls -1t "$BACKUP_DIR/weekly"/db_full_week*.dump | tail -n +5 | while read old_db; do
        WEEK_ID=$(echo "$old_db" | grep -oP 'week\K[0-9]+')
        TIMESTAMP_ID=$(echo "$old_db" | grep -oP '[0-9]{8}_[0-9]{6}')

        rm -f "$BACKUP_DIR/weekly"/db_full_week${WEEK_ID}_*.dump 2>> "$LOG_FILE"
        rm -f "$BACKUP_DIR/weekly"/documents_full_week${WEEK_ID}_*.tar.gz 2>> "$LOG_FILE"
        rm -f "$BACKUP_DIR/weekly"/config_week${WEEK_ID}_*.tar.gz 2>> "$LOG_FILE"
        rm -f "$BACKUP_DIR/weekly"/logs_full_week${WEEK_ID}_*.tar.gz 2>> "$LOG_FILE"
        rm -f "$BACKUP_DIR/weekly"/checksums_week${WEEK_ID}_*.sha256 2>> "$LOG_FILE"

        echo "✓ Removed week $WEEK_ID backups" | tee -a "$LOG_FILE"
    done
fi

# Unset password
unset PGPASSWORD

exit 0
