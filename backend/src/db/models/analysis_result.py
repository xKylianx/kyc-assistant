from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float, Text, JSON
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    file_id = Column(String, primary_key=True, index=True)
    
    # Métadonnées
    analysis_status = Column(String, nullable=False)  # completed, error, in_progress
    analysis_error = Column(Text, nullable=True)
    
    # Résultats par champ (JSON pour flexibilité)
    msisdn_analysis = Column(JSON, nullable=True)
    first_name_analysis = Column(JSON, nullable=True)
    last_name_analysis = Column(JSON, nullable=True)
    id_type_analysis = Column(JSON, nullable=True)
    id_number_analysis = Column(JSON, nullable=True)
    dob_analysis = Column(JSON, nullable=True)
    address_analysis = Column(JSON, nullable=True)
    city_analysis = Column(JSON, nullable=True)
    
    # Score global
    overall_risk_score = Column(Float, nullable=True)
    overall_risk_level = Column(String, nullable=True)  # low, medium, high, critical
    
    # Anomalies détectées
    anomalies = Column(JSON, nullable=True)  # List of detected anomalies
    
    # Timestamps
    analyzed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
