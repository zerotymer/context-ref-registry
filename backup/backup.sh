#!/bin/sh
set -e

BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/llmref_${TIMESTAMP}.sql.gz"
RETAIN_DAYS="${BACKUP_RETAIN_DAYS:-7}"

mkdir -p "${BACKUP_DIR}"

echo "$(date -Iseconds) Starting backup to ${BACKUP_FILE}"

pg_dump \
  -h "${PGHOST}" \
  -p "${PGPORT:-5432}" \
  -U "${PGUSER}" \
  "${PGDATABASE}" \
  | gzip > "${BACKUP_FILE}"

echo "$(date -Iseconds) Backup complete: $(du -sh "${BACKUP_FILE}" | cut -f1)"

# Remove backups older than RETAIN_DAYS
find "${BACKUP_DIR}" -name "llmref_*.sql.gz" -mtime "+${RETAIN_DAYS}" -delete
echo "$(date -Iseconds) Cleaned up backups older than ${RETAIN_DAYS} days"
