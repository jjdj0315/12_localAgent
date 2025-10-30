#!/bin/bash
# Restore from Backup Script
# Restores database and documents from backup archives
# Usage: ./restore-from-backup.sh [--daily TIMESTAMP | --weekly WEEK_NUM]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/local-llm-webapp}"
RESTORE_LOG="$BACKUP_DIR/logs/restore_$(date +%Y%m%d_%H%M%S).log"

mkdir -p "$BACKUP_DIR/logs"

echo "========================================" | tee -a "$RESTORE_LOG"
echo "Restore from Backup - $(date)" | tee -a "$RESTORE_LOG"
echo "========================================" | tee -a "$RESTORE_LOG"
echo "" | tee -a "$RESTORE_LOG"

# Parse arguments
BACKUP_TYPE=""
BACKUP_ID=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --daily)
            BACKUP_TYPE="daily"
            BACKUP_ID="$2"
            shift 2
            ;;
        --weekly)
            BACKUP_TYPE="weekly"
            BACKUP_ID="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [--daily TIMESTAMP | --weekly WEEK_NUM]"
            echo ""
            echo "Examples:"
            echo "  $0 --daily 20250130_020005    # Restore from daily backup"
            echo "  $0 --weekly 05                 # Restore from weekly backup (week 5)"
            echo ""
            echo "List available backups:"
            echo "  ls -lh $BACKUP_DIR/daily/db_incremental_*.sql.gz"
            echo "  ls -lh $BACKUP_DIR/weekly/db_full_week*.dump"
            exit 0
            ;;
        *)
            echo "ERROR: Unknown option: $1" | tee -a "$RESTORE_LOG"
            echo "Use --help for usage information" | tee -a "$RESTORE_LOG"
            exit 1
            ;;
    esac
done

if [ -z "$BACKUP_TYPE" ]; then
    echo "ERROR: Backup type not specified" | tee -a "$RESTORE_LOG"
    echo "Use --help for usage information" | tee -a "$RESTORE_LOG"
    exit 1
fi

# Database credentials from environment or .env file
if [ -f "$PROJECT_ROOT/backend/.env" ]; then
    source "$PROJECT_ROOT/backend/.env"
fi

DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_NAME="${POSTGRES_DB:-llm_webapp}"
DB_USER="${POSTGRES_USER:-postgres}"
DB_PASSWORD="${POSTGRES_PASSWORD}"

export PGPASSWORD="$DB_PASSWORD"

# Confirmation prompt
echo "⚠ WARNING: This will OVERWRITE existing data!" | tee -a "$RESTORE_LOG"
echo "Backup type: $BACKUP_TYPE" | tee -a "$RESTORE_LOG"
echo "Backup ID: $BACKUP_ID" | tee -a "$RESTORE_LOG"
echo "Database: $DB_NAME on $DB_HOST:$DB_PORT" | tee -a "$RESTORE_LOG"
echo "" | tee -a "$RESTORE_LOG"
read -p "Are you sure you want to continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Restore cancelled by user" | tee -a "$RESTORE_LOG"
    exit 0
fi

