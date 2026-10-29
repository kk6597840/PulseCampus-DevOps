# GROUP 39 — MINI PROJECT REPORT

## Title
**PulseCampus: Flask Course Registration API Performance Monitoring Using Prometheus and Grafana**

### Team
- Shlok Kurup — 124A1070
- Hemakshi Monga — 124A1084
- Krish Karthick — 124A1067
- Mayzabeen Labbai — 124A1071

> This document provides report content, not a filled or signed institutional certificate. Enter your guide, subject faculty, college formatting, and screenshots according to your department's instructions. Do not claim benchmark results until they have been measured on your system.

## Abstract

Modern web applications need a way to detect when requests become slower, fail more frequently, or overload supporting systems. This mini project implements a course registration service for student records and course enrollment and adds an observability stack that measures application and system performance. The student API is built with Flask, stores records in SQLite, and exposes a Prometheus-compatible `/metrics` endpoint. Request totals are represented as Counters; response time is represented as a Histogram; and active users and in-progress requests are represented as Gauges. Prometheus scrapes these metrics at five-second intervals, while Grafana displays throughput, average response time, p95 latency, server-error rate, and service health. A traffic generator and controlled slow/error endpoints allow common performance problems to be simulated without harming external services. System CPU and memory charts are provided through a node-exporter integration for the Linux host or Docker VM. The application and monitoring components run together using Docker Compose and are suited to a local classroom demonstration.

## 1. Introduction

Course registration is an example of a service where response time and availability matter. If an enrollment request becomes slow or the application begins to return HTTP 5xx responses, simply looking at the user interface may not explain the problem. Developers benefit from measurements collected consistently over time. This project demonstrates how to add instrumentation to the service, store measurements as time series, and visualize performance in a monitoring dashboard. It also allows viewers to create actual student records and course enrollments rather than only viewing a static monitoring page.

## 2. Problem Statement

The assigned experiment states that the current system has no proper real-time monitoring, making it difficult to understand system health and identify problems. The proposed solution is to instrument a Course Registration or Student API and use Prometheus to collect metrics and Grafana to visualize them. During the demonstration, controlled normal, slow, and failing API calls show changes in throughput, response-time distributions, and error rates.

## 3. Objectives

1. Build a functional Flask API for students, courses, and course enrollments.
2. Export application-level Prometheus metrics from the `/metrics` endpoint.
3. Track requests with Counter, response duration with Histogram, and active users with Gauge.
4. Configure Prometheus collection and Grafana panels for required performance indicators.
5. Include system/host metrics for CPU and memory from node-exporter, clarifying host scope.
6. Simulate high latency and server errors, and verify the charts respond.
7. Package the system into a repeatable, one-command Docker Compose deployment.

## 4. Literature and Tools Used

**Python 3 / Flask:** Lightweight REST API framework with route handling and request hooks.  
**SQLite:** Simple relational database for the student, course, and enrollment tables.  
**prometheus_client:** Official-style Python instrumentation library exposing Counter, Histogram, and Gauge.  
**Prometheus:** Polls metric endpoints and provides a time-series store and PromQL query engine.  
**Grafana:** Dashboard platform; its Prometheus data source and dashboards are provisioned from files.  
**node-exporter:** Linux system metrics exporter (Docker Desktop users observe Linux VM metrics).  
**Docker Compose:** Launches the components on an isolated container network with local volumes.  
**Waitress:** Python WSGI server with concurrent threads suitable for running the classroom Flask app in one process.

## 5. Existing System vs Proposed System

| Existing approach | Proposed system |
|---|---|
| No performance history visible to the team | Prometheus stores time-stamped measurements |
| Difficult to compare normal and degraded requests | Grafana latency charts show average and p95 responses |
| Errors hard to quantify over time | 5xx rate calculation from labeled HTTP counters |
| Manual review of isolated app output | Automatically refreshed monitoring dashboard |
| Limited awareness of host resource usage | Linux/Docker VM system CPU/memory charts |
| Difficult to reproduce performance issue | Built-in load generator and failure simulation |

## 6. System Architecture

```text
  Student Browser or Python Load Generator
                  |
             HTTP Requests
                  |
       +-----------------------+
       | Flask Course API      |
       | SQLite database       |
       | /metrics endpoint     |
       | Counter/Histogram/    |
       | Gauge instrumentation |
       +-----------------------+
                  ^
                  | Pull /metrics every 5 seconds
                  |
       +-----------------------+         +---------------------+
       | Prometheus            | <------ | node-exporter       |
       | Time-series & PromQL  |         | Linux VM CPU / RAM  |
       +-----------------------+         +---------------------+
                  ^
                  | Grafana queries Prometheus
                  |
       +-----------------------+
       | Grafana Dashboard     |
       | RPS / Avg / P95 / 5xx |
       | Active users / health |
       +-----------------------+
```

