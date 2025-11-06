"""
Initial Setup API Endpoints

Provides setup wizard endpoint per FR-034.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ...core.database import get_db
from ...services.setup_service import SetupService


router = APIRouter(prefix="/setup", tags=["setup"])


class SetupRequest(BaseModel):
    """Initial setup request schema."""

    username: str = Field(..., min_length=3, max_length=50, description="Administrator username")
    password: str = Field(..., min_length=8, description="Administrator password (min 8 characters)")
    system_name: str = Field(default="Local LLM System", description="System display name")
    storage_path: str = Field(default="/data", description="Storage path for uploads and backups")


class SetupResponse(BaseModel):
    """Setup completion response."""

    message: str
    admin_username: str
    admin_id: str
    user_id: str
    setup_info: dict


@router.get("/status")
def get_setup_status():
    """
    Check if initial setup has been completed.

    Returns:
        dict: Setup completion status and info
    """
    is_complete = SetupService.is_setup_complete()

    if is_complete:
        setup_info = SetupService.get_setup_info()
        return {
            "setup_complete": True,
            "message": "System has been set up. Setup wizard is disabled.",
            "setup_info": setup_info
        }
    else:
        return {
            "setup_complete": False,
            "message": "System requires initial setup. Please complete the setup wizard."
        }


@router.post("/", response_model=SetupResponse, status_code=status.HTTP_201_CREATED)
def complete_initial_setup(
    setup_data: SetupRequest,
    db: Session = Depends(get_db)
):
    """
    Complete initial system setup (FR-034).

    Creates the first administrator account and setup.lock file.
    This endpoint can only be called once - subsequent calls return 403 Forbidden.

    Args:
        setup_data: Setup configuration including admin credentials
        db: Database session

    Returns:
        SetupResponse: Confirmation with admin details

    Raises:
        HTTPException 403: If setup is already complete (setup.lock exists)
        HTTPException 400: If admin creation fails
    """
    # Check if setup already complete
    if SetupService.is_setup_complete():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="설정이 이미 완료되었습니다. setup.lock 파일이 존재합니다. 재설정하려면 setup.lock 파일을 삭제하고 데이터베이스를 초기화하세요."
        )

    try:
        # Create initial admin and lock file
        result = SetupService.create_initial_admin(
            username=setup_data.username,
            password=setup_data.password,
            system_name=setup_data.system_name,
            storage_path=setup_data.storage_path,
            db=db
        )

        # Get setup info for response
        setup_info = SetupService.get_setup_info()

        return SetupResponse(
            message=result["message"],
            admin_username=result["admin_username"],
            admin_id=result["admin_id"],
            user_id=result["user_id"],
            setup_info=setup_info or {}
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"설정 중 오류가 발생했습니다: {str(e)}"
        )
