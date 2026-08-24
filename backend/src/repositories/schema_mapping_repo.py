from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.db.models.schema_mapping import SchemaMapping


def upsert_schema_mapping(
    db: Session,
    file_id: str,
    is_orange_money: bool,
    confidence_score: Optional[float],
    mapping_status: str,
    nom_column: Optional[str] = None,
    prenom_column: Optional[str] = None,
    msisdn_column: Optional[str] = None,
    dob_column: Optional[str] = None,
    id_type_column: Optional[str] = None,
    id_number_column: Optional[str] = None,
    status_column: Optional[str] = None,
    address_column: Optional[str] = None,
    city_column: Optional[str] = None,
    detection_error: Optional[str] = None,
    all_detected_columns: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Insère ou met à jour le mapping de schéma pour un fichier.
    """
    
    existing = db.query(SchemaMapping).filter(SchemaMapping.file_id == file_id).first()
    
    if existing:
        existing.is_orange_money = is_orange_money
        existing.confidence_score = confidence_score
        existing.nom_column = nom_column
        existing.prenom_column = prenom_column
        existing.msisdn_column = msisdn_column
        existing.dob_column = dob_column
        existing.id_type_column = id_type_column
        existing.id_number_column = id_number_column
        existing.status_column = status_column
        existing.address_column = address_column
        existing.city_column = city_column
        existing.mapping_status = mapping_status
        existing.detection_error = detection_error
        existing.all_detected_columns = all_detected_columns
        db.merge(existing)
    else:
        new_mapping = SchemaMapping(
            file_id=file_id,
            is_orange_money=is_orange_money,
            confidence_score=confidence_score,
            nom_column=nom_column,
            prenom_column=prenom_column,
            msisdn_column=msisdn_column,
            dob_column=dob_column,
            id_type_column=id_type_column,
            id_number_column=id_number_column,
            status_column=status_column,
            address_column=address_column,
            city_column=city_column,
            mapping_status=mapping_status,
            detection_error=detection_error,
            all_detected_columns=all_detected_columns,
        )
        db.add(new_mapping)
    
    db.flush()
    return {"file_id": file_id, "status": "success"}
