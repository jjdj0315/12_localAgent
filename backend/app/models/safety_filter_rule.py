"""
Safety Filter Rule Model

This model stores administrator-defined rules for content filtering.
Supports keyword-based and regex-based filtering across multiple categories.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, Enum as SQLEnum, Integer
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base


class FilterCategory(str, enum.Enum):
    """Content filter categories"""
    VIOLENCE = "violence"           # 폭력성
    SEXUAL = "sexual"               # 성적인 내용
    DANGEROUS = "dangerous"         # 위험한 질문
    HATE = "hate"                   # 혐오 발언
    PII = "pii"                     # 개인정보


class SafetyFilterRule(Base):
    """
    Safety Filter Rule Model

    Stores filtering rules that can be managed by administrators.
    Rules include keywords, regex patterns, and category assignments.

    Example:
        - Violence keywords: ["살인", "폭력", "테러"]
        - PII regex: r"\d{6}-\d{7}"  (주민등록번호)
    """
    __tablename__ = "safety_filter_rules"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Rule metadata
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(SQLEnum(FilterCategory), nullable=False, index=True)

    # Rule configuration
    keywords = Column(ARRAY(String), default=list, nullable=False)  # Exact match keywords
    regex_patterns = Column(ARRAY(String), default=list, nullable=False)  # Regex patterns
    replacement_text = Column(String(500), nullable=True)  # For PII masking (e.g., "***")

    # Rule status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_system_rule = Column(Boolean, default=False, nullable=False)  # Cannot be deleted

    # Priority (higher = checked first)
    priority = Column(Integer, default=0, nullable=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by_admin_id = Column(UUID(as_uuid=True), nullable=True)  # Admin who created this rule

    # Statistics
    match_count = Column(Integer, default=0, nullable=False)  # How many times this rule matched

    def __repr__(self):
        return f"<SafetyFilterRule(id={self.id}, name={self.name}, category={self.category}, active={self.is_active})>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "keywords": self.keywords,
            "regex_patterns": self.regex_patterns,
            "replacement_text": self.replacement_text,
            "is_active": self.is_active,
            "is_system_rule": self.is_system_rule,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "match_count": self.match_count
        }
