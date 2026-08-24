from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

# TODO: adaptez ces imports si chemins différents
from src.api.main import app
from src.api.dependencies import get_db
from src.db.models.uploaded_file import Base


@pytest.fixture()
def test_db(tmp_path: Path):
    db_file = tmp_path / "api_test.db"
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    yield engine, TestingSessionLocal
    engine.dispose()


@pytest.fixture()
def client(test_db):
    _, TestingSessionLocal = test_db

    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_orchestrator_prep_persists_metadata(client: TestClient, test_db, tmp_path: Path):
    engine, _ = test_db

    csv_file = tmp_path / "KYC_Postpaid_20250831.csv"
    csv_file.write_text("id;name\n1;alice\n2;bob\n", encoding="utf-8")

    payload = {
        "prep_state": {
            "thread_id": "thread-test-001",
            "user_id": "user-test-001",
            "file_id": "file-test-001",
            "file_name": csv_file.name,
            "file_path": str(csv_file),
            "prep_status": "uploaded",
            "prep_error": None,
        }
    }

    resp = client.post("/orchestrator/prep", json=payload)
    assert resp.status_code == 200, resp.text

    with engine.connect() as conn:
        row = conn.execute(
            text("""
                SELECT file_id, stored_filename, extension, size_bytes,
                       detected_delimiter, prep_engine, profiled_at
                FROM uploaded_files
                WHERE file_id = :file_id
            """),
            {"file_id": "file-test-001"},
        ).fetchone()

    assert row is not None
    assert row.file_id == "file-test-001"
    assert row.stored_filename is not None
    assert row.extension.lower() == "csv"
    assert row.size_bytes > 0
    assert row.prep_engine is not None
    assert row.profiled_at is not None
