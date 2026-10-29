"""Unit tests for the Group 39 Student API and Prometheus instrumentation."""
import uuid


def create_student(client):
    email = f"student-{uuid.uuid4().hex[:9]}@example.test"
    result = client.post("/api/students", json={"name": "Test Student", "email": email})
    assert result.status_code == 201
    return result.get_json()["id"]


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json()["database"] == "ok"


def test_courses_seeded(client):
    result = client.get("/api/courses")
    assert result.status_code == 200
    courses = result.get_json()["courses"]
    assert len(courses) == 4
    assert {course["code"] for course in courses} == {"CS301", "CS302", "CS303", "CS304"}


def test_student_registration_validation_and_duplicate(client):
    assert client.post("/api/students", json={"name": "A", "email": "bad"}).status_code == 400
    payload = {"name": "Sample Student", "email": "unique@example.test"}
    assert client.post("/api/students", json=payload).status_code == 201
    assert client.post("/api/students", json=payload).status_code == 409
    assert any(s["email"] == payload["email"] for s in client.get("/api/students").json["students"])


def test_enrollment_happy_path_duplicate_and_delete(client):
    student = create_student(client)
    course = client.get("/api/courses").json["courses"][0]["id"]
    payload = {"student_id": student, "course_id": course}
    created = client.post("/api/enrollments", json=payload)
    assert created.status_code == 201
    assert client.post("/api/enrollments", json=payload).status_code == 409
    enrollments = client.get("/api/enrollments").json["enrollments"]
    assert len(enrollments) == 1
    assert client.delete(f"/api/enrollments/{created.json['id']}").status_code == 200
    assert client.delete(f"/api/enrollments/{created.json['id']}").status_code == 404
    assert len(client.get("/api/enrollments").json["enrollments"]) == 0


def test_enrollment_missing_student(client):
    cid = client.get("/api/courses").json["courses"][0]["id"]
    assert client.post("/api/enrollments", json={"student_id": 999999, "course_id": cid}).status_code == 404


def test_enrollment_capacity(client):
    course = client.get("/api/courses").json["courses"][3]
    for _ in range(course["capacity"]):
        sid = create_student(client)
        assert client.post("/api/enrollments", json={"student_id": sid, "course_id": course["id"]}).status_code == 201
    extra_id = create_student(client)
    assert client.post("/api/enrollments", json={"student_id": extra_id, "course_id": course["id"]}).status_code == 409


def test_active_sessions_gauge(client):
    student = create_student(client)
    before = client.get("/api/summary").json["active_users"]
    result = client.post("/api/sessions", json={"student_id": student})
    assert result.status_code == 201
    token = result.json["token"]
    assert client.get("/api/summary").json["active_users"] == before + 1
    assert client.delete(f"/api/sessions/{token}").status_code == 200
    assert client.get("/api/summary").json["active_users"] == before


def test_slow_and_failure_endpoints(client):
    assert client.get("/api/demo/slow?delay_ms=0").status_code == 200
    assert client.get("/api/demo/slow?delay_ms=abc").status_code == 400
    assert client.get("/api/demo/error").status_code == 503


def test_metrics_content(client):
    client.get("/api/courses")
    client.get("/api/demo/error")
    text = client.get("/metrics").text
    assert "http_requests_total" in text
    assert "http_request_duration_seconds_bucket" in text
    assert "active_users" in text
    assert 'status="503"' in text
    assert "http_requests_in_progress" in text


def test_summary_counts_and_missing_route(client):
    assert client.get("/api/summary").json["courses"] == 4
    assert client.get("/api/does_not_exist").status_code == 404
    assert client.post("/api/students", json=[]).status_code == 400
