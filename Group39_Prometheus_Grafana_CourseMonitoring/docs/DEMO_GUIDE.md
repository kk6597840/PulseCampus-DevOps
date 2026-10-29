# Group 39 — Instructor Demonstration Guide

## Prepare before your presentation

Make sure Docker Desktop is running, the ZIP has been extracted, and you are in the extracted folder. Ensure `docker compose ps` shows four running containers (app, prometheus, grafana, node-exporter). Run `python scripts/verify_stack.py` after Grafana starts, and check all required monitoring targets are `UP`. Open three tabs in your browser:

1. **Flask UI:** http://localhost:5000
2. **Prometheus:** http://localhost:9090/targets
3. **Grafana:** http://localhost:3000/d/group39-course-api

Sign into Grafana first (default admin / group39demo), and choose **Last 15 minutes** for the time range. Do not begin with an empty dashboard; send a few normal requests first.

## Suggested 5-minute demo

| Time | On screen | What to explain |
|---|---|---|
| 0:00–0:35 | Course Registration UI | “This is our working Flask student/course API with SQLite persistence.” |
| 0:35–1:15 | Register a student + enroll in a course | “The API validates input, stores records, and responds with success/error HTTP codes.” |
| 1:15–1:45 | Open `/metrics`, then Prometheus `/targets` | “Counter records requests, Histogram measures duration, Gauge tracks active users. Prometheus pulls `/metrics` every 5 seconds.” |
| 1:45–2:20 | Grafana dashboard | “The four required panels are requests/sec, average latency, 95th percentile latency, and HTTP 5xx error rate.” |
| 2:20–3:15 | Run slow traffic | “Intentionally delayed responses cause the latency panels to rise.” |
| 3:15–4:05 | Run error traffic | “HTTP 503 responses increase the error counter and 5xx percentage.” |
| 4:05–5:00 | Start/end demo session, show active users and system metrics | “The active_users Gauge changes when sessions start or end. Other panels show monitored Linux/VM CPU and memory.” |

**Timing note:** A command like `--mode slow --duration 90` keeps running for 90 seconds. To fit a strict 5-minute demo, use **multiple terminal tabs** and shorter 30–45 second scripts, or pre-populate the graphs and then trigger a fresh slow or failed request live. Charts need several five-second scrapes to update. Never claim a graph changed before you actually observe the change.

## Exact demo commands

**Normal requests (first):**

```bash
python scripts/generate_traffic.py --mode normal --duration 35 --rps 10
```

**Slow responses:**

```bash
python scripts/generate_traffic.py --mode slow --duration 35 --rps 8
```

**HTTP 503 failures:**

```bash
python scripts/generate_traffic.py --mode errors --duration 35 --rps 10
```

**Mixture of request types:**

```bash
python scripts/generate_traffic.py --mode mixed --duration 60 --rps 12
```

**Active users:**

```bash
python scripts/generate_traffic.py --mode sessions --duration 15 --rps 1
```

You can alternatively press the **Normal**, **Slow**, and **Failing request** buttons in the UI. Individual requests may be less visually obvious than sustained traffic.

## Show code if the evaluator asks

- `app/main.py`: Flask routes, before/after request instrumentation, deliberate failure/delay endpoints.
- `app/metrics.py`: global Prometheus Counter, Histogram and Gauges.
- `app/database.py`: SQLite tables, constraints, and seeded course catalogue.
- `config/prometheus/prometheus.yml`: 5-second scrape interval and scrape targets.
- `config/grafana/dashboards/group39-course-monitoring.json`: preconfigured panels and PromQL queries.
- `scripts/generate_traffic.py`: HTTP request generation in various modes.
- `docker-compose.yml`: how four services, ports and Docker volumes are defined.

## Suggested division of work across 4 members

This is a **suggestion only**; adjust it to what each person actually implemented and understands.

| Member | Suggested responsibility | Important files |
|---|---|---|
| Shlok Kurup | Flask backend and database API | `app/main.py`, `app/database.py` |
| Hemakshi Monga | Prometheus metrics and scraping | `app/metrics.py`, Prometheus YAML |
| Krish Karthick | Grafana dashboard, PromQL and integration | Dashboard JSON, `docker-compose.yml` |
| Mayzabeen Labbai | Traffic simulation, verification, documentation | `scripts/`, `tests/`, `docs/` |

All members should be able to explain the complete flow.

## Evidence to include in submission

Take 6–10 screenshots from your own live installation. At a minimum, capture the working app, `/metrics`, Prometheus targets UP, the four Grafana requirement panels, and one slow-traffic and one error-traffic example. Do not submit prefilled fictitious readings.

## Practical Q&A to rehearse

**Why is the app on port 5000 but Prometheus on 9090?** Flask serves the API on 5000; Prometheus hosts queries on 9090; Grafana provides the dashboard at 3000.

**Does Flask send data to Prometheus?** No. Prometheus periodically sends an HTTP GET request to Flask `/metrics`.

**How can you show latency changes?** Run `--mode slow`, which invokes an endpoint that sleeps for roughly 1.4 seconds before returning HTTP 200.

**Why might the charts briefly say No data?** New Counters may not exist until the first request, and `rate()` needs at least two Prometheus samples.

**How is p95 calculated?** With Histogram buckets and the PromQL `histogram_quantile` function, over a 5-minute rate window.

**Can node-exporter show my actual Windows CPU?** Not in Docker Desktop’s Linux environment; it shows the underlying Linux VM/host metrics. The app process panels show the Flask process specifically.
