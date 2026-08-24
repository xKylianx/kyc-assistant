from __future__ import annotations

import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

from sqlalchemy.orm import Session

from src.db.models.uploaded_file import UploadedFile


# Keep the MVP contract aligned with the processing agents.
# XLSX can be enabled once active-line detection and analysis loading
# are fully format-aware.
ALLOWED_EXTENSIONS = {".csv"}
MAX_FILE_SIZE_MB = 1000


class StorageService:
    def __init__(self, base_dir: str = "data/uploads"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _validate_extension(self, filename: str) -> str:
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
            raise ValueError(
                f"Extension '{ext}' non supportée. Extensions autorisées: {allowed}"
            )
        return ext

    def _validate_size(self, size_bytes: int) -> None:
        max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
        if size_bytes > max_bytes:
            raise ValueError(
                f"Fichier trop volumineux (> {MAX_FILE_SIZE_MB} MB)."
            )

    def save_file(
        self,
        db: Session,
        original_filename: str,
        content: bytes,
        user_id: Optional[str] = None,
        thread_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not original_filename:
            raise ValueError("Filename is required")

        ext = self._validate_extension(original_filename)
        self._validate_size(len(content))

        file_id = str(uuid.uuid4())
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_name = Path(original_filename).stem.replace(" ", "_")
        stored_filename = f"{ts}_{file_id}_{safe_name}{ext}"
        stored_path = self.base_dir / stored_filename

        try:
            with stored_path.open("wb") as handle:
                handle.write(content)

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

        except Exception:
            db.rollback()
            if stored_path.exists():
                stored_path.unlink(missing_ok=True)
            raise

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
