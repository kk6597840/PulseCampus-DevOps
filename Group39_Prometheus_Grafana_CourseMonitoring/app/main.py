"""Group 39 course-registration service with real Prometheus instrumentation.

Run locally: python -m app.main
Production classroom stack: docker compose up --build -d
"""
from __future__ import annotations

from collections import Counter as CollectionsCounter
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from time import monotonic, perf_counter, sleep
import os
import re
import secrets
import sqlite3

from flask import Flask, Response, g, jsonify, render_template, request
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.database import connection, init_db
from app.metrics import ACTIVE_USERS, HTTP_LATENCY, HTTP_REQUESTS, IN_PROGRESS

SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", "900"))
_EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def create_app(testing=False):
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["TESTING"] = testing
    # Initialize the database before handling traffic; safe to rerun.
    init_db()

    # Classroom demonstration only: this is NOT an authentication system.
    # Token -> (student_id, expiry_monotonic). Kept in one process (1 Gunicorn worker).
    sessions = {}
    sessions_lock = Lock()

    def update_sessions_locked():
        now = monotonic()
        expired = [key for key, (_, expiry) in sessions.items() if expiry <= now]
        for key in expired:
            sessions.pop(key, None)
        ACTIVE_USERS.set(len({student_id for student_id, _ in sessions.values()}))

    @app.before_request
    def start_request_timing():
        g.record_api = request.path.startswith("/api/")
        if g.record_api:
            g.request_started = perf_counter()
            g.request_in_progress = True
            IN_PROGRESS.inc()

    @app.after_request
    def record_request_metrics(response):
        if getattr(g, "record_api", False):
            duration = max(0.0, perf_counter() - g.request_started)
            # Using the URL rule keeps /api/students/1 and /api/students/2
            # from generating unlimited distinct Prometheus time series.
            route = request.url_rule.rule if request.url_rule else "unmatched"
            HTTP_REQUESTS.labels(request.method, route, str(response.status_code)).inc()
            HTTP_LATENCY.labels(request.method, route).observe(duration)
            if getattr(g, "request_in_progress", False):
                IN_PROGRESS.dec()
                g.request_in_progress = False
        return response

    @app.teardown_request
    def clean_up_in_progress(_error):
        # Safety net if Flask exits before after_request executes.
        if getattr(g, "request_in_progress", False):
            IN_PROGRESS.dec()
            g.request_in_progress = False

    @app.get("/")
    def home():
        return render_template("index.html")

    @app.get("/health")
    def health():
        try:
            with connection() as conn:
                conn.execute("SELECT 1").fetchone()
            return jsonify(status="ok", service="group39-student-api", database="ok")
        except sqlite3.Error:
            return jsonify(status="degraded", service="group39-student-api", database="error"), 503

    @app.get("/metrics")
    def metrics():
        with sessions_lock:
            update_sessions_locked()
        return Response(generate_latest(), content_type=CONTENT_TYPE_LATEST)

    @app.get("/api/courses")
    def courses():
        with connection() as conn:
            rows = conn.execute("""
                SELECT c.id, c.code, c.title, c.instructor, c.capacity,
                       COUNT(e.id) AS enrolled
                FROM courses c LEFT JOIN enrollments e ON e.course_id = c.id
                GROUP BY c.id ORDER BY c.code
            """).fetchall()
        return jsonify(courses=[dict(row) for row in rows])

    @app.get("/api/students")
    def students():
        with connection() as conn:
            rows = conn.execute(
                "SELECT id, name, email, created_at FROM students ORDER BY id DESC LIMIT 200"
            ).fetchall()
        return jsonify(students=[dict(row) for row in rows])

    @app.post("/api/students")
    def add_student():
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify(error="Expected a JSON object."), 400
        name = str(payload.get("name", "")).strip()
        email = str(payload.get("email", "")).strip().lower()
        if not 2 <= len(name) <= 80 or len(email) > 254 or not _EMAIL.fullmatch(email):
            return jsonify(error="Name must be 2–80 characters and email must be valid."), 400
        try:
            with connection() as conn:
                cursor = conn.execute(
                    "INSERT INTO students (name, email) VALUES (?, ?)", (name, email)
                )
                student_id = cursor.lastrowid
        except sqlite3.IntegrityError:
            return jsonify(error="A student with this email already exists."), 409
        return jsonify(id=student_id, name=name, email=email), 201

    @app.get("/api/enrollments")
    def enrollments():
        with connection() as conn:
            rows = conn.execute("""
                SELECT e.id, s.id AS student_id, s.name AS student,
                       c.id AS course_id, c.code, c.title, e.created_at
                FROM enrollments e
                JOIN students s ON s.id = e.student_id
                JOIN courses c ON c.id = e.course_id
                ORDER BY e.id DESC LIMIT 200
            """).fetchall()
        return jsonify(enrollments=[dict(row) for row in rows])

    @app.post("/api/enrollments")
    def create_enrollment():
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify(error="Expected a JSON object."), 400
        try:
            student_id = int(payload.get("student_id"))
            course_id = int(payload.get("course_id"))
        except (TypeError, ValueError):
            return jsonify(error="Valid student_id and course_id are required."), 400
        if student_id < 1 or course_id < 1:
            return jsonify(error="IDs must be positive integers."), 400
        with connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            student = conn.execute("SELECT id FROM students WHERE id = ?", (student_id,)).fetchone()
            course = conn.execute("SELECT id, capacity FROM courses WHERE id = ?", (course_id,)).fetchone()
            if student is None or course is None:
                return jsonify(error="Student or course not found."), 404
            existing = conn.execute(
                "SELECT id FROM enrollments WHERE student_id = ? AND course_id = ?",
                (student_id, course_id),
            ).fetchone()
            if existing:
                return jsonify(error="Student is already enrolled in this course."), 409
            occupied = conn.execute(
                "SELECT COUNT(*) FROM enrollments WHERE course_id = ?", (course_id,)
            ).fetchone()[0]
            if occupied >= course["capacity"]:
                return jsonify(error="Course is at full capacity."), 409
            cursor = conn.execute(
                "INSERT INTO enrollments (student_id, course_id) VALUES (?, ?)",
                (student_id, course_id),
            )
            new_id = cursor.lastrowid
        return jsonify(id=new_id, student_id=student_id, course_id=course_id), 201

    @app.delete("/api/enrollments/<int:enrollment_id>")
    def delete_enrollment(enrollment_id):
        with connection() as conn:
            cursor = conn.execute("DELETE FROM enrollments WHERE id = ?", (enrollment_id,))
            if cursor.rowcount == 0:
                return jsonify(error="Enrollment not found."), 404
        return jsonify(message="Enrollment removed.")

    @app.get("/api/summary")
    def summary():
        with connection() as conn:
            students_count = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
            course_count = conn.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
            enrollment_count = conn.execute("SELECT COUNT(*) FROM enrollments").fetchone()[0]
        with sessions_lock:
            update_sessions_locked()
            active = len({student_id for student_id, _ in sessions.values()})
        return jsonify(students=students_count, courses=course_count,
                       enrollments=enrollment_count, active_users=active)

    @app.post("/api/sessions")
    def start_demo_session():
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify(error="Expected a JSON object."), 400
        try:
            student_id = int(payload.get("student_id"))
        except (TypeError, ValueError):
            return jsonify(error="student_id must be a number."), 400
        with connection() as conn:
            exists = conn.execute("SELECT 1 FROM students WHERE id = ?", (student_id,)).fetchone()
        if not exists:
            return jsonify(error="Student not found."), 404
        token = secrets.token_urlsafe(32)
        with sessions_lock:
            update_sessions_locked()
            sessions[token] = (student_id, monotonic() + SESSION_TTL_SECONDS)
            update_sessions_locked()
        return jsonify(token=token, student_id=student_id,
                       expires_in_seconds=SESSION_TTL_SECONDS), 201

    @app.delete("/api/sessions/<token>")
    def end_demo_session(token):
        with sessions_lock:
            update_sessions_locked()
            if sessions.pop(token, None) is None:
                return jsonify(error="Session not found or expired."), 404
            update_sessions_locked()
        return jsonify(message="Demo session ended.")

    @app.get("/api/demo/slow")
    def demo_slow():
        # Bounded by 3 seconds to make latency visibly change without locking the app.
        try:
            delay_ms = max(0, min(3000, int(request.args.get("delay_ms", "1200"))))
        except ValueError:
            return jsonify(error="delay_ms must be an integer."), 400
        sleep(delay_ms / 1000)
        return jsonify(status="ok", message="Intentional latency sample", delay_ms=delay_ms)

    @app.get("/api/demo/error")
    def demo_error():
        # Intentionally generate a real 5xx HTTP response without crashing the process.
        return jsonify(status="error", message="Simulated service unavailable (demo only)"), 503

    @app.errorhandler(404)
    def not_found(_error):
        if request.path.startswith("/api/"):
            return jsonify(error="API endpoint not found."), 404
        return "Not found", 404

    return app


# The WSGI server imports this object; production uses exactly one worker so
# the classroom session Gauge matches the in-memory demo sessions.
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False, threaded=True)
