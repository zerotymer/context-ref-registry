#!/bin/sh
set -e

if [ $# -gt 0 ]; then
    exec "$@"
fi

SCHEDULE="${BACKUP_SCHEDULE:-0 2 * * *}"

# Write wrapper that bakes in env vars at startup time
cat > /run-backup.sh << EOF
#!/bin/sh
PGPASSWORD="${PGPASSWORD}" \
PGHOST="${PGHOST}" \
PGPORT="${PGPORT:-5432}" \
PGUSER="${PGUSER}" \
PGDATABASE="${PGDATABASE}" \
BACKUP_RETAIN_DAYS="${BACKUP_RETAIN_DAYS:-7}" \
/backup.sh >> /var/log/backup.log 2>&1
EOF
chmod +x /run-backup.sh

# busybox crond reads from /var/spool/cron/crontabs/root
mkdir -p /var/spool/cron/crontabs
echo "${SCHEDULE} /run-backup.sh" > /var/spool/cron/crontabs/root
chmod 600 /var/spool/cron/crontabs/root

echo "Backup scheduler started (schedule: ${SCHEDULE})"

exec crond -f -d 8
