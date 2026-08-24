from __future__ import annotations

from src.db.session import engine
from src.db.models.uploaded_file import Base


def init_db():
    Base.metadata.create_all(bind=engine)
