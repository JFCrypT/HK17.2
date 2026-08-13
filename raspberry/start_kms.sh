#!/usr/bin/env bash

# HK17.2 Raspberry Pi unattended KMS startup.
#
# The system Mosquitto service must be disabled once with:
#   sudo systemctl disable --now mosquitto
#
# This script deliberately refuses to reuse an arbitrary Mosquitto process.
# The broker must be the project instance started with raspberry/mosquitto.conf,
# whose listener is reachable from the laboratory LAN on TCP/1883.

set -u

export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
RASPBERRY_DIR="$SCRIPT_DIR"
PYTHON="$RASPBERRY_DIR/.venv/bin/python"
MOSQUITTO_CONF="$RASPBERRY_DIR/mosquitto.conf"

LOG_DIR="$RASPBERRY_DIR/logs"
MOSQUITTO_LOG="$LOG_DIR/mosquitto.log"
KMS_LOG="$LOG_DIR/kms.log"

mkdir -p "$LOG_DIR"

timestamp() {
    date '+%Y-%m-%d %H:%M:%S'
}

log_kms() {
    printf '%s - %s\n' "$(timestamp)" "$*" >> "$KMS_LOG"
}

# Give Raspberry Pi OS, DHCP, and the user session a few seconds to settle.
sleep 8

cd "$PROJECT_DIR" || exit 1

printf '\n==================================================\n' >> "$KMS_LOG"
log_kms "Starting HK17.2 KMS stack"

if [[ ! -x "$PYTHON" ]]; then
    log_kms "ERROR: Python virtual environment not found at $PYTHON"
    exit 1
fi

MOSQUITTO_BIN="$(command -v mosquitto 2>/dev/null || true)"
if [[ -z "$MOSQUITTO_BIN" ]]; then
    log_kms "ERROR: mosquitto executable not found in PATH"
    exit 1
fi

# Accept an already-running broker only when it was started with this exact
# project configuration. Any other broker is an error because it may listen
# only on loopback and silently disconnect the ESP32 nodes.
PROJECT_BROKER_RUNNING=false
while IFS= read -r process_line; do
    [[ -z "$process_line" ]] && continue
    if [[ "$process_line" == *"-c $MOSQUITTO_CONF"* ]]; then
        PROJECT_BROKER_RUNNING=true
        break
    fi
done < <(pgrep -af mosquitto 2>/dev/null || true)

if [[ "$PROJECT_BROKER_RUNNING" != true ]]; then
    if pgrep -x mosquitto >/dev/null 2>&1; then
        log_kms "ERROR: another Mosquitto instance is already running. Refusing to use it."
        log_kms "Run once: sudo systemctl disable --now mosquitto"
        exit 1
    fi

    log_kms "Starting project Mosquitto: $MOSQUITTO_CONF"
    "$MOSQUITTO_BIN" -c "$MOSQUITTO_CONF" -v >> "$MOSQUITTO_LOG" 2>&1 &
    MOSQUITTO_PID=$!

    # Wait until the project listener is reachable on all IPv4 interfaces.
    BROKER_READY=false
    for _ in $(seq 1 20); do
        if ! kill -0 "$MOSQUITTO_PID" >/dev/null 2>&1; then
            break
        fi
        if ss -ltn 2>/dev/null | grep -q '0\.0\.0\.0:1883'; then
            BROKER_READY=true
            break
        fi
        sleep 0.5
    done

    if [[ "$BROKER_READY" != true ]]; then
        log_kms "ERROR: project Mosquitto did not expose 0.0.0.0:1883"
        kill "$MOSQUITTO_PID" >/dev/null 2>&1 || true
        exit 1
    fi
else
    if ! ss -ltn 2>/dev/null | grep -q '0\.0\.0\.0:1883'; then
        log_kms "ERROR: project Mosquitto exists but TCP/1883 is not listening on 0.0.0.0"
        exit 1
    fi
    log_kms "Project Mosquitto already running with the expected configuration"
fi

# Avoid duplicate FastAPI/KMS processes.
if pgrep -af '[r]aspberry/kms_web.py' >/dev/null 2>&1; then
    log_kms "KMS web service already running"
    exit 0
fi

log_kms "Starting kms_web.py (local MQTT 127.0.0.1:1883; LAN endpoint 192.168.1.40:1883)"
exec "$PYTHON" "$RASPBERRY_DIR/kms_web.py" \
    --broker-host 127.0.0.1 \
    --broker-port 1883 \
    --broker-lan-host 192.168.1.40 \
    --web-host 0.0.0.0 \
    --web-port 8000 \
    >> "$KMS_LOG" 2>&1
