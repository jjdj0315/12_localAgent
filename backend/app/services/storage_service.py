"""
Storage management service.

Implements automatic cleanup when user storage reaches 10GB limit
per Clarification 2025-10-28.
"""
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.document import Document
from app.models.user import User

logger = logging.getLogger(__name__)

# Storage limits per Clarification 2025-10-28
USER_STORAGE_LIMIT_BYTES = 10 * 1024 * 1024 * 1024  # 10GB
WARNING_THRESHOLD = 0.8  # 80% of limit
CLEANUP_TARGET_BYTES = 9 * 1024 * 1024 * 1024  # 9GB (10% buffer after cleanup)
INACTIVE_DAYS_THRESHOLD = 30  # Delete items inactive for 30+ days


class StorageService:
    """Service for managing user storage quotas and automatic cleanup."""

    def __init__(self, db: Session):
        self.db = db

    def get_user_storage_usage(self, user_id: UUID) -> Dict[str, int]:
        """
        Calculate total storage usage for a user.

        Returns:
            Dict with:
            - total_bytes: Total storage used
            - conversation_count: Number of conversations
            - document_count: Number of documents
            - message_bytes: Approximate bytes from message content
            - document_bytes: Total bytes from uploaded documents
        """
        # Calculate message storage (approximate: chars * 2 for UTF-8)
        message_bytes = (
            self.db.query(func.coalesce(func.sum(func.length(Message.content) * 2), 0))
            .join(Conversation)
            .filter(Conversation.user_id == user_id)
            .scalar()
        ) or 0

        # Calculate document storage
        document_stats = (
            self.db.query(
                func.count(Document.id),
                func.coalesce(func.sum(Document.file_size), 0)
            )
            .filter(Document.user_id == user_id)
            .one()
        )
        document_count = document_stats[0]
        document_bytes = document_stats[1]

        # Count conversations
        conversation_count = (
            self.db.query(func.count(Conversation.id))
            .filter(Conversation.user_id == user_id)
            .scalar()
        ) or 0

        total_bytes = message_bytes + document_bytes

        return {
            "total_bytes": total_bytes,
            "conversation_count": conversation_count,
            "document_count": document_count,
            "message_bytes": message_bytes,
            "document_bytes": document_bytes,
        }

    def check_storage_warning(self, user_id: UUID) -> Optional[Dict]:
        """
        Check if user storage exceeds 80% warning threshold.

        Returns:
            Dict with warning info if threshold exceeded, None otherwise.
        """
        usage = self.get_user_storage_usage(user_id)
        total_bytes = usage["total_bytes"]

        if total_bytes >= USER_STORAGE_LIMIT_BYTES * WARNING_THRESHOLD:
            percentage = (total_bytes / USER_STORAGE_LIMIT_BYTES) * 100
            return {
                "total_bytes": total_bytes,
                "limit_bytes": USER_STORAGE_LIMIT_BYTES,
                "percentage": percentage,
                "message": f"저장 공간의 {percentage:.1f}%를 사용 중입니다. ({total_bytes / (1024**3):.2f}GB / 10GB)"
            }

        return None

    def auto_cleanup(self, user_id: UUID) -> Dict:
        """
        Automatically cleanup old conversations/documents when storage reaches 10GB.

        Per Clarification 2025-10-28:
        - Delete conversations/documents inactive for 30+ days
        - Delete oldest first (by last_accessed_at)
        - Stop when storage drops below 9GB (10% buffer)
        - If all items are recent (<30 days), raise error

        Returns:
            Dict with cleanup results:
            - deleted_conversations: List of deleted conversation titles
            - deleted_documents: List of deleted document filenames
            - space_recovered_bytes: Total space freed
            - remaining_bytes: Storage after cleanup
        """
        usage = self.get_user_storage_usage(user_id)
        current_bytes = usage["total_bytes"]

        if current_bytes < USER_STORAGE_LIMIT_BYTES:
            return {
                "deleted_conversations": [],
                "deleted_documents": [],
                "space_recovered_bytes": 0,
                "remaining_bytes": current_bytes,
                "message": "저장 공간이 한도 미만입니다. 정리가 필요하지 않습니다."
            }

        logger.info(f"User {user_id} storage at {current_bytes / (1024**3):.2f}GB, starting auto-cleanup")

        # Find conversations inactive for 30+ days, ordered by oldest first
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=INACTIVE_DAYS_THRESHOLD)

        old_conversations = (
            self.db.query(Conversation)
            .filter(
                Conversation.user_id == user_id,
                Conversation.last_accessed_at < cutoff_date
            )
            .order_by(Conversation.last_accessed_at.asc())
            .all()
        )

        if not old_conversations:
            # No old items to delete, user must manually delete
            raise ValueError(
                "저장 공간이 부족합니다. 사용하지 않는 대화나 문서를 삭제해주세요. "
                f"(현재: {current_bytes / (1024**3):.2f}GB / 10GB)"
            )

        deleted_conversations = []
        deleted_documents = []
        space_recovered = 0

        for conversation in old_conversations:
            # Calculate conversation size
            conv_size = conversation.storage_size_bytes or 0

            # Get document info before deletion
            docs = self.db.query(Document).filter(Document.conversation_id == conversation.id).all()
            doc_info = [
                {
                    "filename": doc.filename,
                    "size_bytes": doc.file_size,
                    "file_path": doc.file_path
                }
                for doc in docs
            ]

            # Delete conversation (cascades to messages and documents)
            conversation_title = conversation.title
            self.db.delete(conversation)
            self.db.flush()

            # Delete physical files
            for doc in doc_info:
                try:
                    file_path = Path(doc["file_path"])
                    if file_path.exists():
                        file_path.unlink()
                        logger.info(f"Deleted file: {doc['file_path']}")
                except Exception as e:
                    logger.error(f"Failed to delete file {doc['file_path']}: {e}")

            deleted_conversations.append({
                "title": conversation_title,
                "last_accessed": conversation.last_accessed_at.isoformat(),
                "size_bytes": conv_size
            })
            deleted_documents.extend(doc_info)
            space_recovered += conv_size

            # Check if we've freed enough space
            current_bytes -= conv_size
            if current_bytes <= CLEANUP_TARGET_BYTES:
                logger.info(f"Cleanup target reached: {current_bytes / (1024**3):.2f}GB")
                break

        self.db.commit()

        logger.info(
            f"Auto-cleanup completed for user {user_id}: "
            f"Deleted {len(deleted_conversations)} conversations, "
            f"freed {space_recovered / (1024**3):.2f}GB"
        )

        return {
            "deleted_conversations": deleted_conversations,
            "deleted_documents": deleted_documents,
            "space_recovered_bytes": space_recovered,
            "remaining_bytes": current_bytes,
            "message": (
                f"저장 공간 부족으로 30일 이상 사용하지 않은 항목을 자동으로 정리했습니다. "
                f"{len(deleted_conversations)}개의 대화와 {len(deleted_documents)}개의 문서가 삭제되었습니다. "
                f"확보된 공간: {space_recovered / (1024**3):.2f}GB"
            )
        }

    def update_conversation_storage_size(self, conversation_id: UUID) -> None:
        """
        Update storage_size_bytes for a conversation.

        Calculates total size from:
        - Message content (approximate: chars * 2 for UTF-8)
        - Uploaded documents (actual file sizes)
        """
        from app.models.message import Message

        conversation = self.db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conversation:
            return

        # Calculate message storage
        message_bytes = (
            self.db.query(func.coalesce(func.sum(func.length(Message.content) * 2), 0))
            .filter(Message.conversation_id == conversation_id)
            .scalar()
        ) or 0

        # Calculate document storage
        document_bytes = (
            self.db.query(func.coalesce(func.sum(Document.file_size), 0))
            .filter(Document.conversation_id == conversation_id)
            .scalar()
        ) or 0

        total_bytes = message_bytes + document_bytes
        conversation.storage_size_bytes = total_bytes
        self.db.commit()

        logger.debug(f"Updated conversation {conversation_id} storage: {total_bytes} bytes")
