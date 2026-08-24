from pathlib import Path
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.models.uploaded_file import Base, UploadedFile

# TODO: adaptez cet import à votre vrai repository
# ex: from src.repositories.uploaded_file_repository import upsert_prep_metadata
from src.repositories.uploaded_files_repo import upsert_prep_metadata


def test_upsert_prep_metadata_insert_then_update(tmp_path: Path):
    # DB de test isolée
    db_file = tmp_path / "repo_test.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    # Fichier réel pour size_bytes
    csv_file = tmp_path / "KYC_Postpaid_20250831.csv"
    csv_file.write_text("id;name\n1;alice\n", encoding="utf-8")

    db = SessionLocal()
    try:
        # INSERT
        upsert_prep_metadata(
            db=db,
            file_id="file-repo-001",
            user_id="user-repo-001",
            thread_id="thread-repo-001",
            original_filename=csv_file.name,
            file_path=str(csv_file),
            detected_delimiter=";",
            prep_engine="pandas",
            profiled_at=datetime.utcnow(),
            status="uploaded",
        )
        db.commit()

        row = db.query(UploadedFile).filter(UploadedFile.file_id == "file-repo-001").first()
        assert row is not None
        assert row.stored_filename is not None
        assert row.extension.lower() == "csv"
        assert row.size_bytes > 0
        assert row.detected_delimiter == ";"
        assert row.prep_engine == "pandas"
        assert row.profiled_at is not None

        # UPDATE (idempotence / maj)
        upsert_prep_metadata(
            db=db,
            file_id="file-repo-001",
            user_id="user-repo-001",
            thread_id="thread-repo-001",
            original_filename=csv_file.name,
            file_path=str(csv_file),
            detected_delimiter=",",
            prep_engine="pandas",
            profiled_at=datetime.utcnow(),
            status="processed",
        )
        db.commit()

        row2 = db.query(UploadedFile).filter(UploadedFile.file_id == "file-repo-001").first()
        assert row2 is not None
        assert row2.file_id == "file-repo-001"
        assert row2.detected_delimiter == ","
        assert row2.status in ("processed", "success", "uploaded")  # selon votre logique métier

    finally:
        db.close()
        engine.dispose()
