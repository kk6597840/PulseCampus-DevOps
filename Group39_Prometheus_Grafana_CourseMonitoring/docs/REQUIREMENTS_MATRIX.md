# Group 39 — Excel Assignment Compliance Checklist

**Source:** Uploaded `TE Mini Project.xlsx`, sheet `Third Year Project with Guide`, group 39 entry in row **158**, experiment in column D, project in column E. The exact wording of the assignment is recorded here for easy verification.

## Exact experiment (column D)

> To monitor application and system performance using Prometheus and visualize metrics using Grafana dashboards.
>
> Task: In the current system, there is no proper way to monitor performance in real time, making it hard to analyze system health. This affects decision-making and issue detection. To address this, implement monitoring using Prometheus and visualize metrics through Grafana dashboards

## Exact project (column E)

> Flask or Spring Boot Application Performance Monitoring
>
> Application: A Course Registration or Student API instrumented to expose its own metrics at /metrics.
>
> What you build:
>
> Flask: prometheus_client library with a Counter (total requests), Histogram (response time), and Gauge (active users). Spring Boot: Actuator and Micrometer with /actuator/prometheus
>
> Grafana panels for requests per second, average and 95th percentile latency, and error rate (5xx)
>
> PromQL examples: rate(http_requests_total[1m]) and histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
>
> Demo: Generate traffic with a loop, ab, or hey, add a deliberately slow or failing endpoint, and show latency and error panels reacting in real time.

## Requirement-by-requirement implementation

| Excel requirement | Implemented? | Where / how to demonstrate |
|---|---|---|
| Monitor **application performance** | YES | Flask instrumentation in `app/main.py`, app process metrics, Grafana dashboard |
| Monitor **system performance** | YES | `node-exporter` in `docker-compose.yml`, host CPU/RAM panels in Grafana (Linux/VM scope) |
| **Prometheus** time-series collection | YES | `config/prometheus/prometheus.yml`, 5-second scrapes and Prometheus query UI |
| **Grafana** dashboard visualization | YES | Automatic datasource + dashboard provisioning; 20 Grafana panels |
| Flask **or** Spring Boot | YES (Flask selected) | Flask and SQLite student/course service |
| Course Registration **or** Student API | YES (both in one app) | `/api/students`, `/api/courses`, `/api/enrollments` |
| `/metrics` endpoint | YES | `GET http://localhost:5000/metrics` |
| `prometheus_client` | YES | `requirements.txt`, `app/metrics.py`, `app/main.py` |
| Counter: total HTTP requests | YES | `http_requests_total{method,route,status}` |
| Histogram: response time | YES | `http_request_duration_seconds{method,route}` + bucket/count/sum |
| Gauge: active users | YES | `active_users`, live unique unexpired demo student sessions |
| Grafana **requests per second** | YES | Top KPI and time-series (sum of rate of Counters) |
| Grafana **average response time** | YES | Histogram `_sum` / `_count`, converted to milliseconds |
| Grafana **95th percentile latency** | YES | `histogram_quantile(0.95, sum by (le) (..._bucket[5m]))` |
| Grafana **HTTP 5xx error rate** | YES | Ratio of 5xx request rates to all request rates, percentage |
| PromQL `rate(http_requests_total[1m])` example | YES | Equivalent with `job` matcher and sum aggregation in dashboard & README |
| PromQL `histogram_quantile(...)` example | YES | Correct aggregation by `le`, used in dashboard & README |
| **Generate traffic** | YES | `scripts/generate_traffic.py --mode mixed --duration 90 --rps 12` |
| Deliberately **slow endpoint** | YES | `GET /api/demo/slow?delay_ms=1200` |
| Deliberately **failing endpoint** | YES | `GET /api/demo/error` sends HTTP 503 |
| Demonstrate **live reactive graphs** | YES (ready for live test) | Grafana refresh 5s; run slow/error load and observe changes |

**Interpretation:** "Flask or Spring Boot" presents alternatives, not a requirement to build both. Flask was chosen; all Flask-specific instrumentation points are implemented. `ab` and `hey` are suggestions; the included built-in Python concurrent traffic generator covers the same demonstration goal without separate load-testing software.

**Runtime verification:** Docker images must be pulled and the stack started on the user's machine; unit tests and smoke tests are provided to verify deployment. No screenshot or live Grafana metric is claimed to have been captured in this ZIP before execution.
