#!/bin/bash

PROJECT_DIR="$HOME/Documents/Proyectos/HK17.2"
RASPBERRY_DIR="$PROJECT_DIR/raspberry"
PYTHON="$RASPBERRY_DIR/.venv/bin/python"

LOG_DIR="$RASPBERRY_DIR/logs"
MOSQUITTO_LOG="$LOG_DIR/mosquitto.log"
KMS_LOG="$LOG_DIR/kms.log"

mkdir -p "$LOG_DIR"

# Give Raspberry Pi OS a few seconds to finish booting.
sleep 10

cd "$PROJECT_DIR" || exit 1

echo "==================================================" >> "$KMS_LOG"
echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting HK17.2 KMS" >> "$KMS_LOG"

# Start the project Mosquitto broker if it is not already running.
if ! pgrep -x mosquitto >/dev/null 2>&1; then
    /usr/sbin/mosquitto \
        -c "$RASPBERRY_DIR/mosquitto.conf" \
        >> "$MOSQUITTO_LOG" 2>&1 &

    sleep 2
fi

# Prevent duplicate KMS instances.
if pgrep -f "raspberry/kms_web.py" >/dev/null 2>&1; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - KMS already running" >> "$KMS_LOG"
    exit 0
fi

# Start KMS/Web UI.
exec "$PYTHON" "$RASPBERRY_DIR/kms_web.py" >> "$KMS_LOG" 2>&1
