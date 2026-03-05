import logging
import os
import sys
import time
from pathlib import Path

import psutil
from prometheus_client import Counter, Gauge, Info, start_http_server

try:
    import nmap
    NMAP_AVAILABLE = True
except ImportError:
    NMAP_AVAILABLE = False
    logging.warning("python-nmap not available - security metrics will be simulated")

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================
LOG_PATH = os.environ.get("DCO_LOG_PATH", "/var/log/dco_exporter.log")
LOG_DIR = Path(LOG_PATH).parent
try:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
except OSError:
    LOG_PATH = "/tmp/dco_exporter.log"
    LOG_DIR = Path(LOG_PATH).parent
    LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","message":"%(message)s"}',
    datefmt="%Y-%m-%dT%H:%M:%SZ",
    handlers=[
        logging.FileHandler(LOG_PATH, mode="a"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("dco_exporter")

# =============================================================================
# PROMETHEUS METRICS - System Monitoring
# =============================================================================
cpu_usage = Gauge("dco_cpu_usage_percent", "CPU usage percentage")
memory_usage_percent = Gauge("dco_memory_usage_percent", "Memory usage percentage")
memory_used_bytes = Gauge("dco_memory_used_bytes", "Memory used in bytes")
disk_usage_percent = Gauge("dco_disk_usage_percent", "Disk usage percentage", ["mountpoint"])
disk_io_read_bytes = Gauge("dco_disk_io_read_bytes_total", "Total disk read bytes")
disk_io_write_bytes = Gauge("dco_disk_io_write_bytes_total", "Total disk write bytes")
network_bytes_sent = Gauge("dco_network_bytes_sent_total", "Total network bytes sent")
network_bytes_recv = Gauge("dco_network_bytes_recv_total", "Total network bytes received")
load_average = Gauge("dco_load_average", "System load average", ["period"])

# =============================================================================
# PROMETHEUS METRICS - Security Monitoring
# =============================================================================
open_ports_total = Gauge("dco_open_ports_total", "Total number of open ports detected")
ports_by_service = Gauge("dco_ports_by_service", "Open ports by service name", ["target", "port", "state"])
security_risk_score = Gauge("dco_security_risk_score", "Calculated security risk score (0-100)")
vulnerabilities_detected = Gauge("dco_vulnerabilities_detected", "Simulated vulnerabilities detected")
high_risk_ports = Gauge("dco_high_risk_ports", "Number of high-risk ports exposed")
scan_errors_total = Counter("dco_scan_errors_total", "Total scan errors encountered")

# =============================================================================
# PROMETHEUS METRICS - Automation & Operations
# =============================================================================
exporter_uptime_seconds = Gauge("dco_exporter_uptime_seconds", "Exporter uptime in seconds")
last_scan_timestamp = Gauge("dco_last_scan_timestamp_seconds", "Unix timestamp of last security scan")
scan_duration_seconds = Gauge("dco_scan_duration_seconds", "Duration of last security scan in seconds")
exporter_info = Info("dco_exporter", "DCO Exporter build and version info")

# Ports of interest (SSH, HTTP, HTTPS, Grafana, Prometheus)
TARGET_PORTS = [22, 80, 443, 3000, 9090]

# High-risk ports if left exposed without proper controls
HIGH_RISK_PORTS = {22, 3389, 23, 21}  # SSH, RDP, Telnet, FTP

# Scan targets: localhost and docker default bridge subnet (safe, internal only)
SCAN_TARGETS = ["127.0.0.1", "172.17.0.1"]

# Startup time for uptime calculation
START_TIME = time.time()


def collect_system_metrics() -> None:
    """Collect CPU, memory, disk, network, and load metrics."""
    try:
        cpu_usage.set(psutil.cpu_percent(interval=1))
    except Exception as e:
        logger.warning("Failed to collect CPU metrics: %s", e)

    try:
        mem = psutil.virtual_memory()
        memory_usage_percent.set(mem.percent)
        memory_used_bytes.set(mem.used)
    except Exception as e:
        logger.warning("Failed to collect memory metrics: %s", e)

    try:
        for partition in psutil.disk_partitions(all=False):
            if "loop" in partition.device or "snap" in partition.mountpoint:
                continue
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_usage_percent.labels(mountpoint=partition.mountpoint).set(usage.percent)
            except (PermissionError, OSError):
                pass
    except Exception as e:
        logger.warning("Failed to collect disk usage: %s", e)

    try:
        io = psutil.disk_io_counters()
        if io:
            disk_io_read_bytes.set(io.read_bytes)
            disk_io_write_bytes.set(io.write_bytes)
    except Exception as e:
        logger.warning("Failed to collect disk I/O: %s", e)

    try:
        net = psutil.net_io_counters()
        network_bytes_sent.set(net.bytes_sent)
        network_bytes_recv.set(net.bytes_recv)
    except Exception as e:
        logger.warning("Failed to collect network metrics: %s", e)

    try:
        load = os.getloadavg()
        for i, period in enumerate(["1m", "5m", "15m"]):
            if i < len(load):
                load_average.labels(period=period).set(load[i])
    except (OSError, AttributeError):
        # getloadavg not available on Windows
        load_average.labels(period="1m").set(0)
        load_average.labels(period="5m").set(0)
        load_average.labels(period="15m").set(0)


def run_nmap_scan(target: str, port_arg: str) -> dict | None:
    """
    Run a lightweight Nmap scan on a single target.
    ETHICAL: Only use with localhost or internal Docker network IPs.
    """
    if not NMAP_AVAILABLE:
        return None
    try:
        nm = nmap.PortScanner()
        nm.scan(hosts=target, arguments=f"-p {port_arg} -T4 --min-rate 100")
        return nm[target] if target in nm.all_hosts() else None
    except Exception as e:
        logger.warning("Nmap scan failed for %s: %s", target, e)
        scan_errors_total.inc()
        return None


def collect_security_metrics() -> None:
    """
    Perform security scans on localhost and Docker network.
    Exports: dco_open_ports_total, dco_ports_by_service, dco_security_risk_score,
             dco_vulnerabilities_detected, dco_high_risk_ports
    """
    scan_start = time.time()
    port_arg = ",".join(map(str, TARGET_PORTS))
    total_open = 0
    high_risk_count = 0
    found_services = []

    if NMAP_AVAILABLE:
        for target in SCAN_TARGETS:
            result = run_nmap_scan(target, port_arg)
            if result and "tcp" in result:
                for port, data in result["tcp"].items():
                    state = data.get("state", "unknown")
                    if state == "open":
                        total_open += 1
                        service = data.get("name", "unknown")
                        ports_by_service.labels(target=target, port=str(port), state=state).set(1)
                        found_services.append((target, port, service))
                        if port in HIGH_RISK_PORTS:
                            high_risk_count += 1
    else:
        # Simulated metrics for environments without nmap (e.g. CI)
        total_open = 2  # Simulate SSH + one web port
        high_risk_count = 1
        ports_by_service.labels(target="127.0.0.1", port="22", state="open").set(1)
        ports_by_service.labels(target="127.0.0.1", port="80", state="open").set(1)
        found_services = [("127.0.0.1", 22, "ssh"), ("127.0.0.1", 80, "http")]

    open_ports_total.set(total_open)
    high_risk_ports.set(high_risk_count)

    # Simulated vulnerability count (in production, would integrate Trivy/OVAL)
    vuln_simulation = min(5, total_open + high_risk_count)
    vulnerabilities_detected.set(vuln_simulation)

    # Risk score: 0-100, higher = more risky
    risk = min(100, (total_open * 5) + (high_risk_count * 15) + (vuln_simulation * 5))
    security_risk_score.set(risk)

    scan_duration = time.time() - scan_start
    last_scan_timestamp.set(int(time.time()))
    scan_duration_seconds.set(round(scan_duration, 2))

    logger.info(
        "Security scan completed: targets=%s open_ports=%s high_risk=%s duration_sec=%s",
        SCAN_TARGETS, total_open, high_risk_count, round(scan_duration, 2),
    )


def collect_automation_metrics() -> None:
    """Update exporter uptime in seconds."""
    exporter_uptime_seconds.set(int(time.time() - START_TIME))


def main() -> None:
    """Start the HTTP server and periodically update metrics."""
    port = int(os.environ.get("DCO_EXPORTER_PORT", "8000"))
    scrape_interval = int(os.environ.get("DCO_SCRAPE_INTERVAL", "10"))

    exporter_info.info({
        "version": "1.0.0",
        "description": "DCO-Monitor Data Centre Operations Exporter",
    })

    logger.info("Starting DCO Exporter on port %s", port)
    start_http_server(port)

    collect_security_metrics()  # Initial scan

    while True:
        try:
            collect_system_metrics()
            collect_automation_metrics()
            # Re-scan security every 60 seconds to avoid excessive nmap usage
            if int(time.time()) % 60 < scrape_interval:
                collect_security_metrics()
        except Exception as e:
            logger.exception("Error during metric collection: %s", e)
        time.sleep(scrape_interval)


if __name__ == "__main__":
    main()
