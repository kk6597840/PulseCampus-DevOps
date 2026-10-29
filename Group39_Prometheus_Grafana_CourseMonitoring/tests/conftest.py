import pytest
from app.main import create_app


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "unit_tests.sqlite3"))
    app = create_app(testing=True)
    with app.test_client() as test_client:
        yield test_client
