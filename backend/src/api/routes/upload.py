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
    try:
        # file.file est un SpooledTemporaryFile : lu par blocs directement,
        # jamais chargé entièrement en mémoire, quelle que soit la taille.
        saved = storage_service.save_upload_stream(
            db=db,
            original_filename=file.filename,
            stream=file.file,
            user_id=user_id,
            thread_id=thread_id,
        )

        resolved_thread_id = thread_id or str(uuid.uuid4())
        resolved_user_id = user_id or "anonymous"

        prep_state = {
            "thread_id": resolved_thread_id,
            "user_id": resolved_user_id,
            "file_id": saved["file_id"],
            "file_name": saved["file_name"],
            "file_path": saved["file_path"],
            "prep_status": "uploaded",
            "prep_error": None,
        }

        return {"status": "success", "file": saved, "prep_state": prep_state}

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'upload du fichier: {str(e)}")