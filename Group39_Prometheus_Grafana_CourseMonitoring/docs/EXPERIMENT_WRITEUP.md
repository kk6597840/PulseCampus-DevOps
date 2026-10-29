# DevOps Practical — Group 39

## Title
Application and System Performance Monitoring Using Prometheus and Grafana

## Aim (from Excel file, reproduced exactly)

**To monitor application and system performance using Prometheus and visualize metrics using Grafana dashboards.**

## Given task (from Excel file)

In the current system, there is no proper way to monitor performance in real time, making it hard to analyze system health. This affects decision-making and issue detection. To address this, implement monitoring using Prometheus and visualize metrics through Grafana dashboards.

## Objective

1. Create a Student / Course Registration Flask API.
2. Instrument requests with Prometheus metrics (Counter, Histogram, Gauge).
3. Make metrics available through a `/metrics` HTTP endpoint.
4. Configure Prometheus to scrape the application periodically.
5. Set up Grafana visualization for throughput, average latency, p95 latency, and HTTP 5xx rate.
6. Use a load generator and intentional slow/failed responses to observe live changes.
7. View Flask process health and Linux/Docker VM host CPU and memory metrics.

## Software & hardware requirements

Docker Desktop / Engine, Docker Compose V2, Python 3.10+, terminal and browser. Tested configurations are meant for any current machine that supports Linux Docker images. Internet access is required initially to pull images. Prometheus, Grafana, Flask, Waitress, and SQLite are free/open-source.

## Theory

**Metrics:** Numeric measurements describing application and system behavior.
**Prometheus:** Time-series monitoring system; periodically *pulls* `/metrics` and stores timestamped values.
**Grafana:** Connects to Prometheus and renders dashboards that can refresh periodically.
**Counter:** Monotonically increasing value such as total requests.
**Gauge:** Value that rises/falls, such as currently active user sessions.
**Histogram:** Cumulative bucket counts plus sum/count, used to estimate response-time distributions and p95.
**Rate:** Per-second increase of a Counter over a chosen time window.
**P95:** Estimated duration at or below which 95% of sampled requests fall during the selected window.

## Procedure

1. Extract the complete project and open a terminal in the folder containing `docker-compose.yml`.
2. Start Docker Desktop, then run `docker compose up --build -d`.
3. Run `docker compose ps` to see Flask, Prometheus, Grafana, and node-exporter.
4. Open `http://localhost:5000`; register a sample student and enroll them in one of four courses.
5. Open `http://localhost:5000/metrics`; find `http_requests_total`, `http_request_duration_seconds_bucket`, and `active_users`.
6. Open `http://localhost:9090/targets`, confirm `course-api` and the other two scrape targets report `UP`.
7. Open `http://localhost:3000` (admin / group39demo by default). Open the pre-provisioned Group 39 dashboard.
8. In the terminal run `python scripts/generate_traffic.py --mode normal --duration 90 --rps 10` and observe request-rate charts.
9. Run the same with `--mode slow`; observe average latency and p95 graphs increase.
10. Run the same with `--mode errors`; observe HTTP 503 and 5xx-error percentage increase.
11. Run `--mode sessions` to create active user sessions; observe the `active_users` Gauge increase.
12. Note the Linux/Docker VM host CPU/RAM panels and the Flask process CPU/memory panels.
13. Optional: query `up{job="course-api"}` or inspect `Alerts` in the Prometheus UI.
14. Capture your own actual-running screenshots for experiment submission; do not reuse generated/sample graphs as if observed.

## Observations to fill after execution

| Observation | Command / URL | Your observed value or screenshot |
|---|---|---|
| API healthy | `/health` | [capture after running] |
| Prometheus has target UP | `/targets` | [capture after running] |
| Counter after requests | `/metrics` | [capture after running] |
| Average and p95 increase with slow load | Grafana charts | [capture after running] |
| HTTP 5xx rate with failing load | Grafana charts | [capture after running] |
| Active users Gauge changes | UI + Grafana | [capture after running] |
| System CPU/memory monitoring | Grafana charts | [capture after running] |

## Expected result and conclusion

When deployed and receiving traffic, Prometheus scrapes Flask-exported metrics and node-exporter metrics, while Grafana plots traffic, latency, errors and system health. Controlled error/latency simulation demonstrates how monitoring helps detect service-performance issues. **Actual readings depend on the laptop and generated workload** and must be filled in after running; none have been fabricated here.

## Precautions

- Use a single Flask application process to keep the demo's in-memory Gauge consistent.
- Avoid storing student passwords, personal financial records, or other sensitive information.
- Prometheus and Grafana are bound to localhost; change the demo login if exposed on a network.
- On Windows with Docker Desktop, node-exporter reports **Linux VM** metrics, not host Windows performance.
