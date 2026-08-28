from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import declarative_base
from src.db.base import Base


class ActiveLinesDetection(Base):
    __tablename__ = "active_lines_detections"

    file_id = Column(String, primary_key=True, index=True)

    total_lines_count = Column(Integer, nullable=False, default=0)
    active_lines_count = Column(Integer, nullable=False, default=0)
    active_lines_percentage = Column(Float, nullable=True)

    active_status_column = Column(String, nullable=True)
    active_status_values = Column(JSON, nullable=True)
    active_lines_filter_method = Column(
        String, nullable=False, default="error"
    )
    active_status_reasoning = Column(Text, nullable=True)

    # completed: agent finished; pending_validation: user confirmation needed;
    # validated: user confirmed; error: detection failed.
    detection_status = Column(
        String, nullable=False, default="pending_validation"
    )
    detection_error = Column(Text, nullable=True)

    detected_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    validated_at = Column(DateTime, nullable=True)
