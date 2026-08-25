from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float, Text, JSON, Integer
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    file_id = Column(String, primary_key=True, index=True)

    analysis_status = Column(String, nullable=False)
    analysis_error = Column(Text, nullable=True)

    msisdn_analysis = Column(JSON, nullable=True)
    first_name_analysis = Column(JSON, nullable=True)
    last_name_analysis = Column(JSON, nullable=True)
    id_type_analysis = Column(JSON, nullable=True)
    id_number_analysis = Column(JSON, nullable=True)
    dob_analysis = Column(JSON, nullable=True)
    address_analysis = Column(JSON, nullable=True)
    city_analysis = Column(JSON, nullable=True)

    overall_risk_score = Column(Float, nullable=True)
    overall_risk_level = Column(String, nullable=True)
    overall_compliance_rate = Column(Float, nullable=True)          # NOUVEAU
    active_rows_count = Column(Integer, nullable=True)          # NOUVEAU

    anomalies = Column(JSON, nullable=True)
    anomalies_by_field = Column(JSON, nullable=True)                # NOUVEAU
    executive_summary = Column(JSON, nullable=True)                 # NOUVEAU

    analyzed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
