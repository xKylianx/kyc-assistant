from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
import os

from src.db.models.uploaded_file import UploadedFile


def upsert_prep_metadata(
    db: Session,
    file_id: str,
    user_id: Optional[str],
    thread_id: Optional[str],
    original_filename: Optional[str],
    file_path: Optional[str],
    detected_delimiter: Optional[str],
    prep_engine: Optional[str],
    profiled_at: Optional[datetime] = None,
    status: str = "uploaded",
) -> Dict[str, Any]:
    row = db.query(UploadedFile).filter(UploadedFile.file_id == file_id).first()
    action = "updated"

    if row is None:
        safe_original = original_filename or "unknown.csv"
        name, ext = os.path.splitext(safe_original)

        size_bytes = 0
        if file_path and os.path.exists(file_path):
            size_bytes = os.path.getsize(file_path)
        row = UploadedFile(
            file_id=file_id,
            user_id=user_id,
            thread_id=thread_id,
            original_filename=original_filename,
            stored_filename=safe_original,
            file_path=file_path,
            extension=ext.lstrip(".").lower() if ext else "csv",
            size_bytes = size_bytes,
            status=status,
        )
        db.add(row)
        action = "inserted"
    else:
        # On complète les champs si absents côté DB
        row.user_id = row.user_id or user_id
        row.thread_id = row.thread_id or thread_id
        row.original_filename = row.original_filename or original_filename
        row.file_path = row.file_path or file_path
        row.status = status or row.status

    row.detected_delimiter = detected_delimiter
    row.prep_engine = prep_engine or "unknown"
    row.profiled_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(row)

    return {
        "file_id": row.file_id,
        "action": action,
        "prep_engine": row.prep_engine,
        "detected_delimiter": row.detected_delimiter,
        "profiled_at": row.profiled_at.isoformat() if row.profiled_at else None,
    }
