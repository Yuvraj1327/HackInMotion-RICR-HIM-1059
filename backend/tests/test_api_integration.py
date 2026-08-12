"""
End-to-end-ish API tests using FastAPI's dependency_overrides so we can
exercise real route handlers (auth guard, request validation, response
shape) without needing a live Supabase project.
"""
from fastapi.testclient import TestClient

from app.core.dependencies import CurrentUser, get_current_user
from app.main import app

client = TestClient(app)


def test_health_check():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_protected_endpoint_requires_auth():
    r = client.get("/api/v1/products")
    assert r.status_code == 401
    body = r.json()
    assert body["success"] is False


def test_protected_endpoint_rejects_garbage_token():
    r = client.get("/api/v1/products", headers={"Authorization": "Bearer not-a-real-token"})
    assert r.status_code == 401


def test_invalid_forecast_horizon_returns_422():
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id="u1", email="a@b.com")
    try:
        r = client.post(
            "/api/v1/forecasts/generate/11111111-1111-1111-1111-111111111111",
            json={"horizon_days": 99},  # not in [7, 14, 30]
        )
        assert r.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_invalid_uuid_path_param_returns_422():
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id="u1", email="a@b.com")
    try:
        r = client.get("/api/v1/products/not-a-uuid")
        assert r.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_docs_and_openapi_available():
    r = client.get("/docs")
    assert r.status_code == 200
    r2 = client.get("/openapi.json")
    assert r2.status_code == 200
    assert "paths" in r2.json()


def test_guest_endpoint_exists_and_requires_no_auth():
    # No Authorization header - guest session creation must be publicly
    # reachable, same as /register and /login.
    r = client.post("/api/v1/auth/guest")
    # In this test environment there's no live Supabase project, so the
    # call fails upstream (502) - the important assertions are that it
    # is NOT a 401 (i.e. it doesn't require auth) and NOT a 404 (i.e.
    # the route actually exists), and that the error is clean JSON.
    assert r.status_code not in (401, 404)
    body = r.json()
    assert body["success"] is False
    assert "detail" in body


def test_guest_endpoint_is_a_distinct_route_from_register():
    openapi = client.get("/openapi.json").json()
    assert "/api/v1/auth/guest" in openapi["paths"]
    assert "post" in openapi["paths"]["/api/v1/auth/guest"]
    # Confirm it's registered as its own operation, not an alias of
    # /register (regression guard against the original bug where
    # "Continue as Guest" silently called the public signup endpoint).
    guest_op = openapi["paths"]["/api/v1/auth/guest"]["post"]["operationId"]
    register_op = openapi["paths"]["/api/v1/auth/register"]["post"]["operationId"]
    assert guest_op != register_op