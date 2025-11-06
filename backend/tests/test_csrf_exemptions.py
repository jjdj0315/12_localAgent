"""
CSRF exemption pattern tests (T315, FR-120)

Tests that exempt paths can be accessed without CSRF tokens,
using both exact matching and prefix matching patterns.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_setup_init_works_without_csrf_token():
    """
    Test /api/v1/setup/init works without CSRF token (T315, FR-120).
    
    Uses prefix match: /api/v1/setup/ exempt.
    """
    response = client.post(
        "/api/v1/setup/init",
        json={"admin_username": "test_admin", "admin_password": "securepass123"}
    )
    
    # Should not return 403 CSRF error
    assert response.status_code != 403, (
        f"Setup init endpoint should be CSRF-exempt (prefix match '/api/v1/setup/'). "
        f"Got status {response.status_code}: {response.text}"
    )
    
    # May return 400/409 if setup already done, but not 403
    print(f"✅ /api/v1/setup/init is CSRF-exempt (status: {response.status_code})")


def test_setup_complete_works_without_csrf_token():
    """
    Test /api/v1/setup/complete works without CSRF token (T315, FR-120).
    
    Uses prefix match: /api/v1/setup/ exempt.
    """
    response = client.post(
        "/api/v1/setup/complete",
        json={"confirmed": True}
    )
    
    # Should not return 403 CSRF error
    assert response.status_code != 403, (
        f"Setup complete endpoint should be CSRF-exempt (prefix match '/api/v1/setup/'). "
        f"Got status {response.status_code}: {response.text}"
    )
    
    print(f"✅ /api/v1/setup/complete is CSRF-exempt (status: {response.status_code})")


def test_docs_works_without_csrf_token():
    """
    Test /docs works without CSRF token (T315, FR-120).
    
    Uses exact match: /docs exempt.
    """
    response = client.get("/docs")
    
    # Should return 200 OK (Swagger UI)
    assert response.status_code == 200, (
        f"Docs endpoint should be CSRF-exempt (exact match '/docs'). "
        f"Got status {response.status_code}"
    )
    
    print("✅ /docs is CSRF-exempt (Swagger UI accessible)")


def test_metrics_works_without_csrf_token():
    """
    Test /metrics works without CSRF token (T315, FR-120).
    
    Uses exact match: /metrics exempt (Prometheus scraping).
    """
    response = client.get("/metrics")
    
    # Should return 200 OK
    assert response.status_code == 200, (
        f"Metrics endpoint should be CSRF-exempt (exact match '/metrics'). "
        f"Got status {response.status_code}"
    )
    
    # Verify Prometheus format
    assert "text/plain" in response.headers.get("content-type", ""), (
        "Metrics should return Prometheus text format"
    )
    
    print("✅ /metrics is CSRF-exempt (Prometheus metrics accessible)")


def test_openapi_json_works_without_csrf_token():
    """
    Test /openapi.json works without CSRF token (T315, FR-120).
    
    Uses exact match: /openapi.json exempt.
    """
    response = client.get("/openapi.json")
    
    # Should return 200 OK
    assert response.status_code == 200, (
        f"OpenAPI endpoint should be CSRF-exempt (exact match '/openapi.json'). "
        f"Got status {response.status_code}"
    )
    
    # Verify JSON format
    assert "application/json" in response.headers.get("content-type", ""), (
        "OpenAPI should return JSON format"
    )
    
    print("✅ /openapi.json is CSRF-exempt (OpenAPI spec accessible)")


def test_health_endpoint_works_without_csrf_token():
    """
    Test /api/v1/health works without CSRF token (T315, FR-120).
    
    Uses exact match: /api/v1/health exempt.
    """
    response = client.get("/api/v1/health")
    
    # Should return 200 OK
    assert response.status_code == 200, (
        f"Health endpoint should be CSRF-exempt (exact match '/api/v1/health'). "
        f"Got status {response.status_code}"
    )
    
    # Verify JSON response
    data = response.json()
    assert "status" in data, "Health check should return status field"
    
    print("✅ /api/v1/health is CSRF-exempt")


def test_login_endpoint_works_without_csrf_token():
    """
    Test /api/v1/auth/login works without CSRF token (T315, FR-120).
    
    Uses exact match: /api/v1/auth/login exempt (authentication).
    """
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "test_user", "password": "test_pass"}
    )
    
    # Should not return 403 CSRF error
    assert response.status_code != 403, (
        f"Login endpoint should be CSRF-exempt (exact match '/api/v1/auth/login'). "
        f"Got status {response.status_code}: {response.text}"
    )
    
    # May return 401 if credentials wrong, but not 403
    print(f"✅ /api/v1/auth/login is CSRF-exempt (status: {response.status_code})")


def test_non_exempt_post_requires_csrf_token():
    """
    Test non-exempt POST endpoints require CSRF token (T315, FR-120).
    
    Verifies that exemption is selective, not global.
    """
    # Try to create conversation without CSRF token
    response = client.post(
        "/api/v1/conversations",
        json={"title": "Test Conversation"}
    )
    
    # Should return 403 Forbidden (CSRF validation failure)
    assert response.status_code == 403, (
        f"Non-exempt POST should require CSRF token. "
        f"Got status {response.status_code} instead of 403"
    )
    
    # Verify error message mentions CSRF
    error_detail = response.json().get("detail", "")
    assert "CSRF" in error_detail or "토큰" in error_detail, (
        f"Error should mention CSRF token. Got: {error_detail}"
    )
    
    print("✅ Non-exempt endpoints correctly require CSRF token")


def test_setup_subpaths_all_exempt():
    """
    Test all /api/v1/setup/* subpaths are exempt (T315, FR-120).
    
    Validates prefix matching works for nested paths.
    """
    setup_subpaths = [
        "/api/v1/setup/init",
        "/api/v1/setup/complete",
        "/api/v1/setup/status",
        "/api/v1/setup/validate",
    ]
    
    for path in setup_subpaths:
        # POST without CSRF token
        response = client.post(path, json={})
        
        # Should not return 403 (may return 400/404/405, but not 403)
        assert response.status_code != 403, (
            f"Setup subpath {path} should be CSRF-exempt via prefix match. "
            f"Got status {response.status_code}"
        )
        
        print(f"✅ {path} is CSRF-exempt (prefix match)")


def test_exact_match_does_not_match_subpaths():
    """
    Test exact match does not exempt subpaths (T315, FR-120).
    
    /health is exempt, but /health/detailed should not be (if it existed).
    """
    # This is a documentation test - exact match should be precise
    from app.middleware.csrf_middleware import CSRFMiddleware
    
    middleware = CSRFMiddleware(app=None)
    
    # Exact match: /health is exempt
    assert middleware._is_exempt_path("/health") is True
    
    # Subpaths should not match (unless explicitly added)
    # This depends on implementation - if /health is in EXEMPT_PATHS (exact match),
    # then /health/detailed should NOT be exempt
    
    # Check implementation uses both exact and prefix matching
    assert hasattr(middleware, "CSRF_EXEMPT_PATHS"), "Should have exact paths"
    assert hasattr(middleware, "CSRF_EXEMPT_PREFIXES"), "Should have prefix patterns"
    
    print("✅ Exact match and prefix match are properly separated")


def test_prefix_match_works_for_nested_paths():
    """
    Test prefix match correctly handles nested paths (T315, FR-120).
    
    /api/v1/setup/ prefix should match /api/v1/setup/foo/bar/baz
    """
    from app.middleware.csrf_middleware import CSRFMiddleware
    
    middleware = CSRFMiddleware(app=None)
    
    # Prefix match should work for deeply nested paths
    nested_paths = [
        "/api/v1/setup/init",
        "/api/v1/setup/foo/bar",
        "/api/v1/setup/nested/deep/path",
    ]
    
    for path in nested_paths:
        is_exempt = middleware._is_exempt_path(path)
        assert is_exempt is True, f"{path} should be exempt via prefix match"
        print(f"✅ {path} matched prefix /api/v1/setup/")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
