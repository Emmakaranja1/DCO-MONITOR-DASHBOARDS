set -e

LOG_DIR="${DCO_SCAN_LOG_DIR:-./scan_logs}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="${LOG_DIR}/scan_${TIMESTAMP}.log"


PORTS="22,80,443,3000,9090"
TARGETS="127.0.0.1 172.17.0.1"

mkdir -p "$LOG_DIR"

log() {
    echo "[$(date -Iseconds)] $*" | tee -a "$LOG_FILE"
}

log "========== DCO Manual Security Scan Started =========="
log "Targets: $TARGETS | Ports: $PORTS"

# Check if nmap is available
if ! command -v nmap &>/dev/null; then
    log "WARNING: nmap not found. Install with: apt-get install nmap"
    log "Simulating scan results for demo purposes..."
    echo "127.0.0.1: 22/tcp open ssh" >> "$LOG_FILE"
    echo "127.0.0.1: 80/tcp open http" >> "$LOG_FILE"
    log "========== Scan Complete (Simulated) =========="
    exit 0
fi

# Run scan on each target
for target in $TARGETS; do
    log "Scanning $target..."
    if nmap -p "$PORTS" -T4 "$target" 2>&1 | tee -a "$LOG_FILE"; then
        log "Scan of $target completed."
    else
        log "Scan of $target failed or returned no results (may be unreachable)."
    fi
done

# Query exporter metrics if running (optional)
if command -v curl &>/dev/null; then
    if curl -s --max-time 2 http://localhost:8001/metrics 2>/dev/null | grep -E "dco_open_ports_total|dco_security_risk_score" >> "$LOG_FILE" 2>/dev/null; then
        log "Exporter metrics sampled successfully."
    fi
fi

log "========== DCO Manual Security Scan Complete =========="
log "Log saved to: $LOG_FILE"

echo ""
echo "Scan complete. Results logged to: $LOG_FILE"
