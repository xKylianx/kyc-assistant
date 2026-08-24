from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from src.db.models.active_lines_detection import ActiveLinesDetection


def upsert_active_lines_detection(
    db: Session,
    file_id: str,
    total_lines_count: int,
    active_lines_count: int,
    active_lines_percentage: float,
    active_status_column: Optional[str],
    active_status_values: Optional[List[str]],
    active_lines_filter_method: str,
    active_status_reasoning: Optional[str],
    detection_status: str,
    detection_error: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Insère ou met à jour la détection de lignes actives.
    """
    
    existing = db.query(ActiveLinesDetection).filter(
        ActiveLinesDetection.file_id == file_id
    ).first()
    
    if existing:
        existing.total_lines_count = total_lines_count
        existing.active_lines_count = active_lines_count
        existing.active_lines_percentage = active_lines_percentage
        existing.active_status_column = active_status_column
        existing.active_status_values = active_status_values
        existing.active_lines_filter_method = active_lines_filter_method
        existing.active_status_reasoning = active_status_reasoning
        existing.detection_status = detection_status
        existing.detection_error = detection_error
        db.merge(existing)
    else:
        new_detection = ActiveLinesDetection(
            file_id=file_id,
            total_lines_count=total_lines_count,
            active_lines_count=active_lines_count,
            active_lines_percentage=active_lines_percentage,
            active_status_column=active_status_column,
            active_status_values=active_status_values,
            active_lines_filter_method=active_lines_filter_method,
            active_status_reasoning=active_status_reasoning,
            detection_status=detection_status,
            detection_error=detection_error,
        )
        db.add(new_detection)
    
    db.flush()
    return {"file_id": file_id, "status": "success"}
