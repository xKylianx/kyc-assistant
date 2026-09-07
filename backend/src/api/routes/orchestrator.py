from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from src.services import report_service
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.api.core.exceptions import ValidationError, ProcessingError
from src.api.schemas.prep import PrepRequest
from src.api.schemas.report import ReportResponse
from src.services.orchestrator_service import orchestrator_service
from src.agents.schema_detection_agent import detect_schema
from src.repositories.schema_mapping_repo import upsert_schema_mapping
from src.db.models.uploaded_file import UploadedFile
from src.db.models.schema_mapping import SchemaMapping
from src.db.models.country_detection import CountryDetection
from src.db.models.active_lines_detection import ActiveLinesDetection
from src.db.models.analysis_result import AnalysisResult
from src.repositories.analysis_result_repo import upsert_analysis_results, list_analysis_results

router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])


def _get_file(db: Session, file_id: str) -> UploadedFile:
    uploaded_file = (
        db.query(UploadedFile)
        .filter(UploadedFile.file_id == file_id)
        .first()
    )
    if not uploaded_file:
        raise HTTPException(status_code=404, detail=f"File {file_id} not found")
    return uploaded_file


@router.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@router.post("/prep")
def run_prep(
    req: PrepRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Run the preparation agent and persist dataset metadata."""
    ps = req.prep_state

    if not ps.file_id or not ps.file_path:
        raise ValidationError(
            message="file_id and file_path are required",
            details={"file_id": ps.file_id, "file_path": ps.file_path},
        )

    try:
        result = orchestrator_service.run_prep(
            db=db,
            prep_state=ps.model_dump(),
        )

        if result.get("prep_status") == "error":
            raise ProcessingError(
                message="Preparation failed",
                details={
                    "file_id": ps.file_id,
                    "reason": result.get("prep_error"),
                },
            )

        return {
            "status": "ok",
            "data": {"prep_state": result},
            "meta": {"endpoint": "/orchestrator/prep"},
        }

    except (ValidationError, ProcessingError):
        raise
    except Exception as exc:
        raise ProcessingError(
            message="Failed to process prep",
            details={"file_id": ps.file_id, "reason": str(exc)},
        ) from exc


@router.post("/schema-detect")
def schema_detect(
    file_id: str,
    db: Session = Depends(get_db),
):
    """
    Détecte le schéma du fichier uploadé.
    Vérifie si c'est Orange Money ou mappe les colonnes KYC.
    """
    
    uploaded_file = db.query(UploadedFile).filter(
        UploadedFile.file_id == file_id
    ).first()
    
    if not uploaded_file:
        raise HTTPException(status_code=404, detail=f"File {file_id} not found")
    
    detection_result = detect_schema(
        db=db,
        file_id=file_id,
        file_path=uploaded_file.file_path,
        detected_delimiter=uploaded_file.detected_delimiter,
    )

    # Si pas Orange Money, propose un mapping via LLM plutôt que de laisser
    # l'utilisateur repartir de zéro avec des selects vides.
    if not detection_result.get("is_orange_money", False):
        from src.services.column_suggestion_service import suggest_column_mapping

        suggested = suggest_column_mapping(
            file_path=uploaded_file.file_path,
            delimiter=uploaded_file.detected_delimiter or ",",
            available_columns=detection_result.get("all_detected_columns", []),
        )
        detection_result.update(suggested["columns"])
        detection_result["column_suggestion_reasoning"] = suggested["reasoning"]

    upsert_schema_mapping(
        db=db,
        file_id=file_id,
        is_orange_money=detection_result.get("is_orange_money", False),
        confidence_score=detection_result.get("confidence_score"),
        mapping_status=detection_result.get("mapping_status", "error"),
        nom_column=detection_result.get("nom_column"),
        prenom_column=detection_result.get("prenom_column"),
        msisdn_column=detection_result.get("msisdn_column"),
        dob_column=detection_result.get("dob_column"),
        id_type_column=detection_result.get("id_type_column"),
        id_number_column=detection_result.get("id_number_column"),
        status_column=detection_result.get("status_column"),
        address_column=detection_result.get("address_column"),
        city_column=detection_result.get("city_column"),
        detection_error=detection_result.get("schema_detection_error"),
        all_detected_columns=str(detection_result.get("all_detected_columns")),
    )
    db.commit()
    
    return detection_result

@router.post("/validate-schema")
def validate_schema(
    file_id: str,
    nom_column: str,
    prenom_column: str,
    msisdn_column: str,
    dob_column: str,
    id_type_column: str,
    id_number_column: str,
    status_column: str,
    address_column: str,
    city_column: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Persist the human-confirmed KYC column mapping."""
    existing = (
        db.query(SchemaMapping)
        .filter(SchemaMapping.file_id == file_id)
        .first()
    )
    if not existing:
        raise HTTPException(
            status_code=400,
            detail="Schema must be detected before validation",
        )

    upsert_schema_mapping(
        db=db,
        file_id=file_id,
        # Preserve the agent's Orange Money detection.
        is_orange_money=bool(existing.is_orange_money),
        confidence_score=1.0,
        mapping_status="validated",
        nom_column=nom_column,
        prenom_column=prenom_column,
        msisdn_column=msisdn_column,
        dob_column=dob_column,
        id_type_column=id_type_column,
        id_number_column=id_number_column,
        status_column=status_column,
        address_column=address_column,
        city_column=city_column,
        all_detected_columns=existing.all_detected_columns,
        detection_error=None,
    )
    db.commit()

    return {
        "status": "schema_validated",
        "file_id": file_id,
        "mapping_status": "validated",
        "is_orange_money": bool(existing.is_orange_money),
    }

@router.post("/country-detect")
def country_detect(
    file_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Detect the country associated with the uploaded dataset."""
    from src.agents.country_detection_agent import detect_country
    from src.repositories.country_detection_repo import upsert_country_detection

    uploaded_file = _get_file(db, file_id)

    detection_result = detect_country(
        db=db,
        file_id=file_id,
        file_path=uploaded_file.file_path,
        file_name=uploaded_file.original_filename,
        detected_delimiter=uploaded_file.detected_delimiter,
    )

    upsert_country_detection(
        db=db,
        file_id=file_id,
        detected_country=detection_result.get("detected_country", "Unknown"),
        country_detection_confidence=detection_result.get(
            "country_detection_confidence"
        ),
        country_detection_status=detection_result.get(
            "country_detection_status",
            "error",
        ),
        country_detection_reasoning=detection_result.get(
            "country_detection_reasoning"
        ),
        country_detection_error=detection_result.get(
            "country_detection_error"
        ),
    )
    db.commit()

    return {
        "status": "ok",
        "file_id": file_id,
        **detection_result,
    }

@router.post("/validate-country")
def validate_country(
    file_id: str,
    country: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Persist the human-confirmed country."""
    from src.repositories.country_detection_repo import upsert_country_detection

    _get_file(db, file_id)

    country = country.strip()
    if not country:
        raise HTTPException(status_code=400, detail="Country cannot be empty")

    upsert_country_detection(
        db=db,
        file_id=file_id,
        detected_country=country,
        country_detection_confidence=1.0,
        country_detection_status="validated",
        country_detection_reasoning="User validated",
        country_detection_error=None,
    )
    db.commit()

    return {
        "status": "country_validated",
        "file_id": file_id,
        "country": country,
    }

@router.post("/active-lines-detect")
def active_lines_detect(
    file_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Detect which records are active before KYC analysis."""
    from src.agents.active_lines_detection_agent import detect_active_lines
    from src.repositories.active_lines_detection_repo import (
        upsert_active_lines_detection,
    )

    uploaded_file = db.query(UploadedFile).filter(
        UploadedFile.file_id == file_id
    ).first()

    if not uploaded_file:
        raise HTTPException(status_code=404, detail=f"File {file_id} not found")

    schema_mapping = (
        db.query(SchemaMapping)
        .filter(SchemaMapping.file_id == file_id)
        .first()
    )
    if not schema_mapping:
        raise HTTPException(
            status_code=400,
            detail="Schema must be detected first",
        )

    detection_result = detect_active_lines(
        db=db,
        file_id=file_id,
        file_path=uploaded_file.file_path,
        is_orange_money=schema_mapping.is_orange_money,
        status_column=schema_mapping.status_column,
        detected_delimiter=uploaded_file.detected_delimiter,
    )

    upsert_active_lines_detection(
        db=db,
        file_id=file_id,
        total_lines_count=detection_result.get("total_lines_count", 0),
        active_lines_count=detection_result.get("active_lines_count", 0),
        active_lines_percentage=detection_result.get("active_lines_percentage", 0.0),
        active_status_column=detection_result.get("active_status_column"),
        active_status_values=detection_result.get("active_status_values"),
        active_lines_filter_method=detection_result.get("active_lines_filter_method"),
        active_status_reasoning=detection_result.get("active_status_reasoning"),
        detection_status=detection_result.get("detection_status", "error"),
        detection_error=detection_result.get("detection_error"),
    )
    db.commit()

    # Empêche le frontend de continuer silencieusement vers l'analyse avec
    # des données vides quand la détection a réellement échoué.
    if detection_result.get("detection_status") == "error":
        raise HTTPException(
            status_code=422,
            detail=f"Active lines detection failed: {detection_result.get('detection_error')}",
        )

    return detection_result

@router.post("/validate-active-lines")
def validate_active_lines(
    file_id: str,
    active_status_column: Optional[str] = None,
    active_status_values: Optional[list[str]] = None,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Optionally override and validate the active-line detection."""
    detection = (
        db.query(ActiveLinesDetection)
        .filter(ActiveLinesDetection.file_id == file_id)
        .first()
    )
    if not detection:
        raise HTTPException(
            status_code=400,
            detail="Active lines must be detected before validation",
        )

    if active_status_column is not None:
        detection.active_status_column = active_status_column

    if active_status_values is not None:
        detection.active_status_values = active_status_values

    detection.detection_status = "validated"
    detection.validated_at = datetime.utcnow()
    db.commit()

    return {
        "status": "active_lines_validated",
        "file_id": file_id,
        "active_status_column": detection.active_status_column,
        "active_status_values": detection.active_status_values or [],
        "active_lines_count": detection.active_lines_count,
        "total_lines_count": detection.total_lines_count,
        "active_lines_percentage": detection.active_lines_percentage,
    }


@router.post("/analyze")
def analyze(
    file_id: str,
    db: Session = Depends(get_db),
):
    """
    Lance l'analyse KYC complète sur un fichier, en mode chunké (DuckDB lit
    directement le CSV sur disque, jamais chargé entièrement en mémoire).
    Adapté aux fichiers volumineux (testé conceptuellement jusqu'à plusieurs Go).
    """
    from src.agents.analysis_agent import run_analysis_agent, aggregate_analysis_results
    from src.repositories.analysis_result_repo import upsert_analysis_results
    from src.db.models.uploaded_file import UploadedFile
    from src.db.models.schema_mapping import SchemaMapping
    from src.db.models.country_detection import CountryDetection
    from src.db.models.active_lines_detection import ActiveLinesDetection

    uploaded_file = db.query(UploadedFile).filter(
        UploadedFile.file_id == file_id
    ).first()
    if not uploaded_file:
        raise HTTPException(status_code=404, detail=f"File {file_id} not found")

    schema_mapping = db.query(SchemaMapping).filter(
        SchemaMapping.file_id == file_id
    ).first()
    if not schema_mapping or schema_mapping.mapping_status != "validated":
        raise HTTPException(
            status_code=400,
            detail="Schema must be validated before analysis",
        )

    country_detection = db.query(CountryDetection).filter(
        CountryDetection.file_id == file_id
    ).first()
    if not country_detection or country_detection.country_detection_status not in ("validated", "completed"):
        raise HTTPException(
            status_code=400,
            detail="Country must be validated before analysis",
        )

    active_lines = db.query(ActiveLinesDetection).filter(
        ActiveLinesDetection.file_id == file_id
    ).first()
    if not active_lines:
        raise HTTPException(
            status_code=400,
            detail="Active lines must be detected before analysis",
        )

    # Aucune lecture pandas ici : file_path + delimiter suffisent, chaque
    # node d'analyse lit le fichier lui-même via DuckDB en streaming.
    initial_state = {
        "file_id": file_id,
        "thread_id": uploaded_file.thread_id,
        "data": [],  # volontairement vide : force le passage par ChunkedColumn
        "file_path": uploaded_file.file_path,
        "detected_delimiter": uploaded_file.detected_delimiter or ",",
        "active_status_column": active_lines.active_status_column,
        "active_status_values": active_lines.active_status_values,
        "country": country_detection.detected_country,
        "active_rows_count": active_lines.active_lines_count,
        "schema_mapping": {
            "nom_column": schema_mapping.nom_column,
            "prenom_column": schema_mapping.prenom_column,
            "msisdn_column": schema_mapping.msisdn_column,
            "dob_column": schema_mapping.dob_column,
            "id_type_column": schema_mapping.id_type_column,
            "id_number_column": schema_mapping.id_number_column,
            "status_column": schema_mapping.status_column,
            "address_column": schema_mapping.address_column,
            "city_column": schema_mapping.city_column,
        },
        "analysis_status": "in_progress",
    }

    analysis_result = run_analysis_agent(
        initial_state=initial_state,
        thread_id=uploaded_file.thread_id,
    )

    aggregated = aggregate_analysis_results(analysis_result)

    upsert_analysis_results(
        db=db,
        file_id=file_id,
        analysis_status="completed",
        msisdn_analysis=analysis_result.get("msisdn_analysis"),
        first_name_analysis=analysis_result.get("first_name_analysis"),
        last_name_analysis=analysis_result.get("last_name_analysis"),
        id_type_analysis=analysis_result.get("id_type_analysis"),
        id_number_analysis=analysis_result.get("id_number_analysis"),
        dob_analysis=analysis_result.get("dob_analysis"),
        address_analysis=analysis_result.get("address_analysis"),
        city_analysis=analysis_result.get("city_analysis"),
        overall_risk_score=aggregated["overall_risk_score"],
        overall_risk_level=aggregated["overall_risk_level"],
        overall_compliance_rate=aggregated.get("overall_compliance_rate"),
        active_rows_count=aggregated.get("active_rows_count") or active_lines.active_lines_count,
        anomalies=aggregated.get("critical_fields", []),
        anomalies_by_field=aggregated.get("anomalies_by_field", {}),
        executive_summary=aggregated.get("executive_summary", {}),
    )
    db.commit()

    return {
        "file_id": file_id,
        "analysis_status": "completed",
        **aggregated,
        "detailed_results": {
            "msisdn": analysis_result.get("msisdn_analysis"),
            "first_name": analysis_result.get("first_name_analysis"),
            "last_name": analysis_result.get("last_name_analysis"),
            "id_type": analysis_result.get("id_type_analysis"),
            "id_number": analysis_result.get("id_number_analysis"),
            "dob": analysis_result.get("dob_analysis"),
            "city": analysis_result.get("city_analysis"),
            "address": analysis_result.get("address_analysis"),
        },
    }

@router.get("/report/{file_id}")
def get_report(file_id: str, db: Session = Depends(get_db)):
    """
    Construit le rapport final KYC (agrège AnalysisResult + métadonnées fichier/pays).
    """
    return report_service.build_report(db, file_id)

@router.delete("/analyses/{analysis_id}")
def delete_analysis(
    analysis_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Soft-delete an analysis from the dashboard history."""
    uploaded_file = _get_file(db, analysis_id)
    if uploaded_file.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Analysis not found")

    uploaded_file.deleted_at = datetime.utcnow()
    uploaded_file.status = "archived"
    db.commit()

    return {
        "status": "deleted",
        "analysis_id": analysis_id,
    }


@router.get("/report/{file_id}/export/pdf")
def export_report_pdf(file_id: str, db: Session = Depends(get_db)):
    """
    Exporte le rapport KYC en PDF.
    """
    report = report_service.build_report(db, file_id)
    pdf_bytes = report_service.render_report_pdf(report)
    filename = f"kyc-report-{file_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

@router.get("/analyses")
def list_analyses(
    page: int = 1,
    page_size: int = 10,
    country: Optional[str] = None,
    sort: str = "desc",
    db: Session = Depends(get_db),
):
    """
    Historique paginé des analyses KYC complétées.

    - `country` : filtre sur le pays détecté (ex. "FR", "Madagascar") pour
      comparer l'évolution du niveau de conformité d'un pays donné dans le temps.
    - `sort` : "asc" pour une vue chronologique (tendance), "desc" (défaut)
      pour les analyses les plus récentes en premier.
    """
    if sort not in ("asc", "desc"):
        raise HTTPException(status_code=400, detail="sort doit être 'asc' ou 'desc'")

    return list_analysis_results(
        db=db,
        page=page,
        page_size=page_size,
        country=country,
        sort=sort,
    )