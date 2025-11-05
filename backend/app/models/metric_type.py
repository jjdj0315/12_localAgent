"""MetricType enum for tracking system metrics

This module defines the types of metrics collected by the admin dashboard
metrics history feature (Feature 002).
"""
from enum import Enum


class MetricType(str, Enum):
    """Metric types tracked by the system (from FR-002)"""
    ACTIVE_USERS = "active_users"
    STORAGE_BYTES = "storage_bytes"
    ACTIVE_SESSIONS = "active_sessions"
    CONVERSATION_COUNT = "conversation_count"
    DOCUMENT_COUNT = "document_count"
    TAG_COUNT = "tag_count"

    @property
    def display_name_ko(self) -> str:
        """Korean display name for UI"""
        return {
            "active_users": "활성 사용자",
            "storage_bytes": "저장 공간",
            "active_sessions": "활성 세션",
            "conversation_count": "대화 수",
            "document_count": "문서 수",
            "tag_count": "태그 수",
        }[self.value]

    @property
    def unit(self) -> str:
        """Unit of measurement"""
        return {
            "active_users": "명",
            "storage_bytes": "bytes",
            "active_sessions": "개",
            "conversation_count": "개",
            "document_count": "개",
            "tag_count": "개",
        }[self.value]