# Restore based on backup type
if [ "$BACKUP_TYPE" == "daily" ]; then
    echo "" | tee -a "$RESTORE_LOG"
    echo "Restoring from daily backup: $BACKUP_ID" | tee -a "$RESTORE_LOG"
    echo "========================================" | tee -a "$RESTORE_LOG"

    # Step 1: Restore database
    DB_BACKUP="$BACKUP_DIR/daily/db_incremental_${BACKUP_ID}.sql.gz"
    if [ ! -f "$DB_BACKUP" ]; then
        echo "ERROR: Database backup not found: $DB_BACKUP" | tee -a "$RESTORE_LOG"
        exit 1
    fi

    echo "Step 1: Restoring database from $DB_BACKUP..." | tee -a "$RESTORE_LOG"

    # Drop and recreate database (requires superuser or db owner privileges)
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres \
        -c "DROP DATABASE IF EXISTS ${DB_NAME};" 2>> "$RESTORE_LOG"
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres \
        -c "CREATE DATABASE ${DB_NAME};" 2>> "$RESTORE_LOG"

    # Restore from plain SQL dump
    gunzip -c "$DB_BACKUP" | psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" 2>> "$RESTORE_LOG"

    if [ $? -eq 0 ]; then
        echo "✓ Database restored successfully" | tee -a "$RESTORE_LOG"
    else
        echo "ERROR: Database restore failed" | tee -a "$RESTORE_LOG"
        exit 1
    fi

    # Step 2: Restore documents
    echo "" | tee -a "$RESTORE_LOG"
    echo "Step 2: Restoring documents..." | tee -a "$RESTORE_LOG"

    DOCUMENT_BACKUP="$BACKUP_DIR/daily/documents_${BACKUP_ID}"
    if [ -d "$DOCUMENT_BACKUP" ]; then
        DOCUMENT_TARGET="$PROJECT_ROOT/backend/uploads"

        # Backup existing documents to temporary location
        if [ -d "$DOCUMENT_TARGET" ]; then
            mv "$DOCUMENT_TARGET" "${DOCUMENT_TARGET}_backup_$(date +%Y%m%d_%H%M%S)" 2>> "$RESTORE_LOG"
        fi

        # Restore from backup
        rsync -av "$DOCUMENT_BACKUP/" "$DOCUMENT_TARGET/" 2>> "$RESTORE_LOG"

        if [ $? -eq 0 ]; then
            echo "✓ Documents restored successfully to $DOCUMENT_TARGET" | tee -a "$RESTORE_LOG"
        else
            echo "ERROR: Document restore failed" | tee -a "$RESTORE_LOG"
            exit 1
        fi
    else
        echo "⚠ Document backup not found: $DOCUMENT_BACKUP" | tee -a "$RESTORE_LOG"
    fi

    # Step 3: Restore logs (optional)
    echo "" | tee -a "$RESTORE_LOG"
    echo "Step 3: Restoring application logs (optional)..." | tee -a "$RESTORE_LOG"

    LOG_BACKUP="$BACKUP_DIR/daily/logs_${BACKUP_ID}.tar.gz"
    if [ -f "$LOG_BACKUP" ]; then
        LOG_TARGET="$PROJECT_ROOT/backend/logs"
        mkdir -p "$LOG_TARGET"

        tar -xzf "$LOG_BACKUP" -C "$PROJECT_ROOT/backend" 2>> "$RESTORE_LOG"
        echo "✓ Logs restored to $LOG_TARGET" | tee -a "$RESTORE_LOG"
    else
        echo "⚠ Log backup not found: $LOG_BACKUP" | tee -a "$RESTORE_LOG"
    fi

