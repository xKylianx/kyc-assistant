from __future__ import annotations

import uuid
from typing import Optional, Dict, Any

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.services.storage_service import storage_service

router = APIRouter(prefix="/files", tags=["files"])


@router.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    thread_id: Optional[str] = Form(default=None),
    user_id: Optional[str] = Form(default=None),
    db: Session = Depends(get_db),
):
    """
    Stores the uploaded file and returns the exact PrepState expected by
    POST /orchestrator/prep.

    For the current MVP, the file is read into memory before persistence.
    Chunked upload/storage should be added before exposing the 1 GB limit
    to production users.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="A filename is required")

    resolved_thread_id = thread_id or str(uuid.uuid4())

    try:
        # Stream UploadFile directly to disk. Do not call file.read():
        # that would materialize a potentially 1 GB upload in RAM.
        saved = storage_service.save_upload_stream(
            db=db,
            original_filename=file.filename,
            stream=file.file,
            user_id=user_id,
            thread_id=resolved_thread_id,
        )

        prep_state: Dict[str, Any] = {
            "thread_id": resolved_thread_id,
            "user_id": user_id,
            "file_id": saved["file_id"],
            "file_name": saved["file_name"],
            "file_path": saved["file_path"],
            "prep_status": "uploaded",
            "prep_error": None,
        }

        return {
            "status": "success",
            "file": saved,
            "prep_state": prep_state,
        }

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'upload du fichier: {exc}",
        ) from exc
