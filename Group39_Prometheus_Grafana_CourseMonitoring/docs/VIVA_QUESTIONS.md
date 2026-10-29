# Group 39 — DevOps Mini Project Viva Preparation

**Q1. What is the purpose of your project?**  
To run a working student/course API and monitor request traffic, response latency, errors, active users, and available Linux system metrics using Prometheus and Grafana.

**Q2. Why did you choose Flask?**  
Flask is lightweight and makes it straightforward to create REST endpoints and instrument request hooks with the `prometheus_client` library.

**Q3. What is Prometheus?**  
A monitoring/time-series database that periodically scrapes metrics and allows querying them with PromQL.

**Q4. What is Grafana?**  
A dashboard and visualization tool that queries monitoring data sources, such as Prometheus, and displays charts.

**Q5. What is the difference between them?**  
Prometheus collects, stores and queries numerical measurements; Grafana visualizes them.

**Q6. What is a Counter?**  
A metric that increases, except when a process restarts. Here, `http_requests_total` counts API requests.

**Q7. What is a Histogram?**  
A distribution of observations organized into cumulative buckets. Here it records request durations to calculate averages and latency percentiles.

**Q8. What is a Gauge?**  
A metric that can increase or decrease. Here `active_users` counts unique student IDs with nonexpired demo sessions; `http_requests_in_progress` measures concurrency.

**Q9. Why is `/metrics` used?**  
Prometheus scrapes this endpoint to obtain formatted samples, metric names, labels, and values.

**Q10. What happens when an HTTP request comes in?**  
A Flask hook starts timing and increments in-flight requests. The route executes. After the response, hooks update the Counter, Histogram and in-flight Gauge.

**Q11. Why exclude `/metrics` from request counters?**  
Prometheus scrapes automatically every 5 seconds, so counting scrapes would artificially raise the Student API request rate.

**Q12. What are labels?**  
Attributes attached to measurements. Our request Counter uses HTTP method, normalized route and status. We avoid arbitrary path values to prevent excessive time-series creation.

**Q13. What is PromQL?**  
Prometheus Query Language, used to compute rates, aggregations, and percentile estimations on stored time series.

**Q14. How is requests per second calculated?**  
Using `sum(rate(http_requests_total{job="course-api"}[1m]))`.

**Q15. How is average response time calculated?**  
Take the rate of Histogram sums and divide by the rate of Histogram counts. Multiply by 1000 for milliseconds.

**Q16. What is 95th percentile latency?**  
The approximate latency threshold below which 95% of sampled requests fall over the selected time window.

**Q17. How is p95 calculated here?**  
Using `histogram_quantile(0.95, sum by (le)(rate(http_request_duration_seconds_bucket[5m])))`, multiplied by 1000 to report milliseconds.

**Q18. What is HTTP error rate?**  
The ratio of requests producing HTTP 500–599 to all requests, expressed as a percentage, calculated from status-labeled Counters.

**Q19. What does 503 mean?**  
Service Unavailable. Our `/api/demo/error` endpoint intentionally returns this response for monitoring demonstrations.

**Q20. How do you demonstrate latency?**  
Use `/api/demo/slow?delay_ms=1200` or `--mode slow` in the included load generator.

**Q21. What is the scraping interval?**  
Prometheus scrapes the project’s configured jobs every five seconds.

**Q22. Is the Grafana dashboard truly continuous?**  
It refreshes its queries every five seconds and depends on the Prometheus scrape cadence; it is near-real-time monitoring, not continuous packet capture.

**Q23. Why are initial graphs empty?**  
No API traffic may have been generated, and rates need at least two consecutive scrape samples.

**Q24. How does the Gauge track active users?**  
A session-start endpoint creates an expiring token associated with a student ID. The Gauge counts unique IDs with unexpired sessions; session deletion decreases the count.

**Q25. Is this a real authentication system?**  
No. It is a classroom demonstration of session-based active-user metrics, without password authentication or secure identity verification.

**Q26. Why SQLite?**  
It is self-contained and sufficient for a small local demonstration, with uniqueness constraints and relational integrity.

**Q27. What does Docker Compose do?**  
Defines and launches the Flask application, Prometheus, Grafana and node-exporter together with network and persistent volumes.

**Q28. What does node-exporter measure here?**  
CPU, memory and Linux host or Docker Desktop Linux VM metrics. It does not directly collect native Windows hardware metrics from Docker Desktop.

**Q29. What if the Flask container stops?**  
Prometheus scrape health `up{job="course-api"}` eventually becomes 0 and the availability alert may fire after its 30-second hold time.

**Q30. What are project limitations?**  
Demo-only sessions, no identity/authentication, local deployment, and no external alert notification service. Multiple app processes would need coordinated metrics/session storage.
