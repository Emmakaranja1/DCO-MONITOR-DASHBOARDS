# DCO-Monitor Dashboard

**Data Centre Operations Monitor** — A lightweight monitoring and security automation stack for infrastructure health, log aggregation, and internal port visibility.




## 📋 Project Overview

DCO-Monitor provides a **compact monitoring stack** for data centre and lab environments: system metrics, internal security scanning, and centralized logs in a single deploy. Built for ops teams who need visibility without the overhead of enterprise tooling.

**Deployment:** `docker-compose up -d`



## 🏗 Architecture Diagram


┌─────────────────────────────────────────────────────────────────────────────┐
│                        DCO-Monitor Dashboard Stack                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌──────────────────┐    scrape /metrics     ┌──────────────────┐         │
│   │  DCO Exporter    │ ─────────────────────► │   Prometheus     │         │
│   │  (Python)        │        :8000            │   :9090          │         │
│   │  • System metrics│                        │   • TSDB          │         │
│   │  • Security scan │                        │   • Query API     │         │
│   │  • Automation    │                        └────────┬─────────┘         │
│   └────────┬─────────┘                                │                     │
│            │                                          │                     │
│            │ /var/log/dco_exporter.log                 │ datasource          │
│            ▼                                          ▼                     │
│   ┌──────────────────┐    push logs         ┌──────────────────┐           │
│   │  Promtail        │ ──────────────────►  │   Loki           │           │
│   │  (log shipper)   │                       │   :3100          │           │
│   └──────────────────┘                       └────────┬─────────┘           │
│                                                       │                     │
│                                                       │ datasource          │
│                                                       ▼                     │
│                                              ┌──────────────────┐           │
│                                              │   Grafana        │           │
│                                              │   :3000          │           │
│                                              │   • Dashboards   │           │
│                                              │   • Alerts       │           │
│                                              └──────────────────┘           │
└─────────────────────────────────────────────────────────────────────────────┘



## 🛠 Tech Stack

| Component        | Technology                     | Purpose                          |
|-----------------|--------------------------------|----------------------------------|
| **Exporter**    | Python, prometheus_client      | Custom metrics exposition        |
| **Metrics**     | Prometheus                     | Time-series storage & queries    |
| **Visualization** | Grafana                     | Dashboards & observability       |
| **Logging**     | Loki + Promtail                | Centralized log aggregation      |
| **Security**    | python-nmap (Nmap)             | Port scanning (internal only)    |
| **Automation**  | Bash, Python                   | Scripts & exporters              |
| **CI/CD**       | GitHub Actions                 | Lint, build, quality gates       |
| **Containers**  | Docker, docker-compose         | Reproducible deployment          |



## 🚀 How to Run

### Prerequisites

- Docker & Docker Compose
- (Optional) Nmap installed for full security scan support

### Quick Start


# Clone the repository
git clone https://github.com/YOUR_USERNAME/dco-monitor.git
cd dco-monitor

# Start the full stack (use 'docker-compose' if you have the standalone binary)
docker compose up -d

# Verify services
docker compose ps


### Access Points

| Service   | URL                    | Credentials      |
|----------|------------------------|------------------|
| Grafana  | http://localhost:3000  | admin / admin    |
| Prometheus | http://localhost:9090 | -                |
| Exporter | http://localhost:8001/metrics | -        |
| Loki     | http://localhost:3100  | -                |

### Add Prometheus to Grafana

1. Open Grafana → **Connections** → **Data sources**
2. **Add data source** → **Prometheus**
3. URL: `http://prometheus:9090` → **Save & test**
4. Repeat for **Loki** with URL: `http://loki:3100`



## 📊 Example Metrics

### System Monitoring

| Metric                          | Type   | Description              |
|---------------------------------|--------|--------------------------|
| `dco_cpu_usage_percent`         | Gauge  | CPU utilisation          |
| `dco_memory_usage_percent`      | Gauge  | Memory utilisation       |
| `dco_disk_usage_percent`        | Gauge  | Disk usage by mountpoint |
| `dco_disk_io_read_bytes_total`  | Gauge  | Disk read I/O            |
| `dco_network_bytes_sent_total`  | Gauge  | Network egress           |
| `dco_load_average`              | Gauge  | System load (1m, 5m, 15m)|

### Security Monitoring

| Metric                      | Type   | Description                |
|----------------------------|--------|----------------------------|
| `dco_open_ports_total`     | Gauge  | Open ports detected        |
| `dco_ports_by_service`     | Gauge  | Ports by target/port/state |
| `dco_security_risk_score`  | Gauge  | Risk score (0–100)         |
| `dco_vulnerabilities_detected` | Gauge | Simulated vulns         |
| `dco_high_risk_ports`      | Gauge  | High-risk exposed ports    |
| `dco_scan_errors_total`    | Counter| Scan failures              |

### Automation & Operations

| Metric                         | Type   | Description            |
|--------------------------------|--------|------------------------|
| `dco_exporter_uptime_seconds`  | Gauge  | Exporter uptime        |
| `dco_last_scan_timestamp_seconds` | Gauge | Last scan time      |
| `dco_scan_duration_seconds`    | Gauge  | Scan duration          |



## 📈 Grafana Dashboard Setup

### System Monitoring Panels

1. **CPU Usage**  
   - Query: `dco_cpu_usage_percent`  
   - Visualization: Stat or Time series  

