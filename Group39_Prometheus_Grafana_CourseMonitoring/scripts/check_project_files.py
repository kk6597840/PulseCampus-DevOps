#!/usr/bin/env python3
"""Offline project completeness check (only Python standard library)."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
checks = [
    ("Flask REST service", "app/main.py", "@app.post(\"/api/students\")"),
    ("Course registration", "app/main.py", "@app.post(\"/api/enrollments\")"),
    ("Prometheus metrics endpoint", "app/main.py", "@app.get(\"/metrics\")"),
    ("Counter instrumentation", "app/metrics.py", "Counter("),
    ("Histogram instrumentation", "app/metrics.py", "Histogram("),
    ("Active user Gauge", "app/metrics.py", "ACTIVE_USERS = Gauge("),
    ("Slow demo endpoint", "app/main.py", "@app.get(\"/api/demo/slow\")"),
    ("Failing demo endpoint", "app/main.py", "@app.get(\"/api/demo/error\")"),
    ("Prometheus scraping", "config/prometheus/prometheus.yml", "scrape_interval: 5s"),
    ("Prometheus alert rules", "config/prometheus/alerts.yml", "CourseApiHighErrorRate"),
    ("Grafana provisioning", "config/grafana/provisioning/dashboards/group39.yml", "Group 39"),
    ("Grafana Prometheus data source", "config/grafana/provisioning/datasources/prometheus.yml", "prometheus:9090"),
    ("Linux system monitoring", "docker-compose.yml", "node-exporter"),
    ("Python demo load generator", "scripts/generate_traffic.py", "def traffic_path"),
    ("Flask unit tests", "tests/test_app.py", "def test_metrics_content"),
    ("Exact Excel task mapping", "docs/REQUIREMENTS_MATRIX.md", "Exact experiment"),
]
missing=[]
for label, file, needle in checks:
    content=(ROOT/file).read_text(encoding="utf-8") if (ROOT/file).is_file() else ""
    valid=needle in content
    print(f"{'PASS' if valid else 'FAIL'} {label}")
    if not valid: missing.append(label)

file=ROOT/"config/grafana/dashboards/group39-course-monitoring.json"
data=json.loads(file.read_text(encoding="utf-8"))
panels=data.get('panels', [])
combined="\n".join(t.get('expr','') for p in panels for t in p.get('targets',[]))
metrics=[
    ('Requests/sec PromQL', r'rate\(http_requests_total'),
    ('Average latency PromQL', r'http_request_duration_seconds_sum'),
    ('p95 latency PromQL', r'histogram_quantile\(0\.95'),
    ('HTTP 5xx error rate PromQL', r'status=~'),
    ('active users', r'active_users'),
]
for label,pattern in metrics:
    result=bool(re.search(pattern,combined))
    print(f"{'PASS' if result else 'FAIL'} {label}")
    if not result:missing.append(label)
if len(panels)<4: missing.append('Grafana panels fewer than 4')
print(f'Grafana panels: {len(panels)}')
print('All required files and dashboard queries present.' if not missing else f"Missing: {missing}")
sys.exit(bool(missing))
