#!/usr/bin/env python3
"""Basic HTTP smoke tests of the running monitoring stack; stdlib only."""
import json
from urllib.error import URLError
from urllib.request import urlopen

URLS = [
    ("Flask health", "http://localhost:5000/health", "ok"),
    ("Flask metrics", "http://localhost:5000/metrics", "http_requests_total"),
    ("Prometheus health", "http://localhost:9090/-/healthy", "Healthy"),
    ("Grafana health", "http://localhost:3000/api/health", "database"),
]


def main():
    all_ok = True
    for label, url, fragment in URLS:
        try:
            with urlopen(url, timeout=7) as response:
                body = response.read().decode("utf-8")
                if fragment not in body:
                    raise ValueError(f"missing expected text '{fragment}'")
            print(f"PASS  {label:20s} {url}")
        except (URLError, TimeoutError, ValueError) as error:
            all_ok = False
            print(f"FAIL  {label:20s} {error}")
    try:
        with urlopen("http://localhost:9090/api/v1/targets",timeout=8) as r:
            targets=json.load(r)['data']['activeTargets']
        for target in targets:
            print("TARGET", target['labels'].get('job'), target['health'], target.get('lastError') or '')
            if target['health'] != 'up': all_ok=False
    except (URLError,TimeoutError,KeyError,ValueError) as error:
        print("FAIL  Prometheus targets:",error);all_ok=False
    if not all_ok:
        raise SystemExit(1)
    print("All basic checks passed. Send traffic, then examine Grafana charts.")

if __name__ == "__main__":
    main()
