from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.api.main import app
from src.api.dependencies import get_db
from src.db.models.uploaded_file import Base as UploadedFileBase
from src.db.models.country_detection import Base as CountryDetectionBase
from src.repositories.uploaded_files_repo import upsert_prep_metadata


@pytest.fixture()
def test_db(tmp_path: Path):
    db_file = tmp_path / "country_test.db"
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    
    # Créer les tables
    UploadedFileBase.metadata.create_all(bind=engine)
    CountryDetectionBase.metadata.create_all(bind=engine)
    
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


def test_country_detect_morocco(client: TestClient, test_db, tmp_path: Path):
    """Test détection pays Maroc."""
    _, TestingSessionLocal = test_db
    
    # Créer un fichier CSV avec données marocaines
    csv_file = tmp_path / "morocco_data.csv"
    csv_file.write_text(
        "Nom;Prénom;MSISDN;Ville;ID Type\n"
        "Alaoui;Mohammed;+212612345678;Casablanca;CIN\n"
        "Bennani;Fatima;+212712345679;Rabat;Passport\n",
        encoding="utf-8"
    )
    
    db = TestingSessionLocal()
    try:
        # Insérer le fichier uploadé
        upsert_prep_metadata(
            db=db,
            file_id="file-country-001",
            user_id="user-001",
            thread_id="thread-001",
            original_filename=csv_file.name,
            file_path=str(csv_file),
            detected_delimiter=";",
            prep_engine="pandas",
            status="uploaded",
        )
        db.commit()
    finally:
        db.close()
    
    # Appeler l'endpoint
    resp = client.post("/orchestrator/country-detect?file_id=file-country-001")
    assert resp.status_code == 200
    
    body = resp.json()
    assert body["file_id"] == "file-country-001"
    assert "detected_country" in body
    assert "country_detection_confidence" in body
    assert body["country_detection_status"] in ("completed", "error")
