"""Prometheus metrics definitions

This module defines all Prometheus metrics for monitoring the application.
Metrics are organized by category:
- LLM performance
- API performance
- Database performance
- Business metrics
"""

from prometheus_client import Counter, Histogram, Gauge, Info

# ==============================================================================
# LLM Performance Metrics (가장 중요!)
# ==============================================================================

llm_request_duration = Histogram(
    'llm_request_duration_seconds',
    'LLM request duration in seconds',
    buckets=(1, 2, 5, 8, 10, 12, 15, 20, 30)  # 1초, 2초, 5초, ... 30초
)

llm_requests_total = Counter(
    'llm_requests_total',
    'Total number of LLM requests',
    ['status']  # 'success' or 'error'
)

llm_requests_in_progress = Gauge(
    'llm_requests_in_progress',
    'Number of LLM requests currently being processed'
)

# ==============================================================================
# API Performance Metrics
# ==============================================================================

http_request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint', 'status_code'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1, 2, 5)  # 10ms, 50ms, 100ms, ...
)

http_requests_total = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status_code']
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'Number of HTTP requests currently being processed'
)

# ==============================================================================
# Database Metrics
# ==============================================================================

db_connections_active = Gauge(
    'db_connections_active',
    'Number of active database connections'
)

db_query_duration = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type'],  # 'select', 'insert', 'update', 'delete'
    buckets=(0.001, 0.01, 0.05, 0.1, 0.5, 1, 2)
)

db_queries_total = Counter(
    'db_queries_total',
    'Total number of database queries',
    ['query_type', 'status']  # status: 'success' or 'error'
)

# ==============================================================================
# Business Metrics
# ==============================================================================

active_users_current = Gauge(
    'active_users_current',
    'Number of currently active users (logged in)'
)

conversations_total = Gauge(
    'conversations_total',
    'Total number of conversations in the system'
)

messages_total = Gauge(
    'messages_total',
    'Total number of messages in the system'
)

documents_uploaded_total = Counter(
    'documents_uploaded_total',
    'Total number of documents uploaded',
    ['status']  # 'success' or 'error'
)

# ==============================================================================
# System Info (static metadata)
# ==============================================================================

app_info = Info(
    'app_info',
    'Application information'
)

# Set static application info
app_info.info({
    'version': '0.1.0',
    'name': 'Local LLM Web Application',
    'environment': 'production'
})
