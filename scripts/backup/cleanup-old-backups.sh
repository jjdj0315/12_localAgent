#!/bin/bash
# Cleanup Old Backups Script
# Removes backups older than retention policy
# Usage: ./cleanup-old-backups.sh

set -e

BACKUP_DIR="${BACKUP_DIR:-/var/backups/local-llm-webapp}"
LOG_FILE="$BACKUP_DIR/logs/cleanup_$(date +%Y%m%d_%H%M%S).log"

mkdir -p "$BACKUP_DIR/logs"

echo "========================================" | tee -a "$LOG_FILE"
echo "Backup Cleanup - $(date)" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Retention policies
DAILY_RETENTION_DAYS=7
WEEKLY_RETENTION_COUNT=4  # Keep minimum 4 weekly backups
LOG_RETENTION_DAYS=30

echo "Retention Policies:" | tee -a "$LOG_FILE"
echo "- Daily backups: $DAILY_RETENTION_DAYS days" | tee -a "$LOG_FILE"
echo "- Weekly backups: $WEEKLY_RETENTION_COUNT most recent" | tee -a "$LOG_FILE"
echo "- Log files: $LOG_RETENTION_DAYS days" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Cleanup daily backups older than retention period
echo "Cleaning up daily backups..." | tee -a "$LOG_FILE"
if [ -d "$BACKUP_DIR/daily" ]; then
    DAILY_REMOVED=0

    # Database backups
    for file in $(find "$BACKUP_DIR/daily" -name "db_incremental_*.sql.gz" -mtime +$DAILY_RETENTION_DAYS 2>/dev/null); do
        rm -f "$file"
        DAILY_REMOVED=$((DAILY_REMOVED + 1))
    done

    # Document backups
    for dir in $(find "$BACKUP_DIR/daily" -type d -name "documents_*" -mtime +$DAILY_RETENTION_DAYS 2>/dev/null); do
        rm -rf "$dir"
        DAILY_REMOVED=$((DAILY_REMOVED + 1))
    done

    # Log backups
    for file in $(find "$BACKUP_DIR/daily" -name "logs_*.tar.gz" -mtime +$DAILY_RETENTION_DAYS 2>/dev/null); do
        rm -f "$file"
        DAILY_REMOVED=$((DAILY_REMOVED + 1))
    done

    echo "✓ Removed $DAILY_REMOVED daily backup items older than $DAILY_RETENTION_DAYS days" | tee -a "$LOG_FILE"
else
    echo "⚠ Daily backup directory not found: $BACKUP_DIR/daily" | tee -a "$LOG_FILE"
fi

# Cleanup weekly backups (keep minimum count)
echo "" | tee -a "$LOG_FILE"
echo "Cleaning up weekly backups..." | tee -a "$LOG_FILE"
if [ -d "$BACKUP_DIR/weekly" ]; then
    WEEKLY_COUNT=$(ls -1 "$BACKUP_DIR/weekly"/db_full_week*.dump 2>/dev/null | wc -l)

    if [ "$WEEKLY_COUNT" -gt "$WEEKLY_RETENTION_COUNT" ]; then
        WEEKLY_REMOVED=0

        ls -1t "$BACKUP_DIR/weekly"/db_full_week*.dump | tail -n +$((WEEKLY_RETENTION_COUNT + 1)) | while read old_db; do
            WEEK_ID=$(echo "$old_db" | grep -oP 'week\K[0-9]+')

            rm -f "$BACKUP_DIR/weekly"/db_full_week${WEEK_ID}_*.dump 2>> "$LOG_FILE"
            rm -f "$BACKUP_DIR/weekly"/documents_full_week${WEEK_ID}_*.tar.gz 2>> "$LOG_FILE"
            rm -f "$BACKUP_DIR/weekly"/config_week${WEEK_ID}_*.tar.gz 2>> "$LOG_FILE"
            rm -f "$BACKUP_DIR/weekly"/logs_full_week${WEEK_ID}_*.tar.gz 2>> "$LOG_FILE"
            rm -f "$BACKUP_DIR/weekly"/checksums_week${WEEK_ID}_*.sha256 2>> "$LOG_FILE"

            WEEKLY_REMOVED=$((WEEKLY_REMOVED + 1))
        done

        echo "✓ Removed $WEEKLY_REMOVED old weekly backup sets (keeping $WEEKLY_RETENTION_COUNT most recent)" | tee -a "$LOG_FILE"
    else
        echo "✓ Weekly backups within retention policy ($WEEKLY_COUNT/$WEEKLY_RETENTION_COUNT)" | tee -a "$LOG_FILE"
    fi
else
    echo "⚠ Weekly backup directory not found: $BACKUP_DIR/weekly" | tee -a "$LOG_FILE"
fi

# Cleanup old log files
echo "" | tee -a "$LOG_FILE"
echo "Cleaning up old log files..." | tee -a "$LOG_FILE"
if [ -d "$BACKUP_DIR/logs" ]; then
    LOG_REMOVED=$(find "$BACKUP_DIR/logs" -name "*.log" -mtime +$LOG_RETENTION_DAYS -delete -print 2>/dev/null | wc -l)
    echo "✓ Removed $LOG_REMOVED log files older than $LOG_RETENTION_DAYS days" | tee -a "$LOG_FILE"
fi

# Calculate current backup disk usage
echo "" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "Current Backup Disk Usage:" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
if [ -d "$BACKUP_DIR/daily" ]; then
    echo "Daily: $(du -sh $BACKUP_DIR/daily 2>/dev/null | cut -f1)" | tee -a "$LOG_FILE"
fi
if [ -d "$BACKUP_DIR/weekly" ]; then
    echo "Weekly: $(du -sh $BACKUP_DIR/weekly 2>/dev/null | cut -f1)" | tee -a "$LOG_FILE"
fi
echo "Total: $(du -sh $BACKUP_DIR 2>/dev/null | cut -f1)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "Cleanup completed successfully at $(date)" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

exit 0
