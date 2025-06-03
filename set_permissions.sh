#!/bin/bash

# Get the absolute path to the script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Define volume paths relative to the script's directory
UPLOADS_DIR="$SCRIPT_DIR/uploads"
OUTPUTS_DIR="$SCRIPT_DIR/outputs"
REGIONS_DIR="$SCRIPT_DIR/Regions"
DATABASE_DIR="$SCRIPT_DIR/database"
TEMP_DIR="$SCRIPT_DIR/temp"

# Define the UID and GID to set for the directories
# (1000 is a common default for the first non-root user)
# Adjust if your container runs as a different user/group
TARGET_UID=1000
TARGET_GID=1000

echo "Setting permissions for Docker volumes..."

# Create directories if they don't exist
echo "Creating directories if they don't exist..."
mkdir -p "$UPLOADS_DIR"
mkdir -p "$OUTPUTS_DIR"
mkdir -p "$REGIONS_DIR" # Should ideally exist with data, but create if missing
mkdir -p "$DATABASE_DIR"
mkdir -p "$TEMP_DIR"

# Set ownership
echo "Changing ownership to $TARGET_UID:$TARGET_GID for volumes..."
sudo chown -R $TARGET_UID:$TARGET_GID "$UPLOADS_DIR"
sudo chown -R $TARGET_UID:$TARGET_GID "$OUTPUTS_DIR"
sudo chown -R $TARGET_UID:$TARGET_GID "$REGIONS_DIR"
sudo chown -R $TARGET_UID:$TARGET_GID "$DATABASE_DIR"
sudo chown -R $TARGET_UID:$TARGET_GID "$TEMP_DIR"

# Set permissions (owner and group can read/write/execute, others can read/execute)
echo "Setting permissions (775) for volumes..."
sudo chmod -R 775 "$UPLOADS_DIR"
sudo chmod -R 775 "$OUTPUTS_DIR"
sudo chmod -R 775 "$REGIONS_DIR"
sudo chmod -R 775 "$DATABASE_DIR"
sudo chmod -R 775 "$TEMP_DIR"

echo "Permissions set successfully for uploads, outputs, Regions, database, and temp directories."
echo "Make sure the user/group ID $TARGET_UID:$TARGET_GID matches the user inside your Docker container if you encounter permission issues."
