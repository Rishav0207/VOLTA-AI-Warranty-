"""Integration tests for the FastAPI app."""

import importlib
import os
import sys

from fastapi.testclient import TestClient


def _client(tmp_path) -> TestClient:
    """Create a TestClient with an isolated SQLite database."""
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_path / 'test.db'}"
    os.environ["WARRANTY_APP_SECRET"] = "test-secret"
    sys.modules.pop("main", None)
    from config import get_settings

    get_settings.cache_clear()
    main = importlib.import_module("main")
    return TestClient(main.app)


def test_health_and_auth_flow(tmp_path) -> None:
    """Health, login, and refresh-token flow work end to end."""
    with _client(tmp_path) as client:
        assert client.get("/health").json()["status"] == "healthy"
        response = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
        assert response.status_code == 200
        body = response.json()
        assert body["access_token"]
        assert body["refresh_token"]
        refresh = client.post("/auth/refresh", json={"refresh_token": body["refresh_token"]})
        assert refresh.status_code == 200


def test_customer_registration_claim_and_search(tmp_path) -> None:
    """Customer can register, create a claim, and search semantically."""
    with _client(tmp_path) as client:
        client.post(
            "/auth/register",
            json={
                "username": "customer1",
                "password": "password123",
                "full_name": "Customer One",
                "email": "customer1@example.com",
            },
        )
        login = client.post("/auth/login", json={"username": "customer1", "password": "password123"}).json()
        headers = {"Authorization": f"Bearer {login['access_token']}"}
        products = client.get("/products", headers=headers).json()
        registered = client.post(
            "/customer/register-product",
            headers=headers,
            json={"product_id": products[0]["id"], "serial_number": "SERIAL-1001", "purchase_date": "2026-01-01"},
        )
        assert registered.status_code == 200
        claim = client.post(
            "/customer/service-requests",
            headers=headers,
            json={"customer_product_id": registered.json()["id"], "issue_description": "The motor stopped under normal use."},
        )
        assert claim.status_code == 200
        assert claim.json()["ai_explanation"]["confidence_score"] >= 0
        search = client.post("/api/v1/ai/search", headers=headers, json={"query": "motor warranty", "limit": 5})
        assert search.status_code == 200
