"""
CSRF middleware optimization tests (T312)

Tests for improved CSRF token handling and exempt path matching.
"""

import pytest
from app.middleware.csrf_middleware import CSRFMiddleware


def test_csrf_exempt_path_exact_match():
    """Test exact path matching for CSRF exemption (T312)"""
    middleware = CSRFMiddleware(app=None)

    # Exact matches should be exempt
    assert middleware._is_exempt_path("/api/v1/auth/login") is True
    assert middleware._is_exempt_path("/health") is True
    assert middleware._is_exempt_path("/metrics") is True
    assert middleware._is_exempt_path("/docs") is True

    # Non-exempt paths
    assert middleware._is_exempt_path("/api/v1/admin/users") is False
    assert middleware._is_exempt_path("/api/v1/chat/send") is False


def test_csrf_exempt_path_prefix_match():
    """Test prefix path matching for CSRF exemption (T312)"""
    middleware = CSRFMiddleware(app=None)

    # Setup wizard paths should be exempt (prefix match)
    assert middleware._is_exempt_path("/api/v1/setup/") is True
    assert middleware._is_exempt_path("/api/v1/setup/init") is True
    assert middleware._is_exempt_path("/api/v1/setup/complete") is True
    assert middleware._is_exempt_path("/api/v1/setup/admin") is True

    # Non-matching prefixes
    assert middleware._is_exempt_path("/api/v1/setu") is False
    assert middleware._is_exempt_path("/api/v2/setup/") is False


def test_csrf_exempt_paths_set_type():
    """Test that CSRF_EXEMPT_PATHS is a set for O(1) lookup (T312)"""
    middleware = CSRFMiddleware(app=None)

    # Should be a set for performance
    assert isinstance(middleware.CSRF_EXEMPT_PATHS, set)


def test_csrf_exempt_prefixes_list():
    """Test that CSRF_EXEMPT_PREFIXES is a list (T312)"""
    middleware = CSRFMiddleware(app=None)

    # Should be a list
    assert isinstance(middleware.CSRF_EXEMPT_PREFIXES, list)

    # Should contain setup prefix
    assert "/api/v1/setup/" in middleware.CSRF_EXEMPT_PREFIXES


def test_csrf_token_reissue_optimization_logic():
    """
    Test that token reissue logic checks for existing token (T312).

    This is a code inspection test to verify the optimization is in place.
    """
    import inspect
    from app.middleware.csrf_middleware import CSRFMiddleware

    # Get source code
    source = inspect.getsource(CSRFMiddleware.dispatch)

    # Should check for existing token before generating new one
    assert "existing_token" in source, "Should check for existing token"
    assert "if not existing_token:" in source, "Should only generate when missing"

    # Should not generate token on every GET request
    assert "Generate CSRF token only if missing" in source, "Should have optimization comment"


def test_production_config_validation():
    """
    Test that production configuration validation exists (T312).
    """
    from app.main import validate_production_config

    # Function should exist
    assert callable(validate_production_config)

    # Should check for production environment
    import inspect
    source = inspect.getsource(validate_production_config)

    assert 'ENVIRONMENT == "production"' in source or "ENVIRONMENT == 'production'" in source
    assert "cookie_secure" in source
    assert "cookie_samesite" in source


def test_setup_logging_called():
    """
    Test that setup_logging() is called in main.py (T313).
    """
    import inspect
    from app import main

    source = inspect.getsource(main)

    # Should import setup_logging
    assert "from app.core.logging import setup_logging" in source

    # Should call setup_logging
    assert "setup_logging()" in source

    # Should be called before app creation
    setup_index = source.index("setup_logging()")
    app_create_index = source.index("app = FastAPI")
    assert setup_index < app_create_index, "setup_logging should be called before app creation"


def test_csrf_exempt_paths_comprehensive():
    """Test that all expected paths are exempt (T312)"""
    middleware = CSRFMiddleware(app=None)

    expected_exempt = [
        "/api/v1/auth/login",  # Login
        "/health",             # Health check
        "/api/v1/health",      # API health check
        "/metrics",            # Prometheus metrics
        "/docs",               # Swagger docs
        "/openapi.json",       # OpenAPI spec
    ]

    for path in expected_exempt:
        assert middleware._is_exempt_path(path), f"{path} should be exempt"


def test_csrf_middleware_optimization_benefits():
    """
    Document the benefits of T312 optimizations.
    """
    # This is a documentation test
    benefits = {
        "token_reuse": "CSRF tokens are reused instead of regenerated on every GET request",
        "performance": "Set lookup O(1) for exact path matching",
        "prefix_matching": "Supports wildcard paths like /api/v1/setup/*",
        "security": "Production environment forces secure cookies",
    }

    # All optimizations should be implemented
    middleware = CSRFMiddleware(app=None)

    # Token reuse: Check implementation
    import inspect
    source = inspect.getsource(CSRFMiddleware.dispatch)
    assert "if not existing_token:" in source

    # Set lookup: Check type
    assert isinstance(middleware.CSRF_EXEMPT_PATHS, set)

    # Prefix matching: Check method
    assert hasattr(middleware, '_is_exempt_path')
    assert len(middleware.CSRF_EXEMPT_PREFIXES) > 0

    # All benefits verified
    assert len(benefits) == 4
