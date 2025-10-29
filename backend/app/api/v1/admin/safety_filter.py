"""
Safety Filter Admin API

Endpoints for administrators to manage safety filter rules and view statistics.
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.core.database import get_db
from app.api.deps import get_current_admin
from app.models.user import User
from app.models.safety_filter_rule import SafetyFilterRule, FilterCategory
from app.models.filter_event import FilterEvent
from app.schemas.safety_filter import (
    SafetyFilterRuleCreate,
    SafetyFilterRuleUpdate,
    SafetyFilterRuleResponse,
    FilterStatsResponse,
    FilterStatsByCategory,
    FilterConfigUpdate,
    FilterConfigResponse
)
from app.services.safety_filter_service import SafetyFilterService

router = APIRouter(prefix="/admin/safety-filter", tags=["admin", "safety-filter"])


# ============================================================================
# Filter Rule Management
# ============================================================================

@router.get("/rules", response_model=List[SafetyFilterRuleResponse])
async def list_filter_rules(
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """
    List all safety filter rules.

    **Permissions**: Admin only

    **Query Parameters**:
    - category: Filter by category (violence, sexual, dangerous, hate, pii)
    - is_active: Filter by active status
    """
    query = db.query(SafetyFilterRule)

    if category:
        try:
            filter_cat = FilterCategory(category)
            query = query.filter(SafetyFilterRule.category == filter_cat)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category. Must be one of: {[c.value for c in FilterCategory]}"
            )

    if is_active is not None:
        query = query.filter(SafetyFilterRule.is_active == is_active)

    rules = query.order_by(
        SafetyFilterRule.priority.desc(),
        SafetyFilterRule.created_at
    ).all()

    return rules


@router.post("/rules", response_model=SafetyFilterRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_filter_rule(
    rule_data: SafetyFilterRuleCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """
    Create a new safety filter rule.

    **Permissions**: Admin only

    **Example**:
    ```json
    {
      "name": "폭력 키워드",
      "description": "폭력 관련 키워드 차단",
      "category": "violence",
      "keywords": ["살인", "폭력", "테러"],
      "regex_patterns": [],
      "is_active": true,
      "priority": 10
    }
    ```
    """
    new_rule = SafetyFilterRule(
        **rule_data.dict(),
        created_by_admin_id=admin.id
    )

    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)

    # Clear filter cache to pick up new rule
    filter_service = SafetyFilterService(db)
    filter_service.rule_based_filter.clear_cache()

    return new_rule


@router.get("/rules/{rule_id}", response_model=SafetyFilterRuleResponse)
async def get_filter_rule(
    rule_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """Get a specific filter rule by ID"""
    rule = db.query(SafetyFilterRule).filter(SafetyFilterRule.id == rule_id).first()

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="필터 규칙을 찾을 수 없습니다."
        )

    return rule


@router.put("/rules/{rule_id}", response_model=SafetyFilterRuleResponse)
async def update_filter_rule(
    rule_id: UUID,
    rule_data: SafetyFilterRuleUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """
    Update an existing filter rule.

    **Permissions**: Admin only

    **Note**: System rules (is_system_rule=true) cannot be deleted but can be disabled.
    """
    rule = db.query(SafetyFilterRule).filter(SafetyFilterRule.id == rule_id).first()

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="필터 규칙을 찾을 수 없습니다."
        )

    # Update only provided fields
    update_data = rule_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rule, key, value)

    rule.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(rule)

    # Clear filter cache
    filter_service = SafetyFilterService(db)
    filter_service.rule_based_filter.clear_cache()

    return rule


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_filter_rule(
    rule_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """
    Delete a filter rule.

    **Permissions**: Admin only

    **Note**: System rules (is_system_rule=true) cannot be deleted.
    """
    rule = db.query(SafetyFilterRule).filter(SafetyFilterRule.id == rule_id).first()

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="필터 규칙을 찾을 수 없습니다."
        )

    if rule.is_system_rule:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="시스템 규칙은 삭제할 수 없습니다. 비활성화만 가능합니다."
        )

    db.delete(rule)
    db.commit()

    # Clear filter cache
    filter_service = SafetyFilterService(db)
    filter_service.rule_based_filter.clear_cache()

    return None


# ============================================================================
# Filter Statistics
# ============================================================================

@router.get("/stats", response_model=FilterStatsResponse)
async def get_filter_statistics(
    days: int = 7,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """
    Get safety filter statistics.

    **Permissions**: Admin only

    **Query Parameters**:
    - days: Number of days to include in statistics (default: 7)

    **Returns**:
    - Total events count
    - Events by category
    - Top triggered rules
    - Average processing time
    - Bypass attempt rate
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    # Total events
    total_events = db.query(func.count(FilterEvent.id)).scalar()

    # Events today
    events_today = db.query(func.count(FilterEvent.id)).filter(
        FilterEvent.created_at >= today_start
    ).scalar()

    # Events this period
    events_this_week = db.query(func.count(FilterEvent.id)).filter(
        FilterEvent.created_at >= cutoff_date
    ).scalar()

    # Events by category
    category_stats = db.query(
        FilterEvent.category,
        func.count(FilterEvent.id).label('total_count'),
        func.sum(func.cast(FilterEvent.action == 'blocked', func.Integer)).label('blocked_count'),
        func.sum(func.cast(FilterEvent.action == 'masked', func.Integer)).label('masked_count'),
        func.sum(func.cast(FilterEvent.action == 'warned', func.Integer)).label('warned_count')
    ).filter(
        FilterEvent.created_at >= cutoff_date
    ).group_by(
        FilterEvent.category
    ).all()

    by_category = [
        FilterStatsByCategory(
            category=cat,
            total_count=total or 0,
            blocked_count=blocked or 0,
            masked_count=masked or 0,
            warned_count=warned or 0
        )
        for cat, total, blocked, masked, warned in category_stats
    ]

    # Top triggered rules
    top_rules = db.query(
        SafetyFilterRule.id,
        SafetyFilterRule.name,
        SafetyFilterRule.category,
        SafetyFilterRule.match_count
    ).filter(
        SafetyFilterRule.match_count > 0
    ).order_by(
        desc(SafetyFilterRule.match_count)
    ).limit(10).all()

    top_triggered_rules = [
        {
            "rule_id": str(rule.id),
            "rule_name": rule.name,
            "category": rule.category.value,
            "count": rule.match_count
        }
        for rule in top_rules
    ]

    # Average processing time
    avg_time = db.query(func.avg(FilterEvent.processing_time_ms)).filter(
        FilterEvent.created_at >= cutoff_date,
        FilterEvent.processing_time_ms.isnot(None)
    ).scalar()

    # Bypass attempt rate
    total_with_bypass = db.query(func.count(FilterEvent.id)).filter(
        FilterEvent.created_at >= cutoff_date
    ).scalar()

    bypass_attempts = db.query(func.count(FilterEvent.id)).filter(
        FilterEvent.created_at >= cutoff_date,
        FilterEvent.bypass_attempted == True
    ).scalar()

    bypass_rate = (bypass_attempts / total_with_bypass * 100) if total_with_bypass > 0 else 0.0

    return FilterStatsResponse(
        total_events=total_events,
        events_today=events_today,
        events_this_week=events_this_week,
        by_category=by_category,
        top_triggered_rules=top_triggered_rules,
        avg_processing_time_ms=round(avg_time, 2) if avg_time else 0.0,
        bypass_attempt_rate=round(bypass_rate, 2)
    )


