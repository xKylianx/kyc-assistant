from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float, Boolean, Text
from sqlalchemy.orm import declarative_base
from src.db.base import Base


class SchemaMapping(Base):
    __tablename__ = "schema_mappings"

    file_id = Column(String, primary_key=True, index=True)
    
    # Résultats de détection
    is_orange_money = Column(Boolean, nullable=False)
    confidence_score = Column(Float, nullable=True)
    
    # Colonnes détectées (JSON string ou colonnes individuelles)
    nom_column = Column(String, nullable=True)
    prenom_column = Column(String, nullable=True)
    msisdn_column = Column(String, nullable=True)
    dob_column = Column(String, nullable=True)
    id_type_column = Column(String, nullable=True)
    id_number_column = Column(String, nullable=True)
    status_column = Column(String, nullable=True)
    address_column = Column(String, nullable=True)
    city_column = Column(String, nullable=True)
    
    # Métadonnées
    mapping_status = Column(String, nullable=False)  # auto_detected, pending_user_input, validated, error
    detection_error = Column(Text, nullable=True)
    all_detected_columns = Column(Text, nullable=True)  # JSON string
    
    detected_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    validated_at = Column(DateTime, nullable=True)
