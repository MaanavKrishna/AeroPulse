#!/bin/sh
# Collect, rebuild and export every AEROPULSE_COLLECT_EVERY seconds (default 6 hours).
# A failed run is logged and retried next cycle; it never stops the loop.
set -u
EVERY="${AEROPULSE_COLLECT_EVERY:-21600}"
aeropulse db upgrade
while true; do
  echo "$(date -u +%FT%TZ) collect"
  aeropulse collect || echo "collect finished with problems; see /status"
  aeropulse build && aeropulse export || echo "build or export failed"
  sleep "$EVERY"
done
