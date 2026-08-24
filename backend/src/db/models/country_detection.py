from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class CountryDetection(Base):
    __tablename__ = "country_detections"

    file_id = Column(String, primary_key=True, index=True)
    
    # Résultats de détection
    detected_country = Column(String, nullable=False)
    country_detection_confidence = Column(Float, nullable=True)
    country_detection_reasoning = Column(Text, nullable=True)
    
    # Métadonnées
    country_detection_status = Column(String, nullable=False)  # completed, error
    country_detection_error = Column(Text, nullable=True)
    
    detected_at = Column(DateTime, default=datetime.utcnow, nullable=False)
