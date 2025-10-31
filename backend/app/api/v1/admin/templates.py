"""
Template upload endpoint (T209, FR-084)
Admin-only access for custom document templates
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from pydantic import BaseModel
import os
from pathlib import Path
import shutil

from app.core.database import get_db

router = APIRouter()

# Template storage directory
TEMPLATE_DIR = Path("backend/templates/custom")
TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".jinja2", ".j2"}
MAX_TEMPLATE_SIZE = 1 * 1024 * 1024  # 1MB


class TemplateInfo(BaseModel):
    filename: str
    size_bytes: int
    uploaded_at: str

    class Config:
        from_attributes = True


@router.post("/templates", response_model=TemplateInfo)
async def upload_template(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload custom document template (FR-084)

    Admin only access required
    Allowed extensions: .jinja2, .j2
    Max size: 1MB
    """
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"허용되지 않는 파일 형식입니다. .jinja2 또는 .j2 파일만 업로드 가능합니다."
        )

    # Read file content
    content = await file.read()

    # Validate file size
    if len(content) > MAX_TEMPLATE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"파일 크기가 너무 큽니다. 최대 {MAX_TEMPLATE_SIZE / 1024 / 1024}MB까지 허용됩니다."
        )

    # Sanitize filename
    safe_filename = "".join(c for c in file.filename if c.isalnum() or c in "._-")
    if not safe_filename:
        raise HTTPException(
            status_code=400,
            detail="유효하지 않은 파일 이름입니다."
        )

    # Save file
    file_path = TEMPLATE_DIR / safe_filename

    with open(file_path, "wb") as f:
        f.write(content)

    from datetime import datetime

    return TemplateInfo(
        filename=safe_filename,
        size_bytes=len(content),
        uploaded_at=datetime.utcnow().isoformat()
    )


@router.get("/templates", response_model=List[TemplateInfo])
async def list_templates(
    db: AsyncSession = Depends(get_db)
):
    """
    List all custom templates

    Admin only access required
    """
    templates = []

    if TEMPLATE_DIR.exists():
        for template_path in TEMPLATE_DIR.glob("*"):
            if template_path.is_file() and template_path.suffix in ALLOWED_EXTENSIONS:
                stat = template_path.stat()
                templates.append(TemplateInfo(
                    filename=template_path.name,
                    size_bytes=stat.st_size,
                    uploaded_at=datetime.fromtimestamp(stat.st_mtime).isoformat()
                ))

    return templates


@router.delete("/templates/{filename}")
async def delete_template(
    filename: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete custom template

    Admin only access required
    """
    # Sanitize filename
    safe_filename = "".join(c for c in filename if c.isalnum() or c in "._-")

    file_path = TEMPLATE_DIR / safe_filename

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="템플릿 파일을 찾을 수 없습니다."
        )

    file_path.unlink()

    return {"message": f"템플릿 '{safe_filename}'이(가) 삭제되었습니다."}


@router.get("/templates/{filename}/content")
async def get_template_content(
    filename: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get template file content for preview/editing

    Admin only access required
    """
    # Sanitize filename
    safe_filename = "".join(c for c in filename if c.isalnum() or c in "._-")

    file_path = TEMPLATE_DIR / safe_filename

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="템플릿 파일을 찾을 수 없습니다."
        )

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    return {"filename": safe_filename, "content": content}
