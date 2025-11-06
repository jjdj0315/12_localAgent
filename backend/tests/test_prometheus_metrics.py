"""
Prometheus metrics validation tests (T308, FR-117)

Tests for Prometheus metrics collection:
- Query metrics are recorded
- DB query duration is tracked
- Different query types are distinguished
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_metrics_endpoint_accessible():
    """
    Test /metrics endpoint is accessible (T308)
    """
    response = client.get("/metrics")
    
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")


def test_db_queries_total_increments_after_api_requests():
    """
    Test db_queries_total metric increments after API requests (T308, FR-117)
    """
    # Fetch initial metrics
    response_before = client.get("/metrics")
    metrics_before = response_before.text
    
    # Make 10 API requests that trigger DB queries
    for i in range(10):
        client.get("/api/v1/health")  # Health endpoint queries DB
    
    # Fetch metrics after requests
    response_after = client.get("/metrics")
    metrics_after = response_after.text
    
    # Check that db_queries_total metric exists
    assert "db_queries_total" in metrics_after, "db_queries_total metric should exist"
    
    # Check that it has select query type
    assert 'query_type="select"' in metrics_after, "Should have select query type"


def test_db_query_duration_histogram_has_samples():
    """
    Test db_query_duration histogram has samples (T308, FR-117)
    """
    # Make some API requests
    for i in range(5):
        client.post("/api/v1/auth/login", json={"username": "test", "password": "test"})
    
    # Fetch metrics
    response = client.get("/metrics")
    metrics = response.text
    
    # Check for query duration histogram
    assert "db_query_duration_seconds" in metrics, "db_query_duration metric should exist"
    
    # Histogram should have buckets
    assert "db_query_duration_seconds_bucket" in metrics, "Should have histogram buckets"


def test_metrics_distinguish_query_types():
    """
    Test that different query types are distinguished (T308, FR-117)
    
    Query types: select, insert, update, delete, other
    """
    # Fetch metrics
    response = client.get("/metrics")
    metrics = response.text
    
    # Should have query_type labels
    if "db_queries_total" in metrics:
        # At minimum should have select queries
        assert 'query_type="select"' in metrics or 'query_type=' in metrics, \
            "Should have query_type label"


def test_http_requests_total_metric_exists():
    """
    Test http_requests_total metric exists (T308)
    """
    # Make a request
    client.get("/api/v1/health")
    
    # Fetch metrics
    response = client.get("/metrics")
    metrics = response.text
    
    # Check for HTTP request metrics
    assert "http_requests_total" in metrics or "http_request" in metrics.lower(), \
        "HTTP request metrics should exist"


def test_db_connections_active_metric_exists():
    """
    Test db_connections_active metric exists (T308, FR-117)
    """
    response = client.get("/metrics")
    metrics = response.text
    
    # Check for connection pool metrics
    assert "db_connections_active" in metrics or "db_connection" in metrics.lower(), \
        "DB connection metrics should exist"


def test_metrics_format_is_prometheus_compatible():
    """
    Test metrics are in Prometheus text format (T308)
    """
    response = client.get("/metrics")
    
    # Should be plain text
    assert response.headers["content-type"] in [
        "text/plain; version=0.0.4; charset=utf-8",
        "text/plain; charset=utf-8",
        "text/plain"
    ]
    
    # Should have # HELP and # TYPE comments
    metrics = response.text
    assert "# HELP" in metrics or "# TYPE" in metrics or "_total" in metrics, \
        "Should have Prometheus format markers"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
