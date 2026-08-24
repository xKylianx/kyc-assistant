from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float, Integer, Text, JSON
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class ActiveLinesDetection(Base):
    __tablename__ = "active_lines_detections"

    file_id = Column(String, primary_key=True, index=True)
    active_lines_count = Column(Integer, nullable=False)
    
    # Comptages
    total_lines_count = Column(Integer, nullable=False)
    active_lines_count = Column(Integer, nullable=False)
    active_lines_percentage = Column(Float, nullable=True)
    
    # Détection du statut
    active_status_column = Column(String, nullable=True)
    active_status_values = Column(JSON, nullable=True)  # List of values
    active_lines_filter_method = Column(String, nullable=False)  # orange_money, llm_identified, no_status_column, error
    active_status_reasoning = Column(Text, nullable=True)
    
    # Métadonnées
    detection_status = Column(String, nullable=False)  # completed, pending_validation, validated, error
    detection_error = Column(Text, nullable=True)
    
    detected_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    validated_at = Column(DateTime, nullable=True)