Prometheus uses a pull model; the Flask service does not push metrics directly to Grafana. Grafana queries Prometheus, not the application database, to display the charts.

## 7. Modules

### 7.1 Student registration and course-management module

The Flask application provides endpoints to list courses, register a student using a validated name/email, create enrollments, list enrollments, and delete enrollment records. SQLite uses a unique email constraint for students and a unique `(student_id, course_id)` constraint to prevent duplicate course registrations. A transaction checks remaining course capacity before committing an enrollment.

### 7.2 Prometheus instrumentation module

Flask `before_request` starts timing API operations. After the response is produced, `after_request` increments the request Counter with method, normalized route, and status labels and observes the elapsed duration with a Histogram. A Gauge tracks in-progress requests, and another Gauge tracks unique student IDs with unexpired demo sessions. A `teardown_request` safeguard protects the in-progress Gauge if a request terminates unusually. Only `/api/` calls are included in these application traffic metrics, so the repeated `/metrics` scrapes do not inflate student-API request rates.

### 7.3 Prometheus monitoring module

Prometheus uses a scrape interval of five seconds and three jobs: the course API, Prometheus itself, and node-exporter. A local volume stores metrics history for up to seven days, subject to Prometheus retention settings. Alert rules are included for unavailable metrics targets, more than 10% HTTP 5xx rate, and p95 latency above one second, each with a 30-second hold-down. Rules evaluate locally; automatic email/SMS alert delivery is not included.

### 7.4 Grafana visualization module

A file-provisioned Prometheus data source and Grafana dashboard are created when the stack starts. The dashboard contains 20 panels, including four mandatory top KPIs: requests/second, average latency, p95 latency, and percentage of HTTP 5xx errors. Other panels include traffic curves, error code breakdown, active users, concurrent requests, application/process status, endpoint-level latency, and Linux/Docker VM host resources. A five-second dashboard refresh aligns with the scrape interval.

### 7.5 Traffic simulator

A standard Python script generates controlled traffic without requiring ApacheBench or a separate load-testing utility. Its modes produce mostly successful calls, slow 1.4-second calls, intentional 503 responses, mixed calls, or demo student sessions. Multiple worker threads allow slow requests to overlap. Traffic rate and duration are adjustable from the command line.

## 8. Database Design

**STUDENTS** (`id` PK, `name`, `email` UNIQUE, `created_at`)  
**COURSES** (`id` PK, `code` UNIQUE, `title`, `instructor`, `capacity`)  
**ENROLLMENTS** (`id` PK, `student_id` FK, `course_id` FK, `created_at`, UNIQUE pair)

Relationships: one Student has many Enrollments, and one Course has many Enrollments. Thus a Student may enroll in multiple Courses, within course capacity. Demo sessions are transient process-memory entries rather than database rows.

## 9. Metric Design and Formulas

| Metric | Type | Meaning |
|---|---|---|
| `http_requests_total{method,route,status}` | Counter | Number of API responses by category |
| `http_request_duration_seconds_bucket` | Histogram buckets | Cumulative counts of duration observations |
| `http_request_duration_seconds_sum` | Histogram sum | Total time of observed API operations |
| `http_request_duration_seconds_count` | Histogram count | Total duration observations |
| `active_users` | Gauge | Unique live demo session holders |
| `http_requests_in_progress` | Gauge | Concurrent API calls being handled |
| `up{job="course-api"}` | Prometheus internal | 1 if target scrape succeeds; 0 otherwise |
| `process_resident_memory_bytes` | Client-collected | Flask Python process resident memory |
| `node_cpu_seconds_total` | node-exporter | Linux/Docker VM CPU time counters |

Requests per second = `sum(rate(http_requests_total{job="course-api"}[1m]))`.  
Average response time (seconds) = `sum(rate(http_request_duration_seconds_sum[1m])) / sum(rate(http_request_duration_seconds_count[1m]))` with safe minimum divisor.  
P95 response time = `histogram_quantile(0.95, sum by (le)(rate(http_request_duration_seconds_bucket[5m])))`.  
5xx error percentage = `100 × (request rate with status 500–599) / (all request rate)`.

P95 is an **estimate derived from configured histogram buckets**, not an exact rank computed from every stored request. Prometheus uses rates over windows, so graphs need multiple scrape samples and can decline after a test completes.

## 10. Implementation Workflow

