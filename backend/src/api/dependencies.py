from __future__ import annotations

from typing import Generator
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os

load_dotenv()



from src.db.session import SessionLocal


def get_db() -> Generator[Session, None, None]:
    print("DATABASE_URL =", os.getenv("DATABASE_URL"))
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
