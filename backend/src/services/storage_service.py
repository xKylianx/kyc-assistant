from __future__ import annotations

import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

from sqlalchemy.orm import Session
from src.db.models.uploaded_file import UploadedFile

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".json"}
MAX_FILE_SIZE_MB = 1000


class StorageService:
    def __init__(self, base_dir: str = "data/uploads"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _validate_extension(self, filename: str) -> str:
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Extension '{ext}' non supportée. Autorisées: {ALLOWED_EXTENSIONS}")
        return ext

    def _validate_size(self, size_bytes: int):
        max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
        if size_bytes > max_bytes:
            raise ValueError(f"Fichier trop volumineux (> {MAX_FILE_SIZE_MB} MB).")

    def save_file(
        self,
        db: Session,
        original_filename: str,
        content: bytes,
        user_id: Optional[str] = None,
        thread_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        ext = self._validate_extension(original_filename)
        self._validate_size(len(content))

        file_id = str(uuid.uuid4())
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_name = Path(original_filename).stem.replace(" ", "_")
        stored_filename = f"{ts}_{file_id}_{safe_name}{ext}"
        stored_path = self.base_dir / stored_filename

        with open(stored_path, "wb") as f:
            f.write(content)

        row = UploadedFile(
            file_id=file_id,
            user_id=user_id,
            thread_id=thread_id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            file_path=str(stored_path.resolve()),
            extension=ext,
            size_bytes=len(content),
            status="active",
        )
        db.add(row)
        db.commit()
        db.refresh(row)

        return {
            "file_id": row.file_id,
            "file_name": row.original_filename,
            "stored_file_name": row.stored_filename,
            "file_path": row.file_path,
            "size_bytes": row.size_bytes,
            "extension": row.extension,
            "status": row.status,
            "created_at": row.created_at.isoformat(),
        }


storage_service = StorageService()
