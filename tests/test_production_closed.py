"""With APP_ENV=production (the default) the demo login, the test page and the health details are closed."""
import pytest
from fastapi.testclient import TestClient

from app.config import get_settings


@pytest.fixture
def client(monkeypatch):
    from app.main import app

    def switch(env: str) -> TestClient:
        monkeypatch.setenv("APP_ENV", env)
        get_settings.cache_clear()
        return TestClient(app)

    yield switch
    monkeypatch.setenv("APP_ENV", "development")
    get_settings.cache_clear()


def test_default_environment_is_production(monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)
    get_settings.cache_clear()
    try:
        assert get_settings().app_env == "production"
    finally:
        get_settings.cache_clear()


def test_production_closes_the_demo_login(client):
    c = client("production")
    assert c.get("/api/dev/users").status_code == 404
    assert c.post("/api/dev/login", json={"username": "purchase", "password": "purchase123"}).status_code == 404


def test_production_shows_a_sign_in_notice_instead_of_the_test_page(client):
    c = client("production")
    for path in ("/", "/login"):
        body = c.get(path).text
        assert "Please sign in" in body and "https://autorocket.in" in body
        assert "demo" not in body.lower()


def test_production_health_is_only_ok(client):
    assert client("production").get("/healthz").json() == {"status": "ok"}


def test_development_keeps_the_test_page_and_health_detail(client):
    c = client("development")
    assert c.get("/api/dev/users").status_code == 200
    assert "Please sign in" not in c.get("/").text
    assert "vector_store_backend" in c.get("/healthz").json()


def test_chat_still_needs_a_token(client):
    c = client("production")
    assert c.post("/api/v1/chat", json={"message": "hi"}).status_code in (401, 403, 422)