elif [ "$BACKUP_TYPE" == "weekly" ]; then
    echo "" | tee -a "$RESTORE_LOG"
    echo "Restoring from weekly backup: Week $BACKUP_ID" | tee -a "$RESTORE_LOG"
    echo "========================================" | tee -a "$RESTORE_LOG"

    # Find most recent backup for this week
    WEEK_BACKUPS=$(ls -t "$BACKUP_DIR/weekly"/db_full_week${BACKUP_ID}_*.dump 2>/dev/null | head -n 1)

    if [ -z "$WEEK_BACKUPS" ]; then
        echo "ERROR: No backups found for week $BACKUP_ID" | tee -a "$RESTORE_LOG"
        exit 1
    fi

    DB_BACKUP="$WEEK_BACKUPS"
    TIMESTAMP=$(echo "$DB_BACKUP" | grep -oP '[0-9]{8}_[0-9]{6}')

    # Step 1: Verify checksums
    echo "Step 1: Verifying backup integrity..." | tee -a "$RESTORE_LOG"
    CHECKSUM_FILE="$BACKUP_DIR/weekly/checksums_week${BACKUP_ID}_${TIMESTAMP}.sha256"

    if [ -f "$CHECKSUM_FILE" ]; then
        cd "$BACKUP_DIR/weekly"
        sha256sum -c "$CHECKSUM_FILE" 2>&1 | tee -a "$RESTORE_LOG"

        if [ $? -eq 0 ]; then
            echo "✓ Checksums verified successfully" | tee -a "$RESTORE_LOG"
        else
            echo "ERROR: Checksum verification failed" | tee -a "$RESTORE_LOG"
            exit 1
        fi
    else
        echo "⚠ Checksum file not found, skipping verification" | tee -a "$RESTORE_LOG"
    fi

    # Step 2: Restore database
    echo "" | tee -a "$RESTORE_LOG"
    echo "Step 2: Restoring database from $DB_BACKUP..." | tee -a "$RESTORE_LOG"

    # Drop and recreate database
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres \
        -c "DROP DATABASE IF EXISTS ${DB_NAME};" 2>> "$RESTORE_LOG"
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres \
        -c "CREATE DATABASE ${DB_NAME};" 2>> "$RESTORE_LOG"

    # Restore from custom format dump
    pg_restore -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        --no-owner --no-privileges \
        "$DB_BACKUP" 2>> "$RESTORE_LOG"

    if [ $? -eq 0 ]; then
        echo "✓ Database restored successfully" | tee -a "$RESTORE_LOG"
    else
        echo "ERROR: Database restore failed" | tee -a "$RESTORE_LOG"
        exit 1
    fi

    # Step 3: Restore documents
    echo "" | tee -a "$RESTORE_LOG"
    echo "Step 3: Restoring documents..." | tee -a "$RESTORE_LOG"

    DOCUMENT_BACKUP="$BACKUP_DIR/weekly/documents_full_week${BACKUP_ID}_${TIMESTAMP}.tar.gz"
    if [ -f "$DOCUMENT_BACKUP" ]; then
        DOCUMENT_TARGET="$PROJECT_ROOT/backend/uploads"

        # Backup existing documents
        if [ -d "$DOCUMENT_TARGET" ]; then
            mv "$DOCUMENT_TARGET" "${DOCUMENT_TARGET}_backup_$(date +%Y%m%d_%H%M%S)" 2>> "$RESTORE_LOG"
        fi

        # Extract documents
        mkdir -p "$(dirname $DOCUMENT_TARGET)"
        tar -xzf "$DOCUMENT_BACKUP" -C "$(dirname $DOCUMENT_TARGET)" 2>> "$RESTORE_LOG"

        if [ $? -eq 0 ]; then
            echo "✓ Documents restored successfully to $DOCUMENT_TARGET" | tee -a "$RESTORE_LOG"
        else
            echo "ERROR: Document restore failed" | tee -a "$RESTORE_LOG"
            exit 1
        fi
    else
        echo "⚠ Document backup not found: $DOCUMENT_BACKUP" | tee -a "$RESTORE_LOG"
    fi

    # Step 4: Restore configuration
    echo "" | tee -a "$RESTORE_LOG"
    echo "Step 4: Restoring configuration files..." | tee -a "$RESTORE_LOG"

    CONFIG_BACKUP="$BACKUP_DIR/weekly/config_week${BACKUP_ID}_${TIMESTAMP}.tar.gz"
    if [ -f "$CONFIG_BACKUP" ]; then
        tar -xzf "$CONFIG_BACKUP" -C "$PROJECT_ROOT" 2>> "$RESTORE_LOG"
        echo "✓ Configuration files restored" | tee -a "$RESTORE_LOG"
    else
        echo "⚠ Configuration backup not found: $CONFIG_BACKUP" | tee -a "$RESTORE_LOG"
    fi

    # Step 5: Restore logs
    echo "" | tee -a "$RESTORE_LOG"
    echo "Step 5: Restoring application logs..." | tee -a "$RESTORE_LOG"

    LOG_BACKUP="$BACKUP_DIR/weekly/logs_full_week${BACKUP_ID}_${TIMESTAMP}.tar.gz"
    if [ -f "$LOG_BACKUP" ]; then
        tar -xzf "$LOG_BACKUP" -C "$PROJECT_ROOT/backend" 2>> "$RESTORE_LOG"
        echo "✓ Logs restored" | tee -a "$RESTORE_LOG"
    else
        echo "⚠ Log backup not found: $LOG_BACKUP" | tee -a "$RESTORE_LOG"
    fi
fi

# Summary
echo "" | tee -a "$RESTORE_LOG"
echo "========================================" | tee -a "$RESTORE_LOG"
echo "Restore Summary:" | tee -a "$RESTORE_LOG"
echo "========================================" | tee -a "$RESTORE_LOG"
echo "Backup type: $BACKUP_TYPE" | tee -a "$RESTORE_LOG"
echo "Backup ID: $BACKUP_ID" | tee -a "$RESTORE_LOG"
echo "Database: Restored to $DB_NAME" | tee -a "$RESTORE_LOG"
echo "Documents: Restored to $PROJECT_ROOT/backend/uploads" | tee -a "$RESTORE_LOG"
echo "" | tee -a "$RESTORE_LOG"
echo "⚠ IMPORTANT: Please restart the application to apply changes:" | tee -a "$RESTORE_LOG"
echo "  docker-compose restart backend" | tee -a "$RESTORE_LOG"
echo "" | tee -a "$RESTORE_LOG"
echo "Restore completed successfully at $(date)" | tee -a "$RESTORE_LOG"
echo "========================================" | tee -a "$RESTORE_LOG"

# Unset password
unset PGPASSWORD

exit 0