1. Define data model and API routes in Flask.
2. Add global Counter/Histogram/Gauge metric definitions.
3. Attach request timing to Flask request life-cycle hooks.
4. Create `/metrics` endpoint using `generate_latest()`.
5. Build Dockerfile to run Flask with Waitress and its SQLite data volume.
6. Configure Prometheus static targets and alerting rules.
7. Configure Grafana data source and import dashboard via file provisioning.
8. Build UI, interactive traffic simulation and load-generation script.
9. Run tests and perform a live demonstration while recording actual output.

## 11. Test Plan and Expected Behavior

| Case | Action | Expected |
|---|---|---|
| API health | GET `/health` | `200` and database `ok` |
| Course list | GET `/api/courses` | Four initial courses |
| Student creation | Valid JSON POST `/api/students` | `201` and student ID |
| Invalid email | Invalid email POST | `400` |
| Duplicate email | Repeat creation | `409` |
| Valid enrollment | POST student+course IDs | `201` |
| Duplicate enrollment | Repeat pair | `409` |
| Session start/stop | POST, then DELETE | Gauge rises, then falls |
| Slow endpoint | GET `/api/demo/slow` | `200`, deliberate delay |
| Fail endpoint | GET `/api/demo/error` | `503` |
| Raw Prometheus output | GET `/metrics` | Exposition contains request, latency, active user families |
| Load normal / slow / errors | Run scripts | Prometheus & Grafana change over scrape window |
| Target state | Open `/targets` | API target UP while process is running |
| Host resource monitoring | Grafana node-exporter panels | Linux/Docker VM host CPU and memory reported |

## 12. Screenshots to Capture During Demonstration

Use screenshots from **your running setup** and label them consistently:

- Figure 1: Docker Compose services running.
- Figure 2: Course registration UI and student creation.
- Figure 3: Student course enrollment and updated table.
- Figure 4: Raw `/metrics` endpoint showing Counter, Histogram, Gauge.
- Figure 5: Prometheus `/targets` with target UP.
- Figure 6: Normal traffic and Grafana request rate chart.
- Figure 7: Slow traffic and rising average/p95 latency.
- Figure 8: HTTP 503 traffic and rising 5xx error percentage.
- Figure 9: Active student count and active_users Gauge chart.
- Figure 10: Linux/Docker VM host CPU/memory and process metrics.

## 13. Results and Discussion

**Expected outcomes:** Valid API requests create students and enrollments in SQLite. The `/metrics` endpoint provides application Counters, Histograms, and Gauges. When Prometheus successfully scrapes the target, the Grafana dashboard shows current rates and trends. Slow requests should increase latency values, and intentionally failing HTTP 503 requests should increase the 5xx error percentage. Opening or closing demo sessions should change `active_users`. The system charts describe the monitored Linux host or Docker VM.

**Actual observed results:** Record timestamps, representative metric values, Grafana screenshot evidence, and any environment-specific errors after your group runs the project. Actual values have **not** been predetermined or fabricated in this report.

## 14. Advantages

- No paid cloud account or external API key is needed.
- All core application and dashboard configuration files are version controlled.
- Metrics are collected automatically and can be examined using PromQL.
- Problem scenarios are reproducible without disrupting external systems.
- Course registration is functional, rather than a static mockup.

## 15. Limitations and Future Scope

This is a local, classroom-grade system. The demo active-users measure tracks unique in-memory session holders, not authenticated logins. Running multiple Python processes would require additional coordination or proper Prometheus multiprocess support. HTTP endpoints are not protected by authentication. Prometheus alert rules do not have external alert notification routing. The system exporter on Windows Docker Desktop does not observe native Windows host hardware. Potential improvements include authenticated student logins, PostgreSQL persistence, service-level objectives (SLOs), an alert routing service, distributed tracing, continuous integration tests, and deployment to Kubernetes.

## 16. Conclusion

The mini project illustrates an end-to-end DevOps monitoring workflow in which a real Flask service exports request metrics, Prometheus collects and stores them, and Grafana visualizes application and system conditions. By reproducing delays, failed requests, and active-user changes, the group can explain how monitoring supports operational awareness, faster issue identification, and better maintenance decisions.

## References

1. Prometheus configuration documentation: https://prometheus.io/docs/prometheus/latest/configuration/configuration/
2. Python Prometheus instrumentation: https://prometheus.github.io/client_python/instrumenting/
3. Prometheus Histogram documentation: https://prometheus.github.io/client_python/instrumenting/histogram/
4. Grafana configuration provisioning: https://grafana.com/docs/grafana/latest/administration/provisioning/
5. Flask documentation: https://flask.palletsprojects.com/
6. Docker Compose documentation: https://docs.docker.com/compose/
