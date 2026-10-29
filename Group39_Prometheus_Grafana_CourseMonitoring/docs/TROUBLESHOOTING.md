# Troubleshooting — Group 39

## 1. `docker` is not recognized / cannot connect to Docker daemon

Install/start Docker Desktop for Windows/Mac, or Docker Engine + Compose V2 on Linux. Enable Linux containers. After the engine starts, retry `docker compose up --build -d`. Check `docker version` and `docker compose version`.

## 2. Port 3000, 5000 or 9090 is already in use

Another application is using a local port. Stop the conflicting app. Use `netstat -ano | findstr :5000` in Windows CMD or `ss -ltn` on Linux to identify it. If you change host port bindings in Compose, update all local browser URLs/scripts accordingly; Docker service-to-service addresses remain `app:5000` and `prometheus:9090`.

## 3. Docker Compose build fails downloading images/libraries

Docker needs internet access on first run. Verify Docker Desktop reports that it is running, internet/DNS access is available, and your firewall/proxy allows Docker pulls. Retry `docker compose up --build -d`.

## 4. Grafana login doesn't accept `admin` / `group39demo`

Grafana stores the administrator password in its persistent named volume. Changes to `GF_SECURITY_ADMIN_PASSWORD` apply during initial database creation, not to a preexisting administrator account. Use the password you previously created or run `docker compose exec grafana grafana cli admin reset-admin-password NEW_PASSWORD` (adapt if prompted). Do not delete volumes unless you accept loss of saved data.

## 5. Grafana says “No data”

1. Open http://localhost:5000/health and check status `ok`.
2. Open http://localhost:9090/targets and ensure `course-api` is UP.
3. Generate traffic for 30+ seconds: `python scripts/generate_traffic.py --mode mixed --duration 45 --rps 10`.
4. Wait for several scrapes (5-second scrape interval).
5. Set the dashboard to **Last 15 minutes**, refresh **5s**.
6. In Prometheus query `http_requests_total` and `up{job="course-api"}`.
7. Check the Grafana data source `Prometheus` has URL `http://prometheus:9090` (not localhost inside Grafana container).

## 6. A single click doesn't noticeably change RPS or error charts

Rate queries average measurements over a 1-minute window and p95 uses a 5-minute window. Several sustained 503 or slow requests will have a clearer visible effect than one click. Run the included Python traffic generator.

## 7. Prometheus reports target DOWN

Check `docker compose ps` and `docker compose logs app --tail 80`. Prometheus targets must use the internal Compose service address `app:5000`, never `localhost:5000` (which would refer to Prometheus's own container).

## 8. Why is node-exporter showing Linux CPU on a Windows machine?

Docker Desktop uses a Linux virtual machine to run Linux containers; the system exporter observes that Linux environment. It is not a Windows host exporter. To monitor actual Windows hardware, a separate Windows exporter installation/integration would be needed and is outside this assignment.

## 9. Why does the `active_users` metric show 0?

Create a student and choose **Start session** in the UI. Or run `python scripts/generate_traffic.py --mode sessions --duration 15 --rps 1`. Sessions expire after 900 seconds by default, and the Gauge is refreshed when metrics are scraped. It is an in-memory teaching demo rather than real authenticated login.

## 10. Dashboard panels missing

Verify `config/grafana/provisioning/datasources/prometheus.yml`, `config/grafana/provisioning/dashboards/group39.yml` and `config/grafana/dashboards/group39-course-monitoring.json` exist. Run `docker compose logs grafana --tail 100` to inspect provisioning logs. Restart with `docker compose restart grafana` after correcting them.

## 11. App is reachable but enrollments fail

Use a student created in the current database. Choose an existing course and avoid duplicate registration. Inputs must pass validation and course capacity must not be exceeded. Data persists in the `course_data` named volume across `docker compose down` unless `-v` is used.

## 12. Stop without losing data

Use `docker compose down`; it preserves the SQLite, Grafana and Prometheus named volumes. Only `docker compose down -v` deletes them. Back up SQLite volume before major changes.

## 13. Test environment issue

Install local dependencies with `python -m pip install -r requirements-dev.txt`. `python -m pytest -q` tests Flask locally with temporary SQLite databases; Docker itself is not needed for unit tests. `scripts/verify_stack.py` checks actual running HTTP services and requires Docker stack startup.
