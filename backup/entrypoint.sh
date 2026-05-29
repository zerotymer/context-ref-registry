#!/bin/sh
set -e

# Allow direct command override (e.g. docker compose run backup /backup.sh)
if [ $# -gt 0 ]; then
    exec "$@"
fi

# Install crontab entry for the backup job
echo "${BACKUP_SCHEDULE:-0 2 * * *} PGPASSWORD=\"${PGPASSWORD}\" PGHOST=\"${PGHOST}\" PGPORT=\"${PGPORT:-5432}\" PGUSER=\"${PGUSER}\" PGDATABASE=\"${PGDATABASE}\" BACKUP_RETAIN_DAYS=\"${BACKUP_RETAIN_DAYS:-7}\" /backup.sh >> /var/log/backup.log 2>&1" | crontab -

echo "Backup scheduler started (schedule: ${BACKUP_SCHEDULE:-0 2 * * *})"

# Run crond in foreground
exec crond -f -l 2