2. **Memory Usage**  
   - Query: `dco_memory_usage_percent`  
   - Visualization: Gauge (0–100)  

3. **Disk Usage**  
   - Query: `dco_disk_usage_percent{mountpoint=~".+"}`  
   - Visualization: Bar gauge or Time series  

4. **Network Traffic**  
   - Query: `rate(dco_network_bytes_sent_total[5m])` and `rate(dco_network_bytes_recv_total[5m])`  
   - Visualization: Time series (dual axis)  

### Security Monitoring Panels

5. **Open Ports**  
   - Query: `dco_open_ports_total`  
   - Visualization: Stat  

6. **Security Risk Score**  
   - Query: `dco_security_risk_score`  
   - Visualization: Gauge (0–100, green/yellow/red)  

7. **Vulnerabilities Detected**  
   - Query: `dco_vulnerabilities_detected`  
   - Visualization: Stat  

### Operations Panels

8. **Scan Duration**  
   - Query: `dco_scan_duration_seconds`  
   - Visualization: Stat  

9. **Exporter Health**  
   - Query: `dco_exporter_uptime_seconds` or `up{job="dco-exporter"}`  
   - Visualization: Stat  

### Quick Import

Create a new dashboard and add panels using the queries above. Optionally export a JSON dashboard and share it in the repo for one-click import.



## 🔒 Ethical & Safe Scanning

**Important:** Nmap scans are restricted to internal targets only:

- `127.0.0.1` (localhost)
- `172.17.0.1` (Docker default bridge gateway)

**No external IP scanning is performed.** Suitable for lab, staging, and internal networks.



## 📁 Project Structure


dco-monitor/
├── dco_exporter.py          # Custom Prometheus exporter
├── requirements.txt         # Python dependencies
├── Dockerfile               # Exporter container build
├── docker-compose.yml       # Full stack orchestration
├── prometheus.yml           # Prometheus scrape config
├── promtail.yml             # Log shipping config
├── loki-config.yml          # Loki configuration
├── run_scan.sh              # Manual security scan script
├── ruff.toml                # Python lint config
├── Screenshots/             # Proof-of-work screenshots
└── .github/
    └── workflows/
        └── docker-build.yml # CI/CD pipeline




## 🤖 Automation Script

Trigger a manual port scan and append results to an audit log:


./run_scan.sh


Output is logged to `./scan_logs/scan_YYYYMMDD_HHMMSS.log`.



## 📊 Business Value

How this project delivers value in a data centre operations context:

| Benefit | Impact |
|---------|--------|
| **Visibility** | Central view of system health, security posture, and exporter uptime — fewer blind spots, faster incident detection |
| **Automation** | Exporter and scripts reduce manual checks; metrics and scans run continuously without operator intervention |
| **Logging** | Centralised logs (Loki) support incident response, root-cause analysis, and audit trails for compliance |
| **Scalability** | Containerised design allows easy extension to more exporters, hosts, or targets as the estate grows |
| **Security awareness** | Port scanning and risk scoring surface exposed services — supports hardening and change validation |  



## 📸 Screenshots

Deployment overview — data sources, dashboards, and log observability.

### Data Sources Configured

Prometheus and Loki are connected to Grafana for metrics and logs.

![Data Sources Overview - Prometheus and Loki configured](Screenshots/Screenshot%20from%202026-03-05%2012-50-42.png)

*Both Prometheus and Loki data sources configured and ready for dashboards and log queries.*



### Prometheus Data Source

![Prometheus data source configuration](Screenshots/Screenshot%20from%202026-03-05%2012-25-49.png)

*Prometheus connected at `http://prometheus:9090` — default data source for metrics.*



### Loki Data Source

![Loki data source configuration](Screenshots/Screenshot%20from%202026-03-05%2012-27-51.png)

*Loki connected at `http://loki:3100` for centralized log aggregation from the DCO exporter.*



### Dashboard Panel Creation

![Creating a Grafana panel with Prometheus](Screenshots/Screenshot%20from%202026-03-05%2012-29-32.png)

*Edit panel view — building a visualization with Prometheus as the data source.*



### System Monitoring: CPU Usage (Live Metrics)

![CPU usage time-series from DCO exporter](Screenshots/Screenshot%20from%202026-03-05%2012-40-28.png)

*Live `dco_cpu_usage_percent` time-series — DCO exporter metrics scraped by Prometheus and visualized in Grafana. Threshold at 80% for alerting.*



### Log Observability (Loki)

![Loki Explore — DCO exporter logs](Screenshots/Screenshot%20from%202026-03-05%2012-49-43.png)

*Querying `dco-exporter` logs via Loki — structured logging and log aggregation working end-to-end.*



## 🎯 Technical Stack

| Area                    | Implementation                                       |
|-------------------------|------------------------------------------------------|
| **System metrics**      | psutil, load average, disk I/O, network stats        |
| **Automation**          | Python exporter, Bash scripts, Prometheus scraping   |
| **Containers**          | Dockerfile, docker-compose, multi-service stack      |
| **Observability**       | Prometheus, Grafana, custom Prometheus metrics       |
| **Security scanning**   | Nmap, python-nmap, port enumeration, risk scoring    |
| **Logging**             | Structured logs, Loki, Promtail                      |
| **CI**                  | GitHub Actions, lint, build verification             |



## 📝 License

MIT License.
