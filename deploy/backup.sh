#!/bin/sh
# Nightly Postgres dump. Run from cron on the host, e.g.
#   15 2 * * * /opt/aeropulse/deploy/backup.sh /var/backups/aeropulse
# Copy the output directory to off-site storage with your tool of choice.
set -eu
OUT="${1:?usage: backup.sh <directory>}"
mkdir -p "$OUT"
FILE="$OUT/aeropulse-$(date -u +%Y%m%d).sql.gz"
docker compose -f "$(dirname "$0")/compose.yaml" exec -T db pg_dump -U aeropulse aeropulse | gzip > "$FILE"
find "$OUT" -name 'aeropulse-*.sql.gz' -mtime +30 -delete
echo "wrote $FILE"
