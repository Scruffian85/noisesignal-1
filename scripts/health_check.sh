#!/bin/bash

# NoiseSignal Health Check Script
# Monitors the health of the NoiseSignal automation system

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(dirname "$SCRIPT_DIR")"
LOG_FILE="${APP_DIR}/data/logs/health_check.log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to check file age
check_file_age() {
    local file_path="$1"
    local max_age_hours="$2"
    local description="$3"

    if [ -f "$file_path" ]; then
        local file_age_seconds=$(( $(date +%s) - $(stat -c %Y "$file_path" 2>/dev/null || stat -f %m "$file_path") ))
        local file_age_hours=$(( file_age_seconds / 3600 ))

        if [ $file_age_hours -gt $max_age_hours ]; then
            log "WARNING: $description is $file_age_hours hours old (max: $max_age_hours)"
            return 1
        else
            log "OK: $description is current ($file_age_hours hours old)"
            return 0
        fi
    else
        log "WARNING: $description not found at $file_path"
        return 1
    fi
}

# Function to check if process is running
check_process() {
    local process_name="$1"
    if pgrep -f "$process_name" > /dev/null; then
        log "OK: Process '$process_name' is running"
        return 0
    else
        log "INFO: Process '$process_name' is not running (this may be normal)"
        return 1
    fi
}

# Function to check disk space
check_disk_space() {
    local path="$1"
    local min_free_mb="$2"

    local free_space_kb=$(df "$path" | awk 'NR==2 {print $4}')
    local free_space_mb=$(( free_space_kb / 1024 ))

    if [ $free_space_mb -lt $min_free_mb ]; then
        log "WARNING: Low disk space on $path: ${free_space_mb}MB free (min: ${min_free_mb}MB)"
        return 1
    else
        log "OK: Disk space on $path: ${free_space_mb}MB free"
        return 0
    fi
}

# Function to validate configuration
check_configuration() {
    local config_ok=0

    # Check if .env file exists
    if [ -f "$APP_DIR/.env" ]; then
        log "OK: Environment configuration file found"

        # Source the .env file and check required variables
        set -a
        source "$APP_DIR/.env"
        set +a

        if [ -z "$GMAIL_ADDRESS" ]; then
            log "WARNING: GMAIL_ADDRESS not set in environment"
            config_ok=1
        fi

        if [ -z "$GMAIL_APP_PASSWORD" ]; then
            log "WARNING: GMAIL_APP_PASSWORD not set in environment"
            config_ok=1
        fi

    else
        log "WARNING: No .env file found"
        config_ok=1
    fi

    # Check required files
    local required_files=("secret.json" "scheduler.py" "main.py" "config.py" "email_notifier.py")
    for file in "${required_files[@]}"; do
        if [ -f "$APP_DIR/$file" ]; then
            log "OK: Required file $file exists"
        else
            log "ERROR: Required file $file missing"
            config_ok=1
        fi
    done

    return $config_ok
}

# Function to check YouTube token
check_youtube_token() {
    local token_file="$APP_DIR/token.pickle"

    if [ -f "$token_file" ]; then
        # Check if token is recent (less than 30 days old)
        if check_file_age "$token_file" 720 "YouTube token"; then  # 30 days = 720 hours
            return 0
        else
            log "WARNING: YouTube token may need refresh"
            return 1
        fi
    else
        log "WARNING: YouTube token file not found"
        return 1
    fi
}

# Main health check routine
main() {
    log "Starting NoiseSignal health check"
    log "Application directory: $APP_DIR"

    local overall_status=0

    # Change to application directory
    cd "$APP_DIR"

    # Check configuration
    log "Checking configuration..."
    if ! check_configuration; then
        overall_status=1
    fi

    # Check YouTube token
    log "Checking YouTube authentication..."
    if ! check_youtube_token; then
        overall_status=1
    fi

    # Check recent execution
    log "Checking recent execution..."
    if ! check_file_age "emerging_playlist_results.csv" 168 "Last execution results"; then  # 7 days
        overall_status=1
    fi

    # Check log files
    log "Checking log files..."
    check_file_age "data/logs/noisesignal.log" 168 "Application logs" || true

    # Check disk space (require at least 100MB free)
    log "Checking disk space..."
    if ! check_disk_space "$APP_DIR" 100; then
        overall_status=1
    fi

    # Check if any NoiseSignal processes are running
    log "Checking running processes..."
    check_process "scheduler.py" || true
    check_process "main.py" || true

    # Summary
    if [ $overall_status -eq 0 ]; then
        log "Health check completed: ALL CHECKS PASSED"
    else
        log "Health check completed: SOME ISSUES FOUND"
    fi

    # Clean up old health check logs (keep last 7 days)
    find "$(dirname "$LOG_FILE")" -name "health_check.log*" -type f -mtime +7 -delete 2>/dev/null || true

    return $overall_status
}

# Run health check
main "$@"