# ============================================================================
# Filter Configuration
# ============================================================================

@router.get("/config", response_model=FilterConfigResponse)
async def get_filter_config(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """
    Get current filter configuration.

    **Permissions**: Admin only
    """
    filter_service = SafetyFilterService(db)
    status_info = filter_service.get_filter_status()

    rule_count = db.query(func.count(SafetyFilterRule.id)).scalar()
    active_rule_count = db.query(func.count(SafetyFilterRule.id)).filter(
        SafetyFilterRule.is_active == True
    ).scalar()

    return FilterConfigResponse(
        enable_rule_based=status_info["rule_based_enabled"],
        enable_ml_based=status_info["ml_based_enabled"],
        ml_confidence_threshold=0.7,  # TODO: Make this configurable
        max_processing_time_ms=2000,  # FR-082
        rule_count=rule_count,
        active_rule_count=active_rule_count,
        ml_model_loaded=status_info["ml_based_enabled"]
    )


@router.post("/config/clear-cache", status_code=status.HTTP_200_OK)
async def clear_filter_cache(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """
    Clear filter rule cache.

    **Permissions**: Admin only

    **Use case**: Call after bulk updating filter rules to ensure changes take effect immediately.
    """
    filter_service = SafetyFilterService(db)
    filter_service.rule_based_filter.clear_cache()

    return {"message": "필터 캐시가 초기화되었습니다."}


# ============================================================================
# Bulk Operations
# ============================================================================

@router.post("/rules/bulk-toggle", status_code=status.HTTP_200_OK)
async def bulk_toggle_rules(
    category: str,
    is_active: bool,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """
    Enable or disable all rules in a category.

    **Permissions**: Admin only

    **Example**: Disable all violence filters temporarily
    ```
    POST /admin/safety-filter/rules/bulk-toggle?category=violence&is_active=false
    ```
    """
    try:
        filter_cat = FilterCategory(category)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category. Must be one of: {[c.value for c in FilterCategory]}"
        )

    updated_count = db.query(SafetyFilterRule).filter(
        SafetyFilterRule.category == filter_cat
    ).update(
        {"is_active": is_active, "updated_at": datetime.utcnow()},
        synchronize_session=False
    )

    db.commit()

    # Clear cache
    filter_service = SafetyFilterService(db)
    filter_service.rule_based_filter.clear_cache()

    action = "활성화" if is_active else "비활성화"
    return {
        "message": f"{category} 카테고리의 {updated_count}개 규칙이 {action}되었습니다.",
        "updated_count": updated_count
    }
