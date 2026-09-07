from __future__ import annotations

from src.db.session import engine
from src.db.base import Base

# Import nécessaire pour enregistrer chaque table sur Base.metadata
from src.db.models import (  # noqa: F401
    uploaded_file,
    schema_mapping,
    country_detection,
    analysis_result,
    active_lines_detection,
)


def init_db():
    Base.metadata.create_all(bind=engine)