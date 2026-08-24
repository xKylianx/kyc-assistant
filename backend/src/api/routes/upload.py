from __future__ import annotations

from typing import Optional, Dict, Any
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.services.storage_service import storage_service

router = APIRouter(prefix="/files", tags=["files"])

@router.get("/health")
def health():
    return {"status": "Ok"}

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    thread_id: Optional[str] = Form(default=None),
    user_id: Optional[str] = Form(default=None),
    db : Session = Depends(get_db),
):
    try:
        content = await file.read()

        saved = storage_service.save_file(
            db=db,
            original_filename=file.filename,
            content=content,
            user_id=user_id,
            thread_id=thread_id,
        )

        prep_state: Dict[str, Any] = {
            "thread_id": thread_id,
            "user_id": user_id,
            "file_id": saved["file_id"],
            "file_name": saved["file_name"],
            "file_path": saved["file_path"],
            "prep_status": "uploaded",
            "prep_error": None,
        }

        return {"status": "success", "file" : saved, "prep_state": prep_state}
    
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'upload du fichier: {str(e)}")