"""
Test configuration and fixtures for Safety Filter tests
"""
import sys
from pathlib import Path

# Add backend to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base
from app.models.safety_filter_rule import SafetyFilterRule, FilterCategory
from app.models.filter_event import FilterEvent
from app.models.user import User
from datetime import datetime
import uuid


@pytest.fixture(scope="function")
def test_db_session():
    """Create a clean test database session for each test"""
    # Use in-memory SQLite for fast testing
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    # Seed default filter rules
    _seed_default_rules(session)

    yield session

    session.close()


def _seed_default_rules(session):
    """Seed default safety filter rules for testing"""
    default_rules = [
        SafetyFilterRule(
            id=uuid.uuid4(),
            name="폭력 키워드",
            description="폭력적인 표현 차단",
            category=FilterCategory.VIOLENCE,
            keywords=["죽이", "때리", "폭행", "살해"],
            regex_patterns=[r"\b(공격|폭력)\b"],
            is_active=True,
            is_system_rule=True,
            priority=10,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        ),
        SafetyFilterRule(
            id=uuid.uuid4(),
            name="성적 키워드",
            description="부적절한 성적 표현 차단",
            category=FilterCategory.SEXUAL,
            keywords=["성관계", "음란"],
            regex_patterns=[],
            is_active=True,
            is_system_rule=True,
            priority=10,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        ),
        SafetyFilterRule(
            id=uuid.uuid4(),
            name="혐오 발언",
            description="차별적 혐오 표현 차단",
            category=FilterCategory.HATE,
            keywords=["혐오", "차별"],
            regex_patterns=[],
            is_active=True,
            is_system_rule=True,
            priority=10,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        ),
        SafetyFilterRule(
            id=uuid.uuid4(),
            name="위험 정보",
            description="위험한 정보 차단",
            category=FilterCategory.DANGEROUS,
            keywords=["폭탄 제조", "마약 제조"],
            regex_patterns=[],
            is_active=True,
            is_system_rule=True,
            priority=10,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        ),
        SafetyFilterRule(
            id=uuid.uuid4(),
            name="개인정보",
            description="개인정보 보호",
            category=FilterCategory.PII,
            keywords=[],
            regex_patterns=[r'\b\d{6}[-\s]?\d{7}\b'],  # 주민등록번호
            is_active=True,
            is_system_rule=True,
            priority=10,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    ]

    for rule in default_rules:
        session.add(rule)

    session.commit()


@pytest.fixture
def test_user_id():
    """Provide a test user UUID"""
    return uuid.uuid4()


@pytest.fixture
def test_conversation_id():
    """Provide a test conversation UUID"""
    return uuid.uuid4()
