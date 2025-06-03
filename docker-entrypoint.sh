#!/usr/bin/env sh
set -e
/app/scripts/fix-permissions.sh
exec "$@"

