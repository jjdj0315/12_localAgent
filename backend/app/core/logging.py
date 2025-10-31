"""
Structured logging with correlation IDs (T228)

Provides:
- Request correlation IDs
- Structured JSON logging
- Log levels per component
- Performance tracking
"""

import logging
import sys
import json
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from contextvars import ContextVar

# Context variable for request correlation ID
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


class StructuredFormatter(logging.Formatter):
    """
    JSON formatter for structured logging
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id_var.get(),
        }

        # Add extra fields
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id

        if hasattr(record, "request_path"):
            log_data["request_path"] = record.request_path

        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms

        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code

        # Add exception info
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add stack trace for errors
        if record.levelno >= logging.ERROR and record.stack_info:
            log_data["stack_trace"] = self.formatStack(record.stack_info)

        return json.dumps(log_data, ensure_ascii=False)


def setup_logging(
    level: str = "INFO",
    json_format: bool = True
) -> None:
    """
    Setup application logging

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Use JSON structured logging
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    if json_format:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Set levels for noisy libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get logger for a module

    Args:
        name: Module name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def set_correlation_id(correlation_id: str = None) -> str:
    """
    Set correlation ID for current request

    Args:
        correlation_id: Correlation ID (generated if not provided)

    Returns:
        The correlation ID
    """
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())

    correlation_id_var.set(correlation_id)
    return correlation_id


def get_correlation_id() -> Optional[str]:
    """
    Get current correlation ID

    Returns:
        Correlation ID or None
    """
    return correlation_id_var.get()


def log_request(
    logger: logging.Logger,
    method: str,
    path: str,
    user_id: str = None,
    status_code: int = None,
    duration_ms: float = None
) -> None:
    """
    Log HTTP request

    Args:
        logger: Logger instance
        method: HTTP method
        path: Request path
        user_id: User ID (if authenticated)
        status_code: Response status code
        duration_ms: Request duration in milliseconds
    """
    extra = {
        "request_path": f"{method} {path}",
        "user_id": user_id,
        "status_code": status_code,
        "duration_ms": duration_ms
    }

    level = logging.INFO
    if status_code and status_code >= 500:
        level = logging.ERROR
    elif status_code and status_code >= 400:
        level = logging.WARNING

    logger.log(
        level,
        f"{method} {path} - {status_code} ({duration_ms:.2f}ms)" if duration_ms else f"{method} {path}",
        extra=extra
    )


def log_llm_generation(
    logger: logging.Logger,
    user_id: str,
    prompt_length: int,
    response_length: int,
    duration_ms: float,
    model: str = None
) -> None:
    """
    Log LLM generation

    Args:
        logger: Logger instance
        user_id: User ID
        prompt_length: Prompt character count
        response_length: Response character count
        duration_ms: Generation duration
        model: Model name
    """
    logger.info(
        f"LLM generation completed",
        extra={
            "user_id": user_id,
            "prompt_length": prompt_length,
            "response_length": response_length,
            "duration_ms": duration_ms,
            "model": model
        }
    )


def log_error(
    logger: logging.Logger,
    message: str,
    error: Exception = None,
    user_id: str = None,
    extra: Dict[str, Any] = None
) -> None:
    """
    Log error with structured data

    Args:
        logger: Logger instance
        message: Error message
        error: Exception object
        user_id: User ID
        extra: Additional data
    """
    log_extra = {"user_id": user_id}
    if extra:
        log_extra.update(extra)

    if error:
        logger.error(message, exc_info=error, extra=log_extra)
    else:
        logger.error(message, extra=log_extra)
