from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from src.db.models.country_detection import CountryDetection


def upsert_country_detection(
    db: Session,
    file_id: str,
    detected_country: str,
    country_detection_confidence: Optional[float],
    country_detection_status: str,
    country_detection_reasoning: Optional[str] = None,
    country_detection_error: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Insère ou met à jour la détection de pays pour un fichier.
    """
    
    existing = db.query(CountryDetection).filter(
        CountryDetection.file_id == file_id
    ).first()
    
    if existing:
        existing.detected_country = detected_country
        existing.country_detection_confidence = country_detection_confidence
        existing.country_detection_reasoning = country_detection_reasoning
        existing.country_detection_status = country_detection_status
        existing.country_detection_error = country_detection_error
        db.merge(existing)
    else:
        new_detection = CountryDetection(
            file_id=file_id,
            detected_country=detected_country,
            country_detection_confidence=country_detection_confidence,
            country_detection_reasoning=country_detection_reasoning,
            country_detection_status=country_detection_status,
            country_detection_error=country_detection_error,
        )
        db.add(new_detection)
    
    db.flush()
    return {"file_id": file_id, "status": "success"}
