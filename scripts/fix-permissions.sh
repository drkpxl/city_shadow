#!/usr/bin/env sh
# Adjust ownership and permissions for mounted volumes
set -e

TARGET_UID=${APP_UID:-1000}
TARGET_GID=${APP_GID:-1000}

chown -R $TARGET_UID:$TARGET_GID /app/uploads /app/outputs /app/temp /app/database 2>/dev/null || true
find /app/uploads /app/outputs /app/temp /app/database -type d -exec chmod 775 {} +
find /app/uploads /app/outputs /app/temp /app/database -type f -exec chmod 664 {} +
