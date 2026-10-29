"""Bounded-cardinality Prometheus metrics for the instrumented API."""
from prometheus_client import Counter, Gauge, Histogram

HTTP_REQUESTS = Counter(
    "http_requests_total",
    "Total HTTP API requests, labeled by method, normalized route, and status code.",
    ("method", "route", "status"),
)
HTTP_LATENCY = Histogram(
    "http_request_duration_seconds",
    "API response time in seconds.",
    ("method", "route"),
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)
ACTIVE_USERS = Gauge(
    "active_users", "Unique demo student IDs with nonexpired live sessions."
)
IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "API requests currently in progress (excludes Prometheus scrapes).",
)
