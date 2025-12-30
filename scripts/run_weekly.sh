#!/bin/bash

# NoiseSignal Weekly Execution Script
# This script runs the automated music discovery process

set -e  # Exit on any error

# Set PATH to ensure python3 is available (critical for cron environment)
export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(dirname "$SCRIPT_DIR")"
LOG_FILE="${APP_DIR}/data/logs/weekly_execution.log"
LOCK_FILE="${APP_DIR}/data/noisesignal.lock"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to cleanup on exit
cleanup() {
    if [ -f "$LOCK_FILE" ]; then
        rm -f "$LOCK_FILE"
        log "Lock file removed"
    fi
}

# Set up trap for cleanup
trap cleanup EXIT

# Check if another instance is running
if [ -f "$LOCK_FILE" ]; then
    PID=$(cat "$LOCK_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        log "Another instance is already running (PID: $PID). Exiting."
        exit 1
    else
        log "Stale lock file found. Removing..."
        rm -f "$LOCK_FILE"
    fi
fi

# Create lock file
echo $$ > "$LOCK_FILE"
log "Lock file created with PID: $$"

# Change to application directory
cd "$APP_DIR"

log "Starting NoiseSignal weekly execution"
log "Working directory: $(pwd)"

# Check if Python virtual environment exists
if [ -d "venv" ]; then
    log "Activating Python virtual environment"
    source venv/bin/activate
elif [ -d ".venv" ]; then
    log "Activating Python virtual environment (.venv)"
    source .venv/bin/activate
else
    log "No virtual environment found, using system Python"
fi

# Check Python environment
log "Python version: $(python3 --version)"
log "Python path: $(which python3)"

# Verify required files exist
REQUIRED_FILES=("secret.json" "scheduler.py" "main.py" "config.py")
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        log "ERROR: Required file $file not found"
        exit 1
    fi
done

log "All required files found"

# Set environment variables if .env file exists
if [ -f ".env" ]; then
    log "Loading environment variables from .env file"
    set -a  # automatically export all variables
    source .env
    set +a
fi

# Run the scheduler
log "Executing NoiseSignal scheduler"
if python3 scheduler.py; then
    log "NoiseSignal execution completed successfully"
    EXIT_CODE=0
else
    log "NoiseSignal execution failed"
    EXIT_CODE=1
fi

# Optional: Clean up old log files (keep last 30 days)
find "$(dirname "$LOG_FILE")" -name "*.log" -type f -mtime +30 -delete 2>/dev/null || true

log "Weekly execution script completed with exit code: $EXIT_CODE"
exit $EXIT_CODE