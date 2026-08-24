from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    file_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=True, index=True)
    thread_id = Column(String, nullable=True, index=True)

    original_filename = Column(String, nullable=False)
    stored_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    extension = Column(String, nullable=False)
    size_bytes = Column(Integer, nullable=False)

    status = Column(String, nullable=False, default="active")  # e.g., active, processed, archived
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)  # For soft deletion

    detected_delimiter = Column(String, nullable=True)
    prep_engine = Column(String, nullable=True)
    profiled_at = Column(DateTime, nullable=True)