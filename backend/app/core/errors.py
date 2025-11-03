"""Korean error messages for the application

This module provides centralized error messages in Korean for consistent
user-facing error handling across the application.
"""

# ============================================================================
# Metrics Feature Error Messages (Feature 002)
# ============================================================================

# Metric collection errors (FR-019, FR-020)
METRICS_COLLECTION_FAILED = "메트릭 수집에 실패했습니다: {metric_type}"
METRICS_COLLECTION_RETRY_EXHAUSTED = "메트릭 수집 최대 재시도 횟수 초과: {metric_type}"
METRICS_UNKNOWN_TYPE = "알 수 없는 메트릭 타입: {metric_type}"
METRICS_DB_QUERY_ERROR = "메트릭 데이터베이스 쿼리 오류: {error}"

# Metric query errors (FR-017)
METRICS_INVALID_GRANULARITY = "잘못된 세분성 값입니다. 'hourly' 또는 'daily'만 허용됩니다."
METRICS_INVALID_TIME_RANGE = "잘못된 시간 범위입니다. 시작 시간이 종료 시간보다 늦습니다."
METRICS_TIME_RANGE_TOO_LARGE = "요청한 시간 범위가 너무 큽니다. 최대 {max_days}일까지만 조회 가능합니다."
METRICS_NO_DATA_FOUND = "선택한 기간 동안 메트릭 데이터가 없습니다."

# Period comparison errors (FR-022)
METRICS_COMPARISON_PERIOD_MISMATCH = "비교 기간의 길이가 일치하지 않습니다."
METRICS_COMPARISON_INSUFFICIENT_DATA = "기간 비교를 위한 데이터가 부족합니다."

# Export errors (FR-024, FR-025)
METRICS_EXPORT_FAILED = "메트릭 데이터 내보내기에 실패했습니다: {error}"
METRICS_EXPORT_TOO_MANY_TYPES = "한 번에 최대 {max_types}개의 메트릭만 내보낼 수 있습니다."
METRICS_EXPORT_FILE_SIZE_EXCEEDED = "내보내기 파일 크기가 제한({max_size}MB)을 초과했습니다."
METRICS_EXPORT_INVALID_FORMAT = "잘못된 내보내기 형식입니다. 'csv' 또는 'pdf'만 허용됩니다."

# Chart rendering errors (FR-017, FR-018)
METRICS_CHART_RENDER_FAILED = "차트 렌더링에 실패했습니다: {error}"
METRICS_DOWNSAMPLE_FAILED = "데이터 다운샘플링에 실패했습니다: {error}"

# Scheduler errors (FR-018)
SCHEDULER_NOT_INITIALIZED = "스케줄러가 초기화되지 않았습니다."
SCHEDULER_ALREADY_RUNNING = "스케줄러가 이미 실행 중입니다."
SCHEDULED_TASK_FAILED = "예약 작업 실행 실패: {task_name}"

# ============================================================================
# General Application Error Messages
# ============================================================================

# Authentication errors
AUTH_INVALID_CREDENTIALS = "이메일 또는 비밀번호가 올바르지 않습니다."
AUTH_TOKEN_EXPIRED = "세션이 만료되었습니다. 다시 로그인해주세요."
AUTH_TOKEN_INVALID = "유효하지 않은 인증 토큰입니다."
AUTH_INSUFFICIENT_PERMISSIONS = "이 작업을 수행할 권한이 없습니다."

# Database errors
DB_CONNECTION_FAILED = "데이터베이스 연결에 실패했습니다."
DB_QUERY_FAILED = "데이터베이스 쿼리 실행에 실패했습니다: {error}"
DB_CONSTRAINT_VIOLATION = "데이터 무결성 제약 조건 위반: {constraint}"

# Validation errors
VALIDATION_REQUIRED_FIELD = "{field} 필드는 필수입니다."
VALIDATION_INVALID_FORMAT = "{field} 형식이 올바르지 않습니다."
VALIDATION_OUT_OF_RANGE = "{field} 값이 허용 범위를 벗어났습니다."

# Generic errors
INTERNAL_SERVER_ERROR = "서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
RESOURCE_NOT_FOUND = "요청한 리소스를 찾을 수 없습니다."
OPERATION_FAILED = "작업 수행에 실패했습니다: {error}"
