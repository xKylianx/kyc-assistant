from __future__ import annotations

import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, BinaryIO

from sqlalchemy.orm import Session

from src.db.models.uploaded_file import UploadedFile

ALLOWED_EXTENSIONS = {".csv"}
MAX_FILE_SIZE_MB = 1000
UPLOAD_CHUNK_SIZE = 8 * 1024 * 1024  # 8 MiB


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
        #MAX size = 2GO
        max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024 * 2
        if size_bytes > max_bytes:
            raise ValueError(
                f"Fichier trop volumineux (> {MAX_FILE_SIZE_MB} MB)."
            )

    def _new_storage_target(self, original_filename: str) -> tuple[str, str, Path]:
        ext = self._validate_extension(original_filename)
        file_id = str(uuid.uuid4())
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_name = Path(original_filename).stem.replace(" ", "_")
        stored_filename = f"{ts}_{file_id}_{safe_name}{ext}"
        return file_id, ext, self.base_dir / stored_filename

    def _persist_metadata(
        self,
        db: Session,
        *,
        file_id: str,
        user_id: Optional[str],
        thread_id: Optional[str],
        original_filename: str,
        stored_filename: str,
        stored_path: Path,
        extension: str,
        size_bytes: int,
    ) -> Dict[str, Any]:
        row = UploadedFile(
            file_id=file_id,
            user_id=user_id,
            thread_id=thread_id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            file_path=str(stored_path.resolve()),
            extension=extension,
            size_bytes=size_bytes,
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

    def save_upload_stream(
        self,
        db: Session,
        *,
        original_filename: str,
        stream: BinaryIO,
        user_id: Optional[str] = None,
        thread_id: Optional[str] = None,
        chunk_size: int = UPLOAD_CHUNK_SIZE,
    ) -> Dict[str, Any]:
        """
        Persist an upload incrementally.

        The complete file is never materialized as a bytes object in RAM.
        A hard size limit is enforced while writing the stream.
        """
        if not original_filename:
            raise ValueError("Filename is required")

        file_id, ext, stored_path = self._new_storage_target(original_filename)
        stored_filename = stored_path.name
        max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
        total_size = 0

        try:
            with stored_path.open("wb") as handle:
                while True:
                    chunk = stream.read(chunk_size)
                    if not chunk:
                        break

                    total_size += len(chunk)
                    if total_size > max_bytes:
                        raise ValueError(
                            f"Fichier trop volumineux (> {MAX_FILE_SIZE_MB} MB)."
                        )

                    handle.write(chunk)

            return self._persist_metadata(
                db,
                file_id=file_id,
                user_id=user_id,
                thread_id=thread_id,
                original_filename=original_filename,
                stored_filename=stored_filename,
                stored_path=stored_path,
                extension=ext,
                size_bytes=total_size,
            )

        except Exception:
            db.rollback()
            stored_path.unlink(missing_ok=True)
            raise

    def save_file(
        self,
        db: Session,
        original_filename: str,
        content: bytes,
        user_id: Optional[str] = None,
        thread_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Backward-compatible API for small in-memory callers."""
        self._validate_size(len(content))
        from io import BytesIO

        return self.save_upload_stream(
            db,
            original_filename=original_filename,
            stream=BytesIO(content),
            user_id=user_id,
            thread_id=thread_id,
        )


storage_service = StorageService()
