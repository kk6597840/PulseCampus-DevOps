"""SQLite persistence for the student course registration demonstration."""
from contextlib import contextmanager
from pathlib import Path
import os
import sqlite3

DEFAULT_COURSES = (
    ("CS301", "Cloud Computing Basics", "Dr. Meera Shah", 35),
    ("CS302", "DevOps Foundations", "Prof. Arjun Rao", 40),
    ("CS303", "Python Web Engineering", "Prof. Riya Singh", 30),
    ("CS304", "Observability & Monitoring", "Prof. Neha Iyer", 25),
)


def database_path():
    return Path(os.environ.get("DATABASE_PATH", "data/registrations.sqlite3"))


@contextmanager
def connection():
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                instructor TEXT NOT NULL,
                capacity INTEGER NOT NULL CHECK (capacity > 0)
            );
            CREATE TABLE IF NOT EXISTS enrollments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
                course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (student_id, course_id)
            );
            CREATE INDEX IF NOT EXISTS idx_enrollments_course ON enrollments(course_id);
        """)
        conn.executemany(
            "INSERT OR IGNORE INTO courses (code, title, instructor, capacity) VALUES (?, ?, ?, ?)",
            DEFAULT_COURSES,
        )
