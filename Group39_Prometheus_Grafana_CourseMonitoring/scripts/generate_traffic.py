#!/usr/bin/env python3
"""Concurrent standard-library load generator for the Group 39 Flask API.

Examples:
  python scripts/generate_traffic.py --mode mixed --duration 90 --rps 12
  python scripts/generate_traffic.py --mode slow --duration 90 --rps 8
  python scripts/generate_traffic.py --mode errors --duration 90 --rps 10
  python scripts/generate_traffic.py --mode sessions --duration 90 --rps 5
"""
import argparse
import concurrent.futures
from collections import Counter
import json
import random
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4


def send(url, method="GET", payload=None, timeout=8):
    data = json.dumps(payload).encode() if payload is not None else None
    req = Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    start = time.perf_counter()
    try:
        with urlopen(req, timeout=timeout) as response:
            body = response.read()
            return response.status, time.perf_counter() - start, json.loads(body)
    except HTTPError as error:
        return error.code, time.perf_counter() - start, {}
    except (URLError, TimeoutError, OSError) as error:
        return 0, time.perf_counter() - start, {"error": str(error)}


def traffic_path(mode):
    x = random.random()
    if mode == "normal":
        return "/api/courses" if x < 0.65 else "/api/summary"
    if mode == "slow":
        return "/api/demo/slow?delay_ms=1400" if x < 0.8 else "/api/courses"
    if mode == "errors":
        return "/api/demo/error" if x < 0.75 else "/api/courses"
    if mode == "mixed":
        return "/api/courses" if x < 0.55 else (
            "/api/demo/slow?delay_ms=1000" if x < 0.83 else "/api/demo/error")
    return "/api/courses"


def session_demo(base, stop_time, rps, total):
    # Fresh students create real, visibly increasing 'active_users' Gauge values.
    # Sessions are deliberately left open for the dashboard for 15 minutes or
    # until expiry; don't use this script for production load testing.
    next_request = time.monotonic()
    while time.monotonic() < stop_time:
        unique = uuid4().hex[:12]
        status, _, student = send(base + "/api/students", "POST", {
            "name": f"Demo Student {unique[:5]}",
            "email": f"group39-{unique}@example.test",
        })
        if status == 201:
            code, _, _ = send(base + "/api/sessions", "POST", {"student_id": student["id"]})
            total[code] += 1
        else:
            total[status] += 1
        next_request += 1 / rps
        time.sleep(max(0, next_request - time.monotonic()))


def main():
    p = argparse.ArgumentParser(description="Group 39 educational Prometheus load generator")
    p.add_argument("--base-url", default="http://localhost:5000")
    p.add_argument("--mode", choices=("normal", "slow", "errors", "mixed", "sessions"), default="mixed")
    p.add_argument("--duration", type=int, default=90, help="seconds, from 1 to 600")
    p.add_argument("--rps", type=float, default=10.0, help="attempted requests/s, from 0.1 to 50")
    args = p.parse_args()
    if not 1 <= args.duration <= 600 or not 0.1 <= args.rps <= 50:
        p.error("duration must be 1–600 and rps 0.1–50")
    base = args.base_url.rstrip("/")
    status, _, _ = send(base + "/health")
    if status != 200:
        p.error(f"Flask API is unavailable at {base}/health (HTTP {status}). Start Docker Compose.")
    print(f"Group 39 traffic: mode={args.mode} | {args.duration}s | attempted {args.rps:g} req/s | {base}",flush=True)
    counts = Counter()
    done_at = time.monotonic() + args.duration
    if args.mode == "sessions":
        session_demo(base, done_at, args.rps, counts)
    else:
        # Always issue requests at specified cadence while slow calls are in flight.
        futures = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=24) as pool:
            next_request = time.monotonic()
            last_report = next_request
            while time.monotonic() < done_at:
                futures.append(pool.submit(send, base + traffic_path(args.mode)))
                next_request += 1 / args.rps
                time.sleep(max(0, next_request - time.monotonic()))
                if time.monotonic() - last_report >= 10:
                    completed = sum(f.done() for f in futures)
                    print(f"  issued: {len(futures)} | completed: {completed}",flush=True)
                    last_report = time.monotonic()
            for future in concurrent.futures.as_completed(futures):
                status, _, _ = future.result()
                counts[status] += 1
    print("Response counts:",dict(sorted(counts.items())))
    print("Notes: 503 is an expected intentional failure for errors/mixed mode.")
    print("Open Grafana → Group 39 → Course Registration dashboard; refresh = 5 sec.")

if __name__ == "__main__":
    main()
