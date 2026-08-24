from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
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
) -> Dict[str, Any]:
    """Detect Orange Money schema and candidate KYC column mapping."""
    uploaded_file = _get_file(db, file_id)

    detection_result = detect_schema(
        db=db,
        file_id=file_id,
        file_path=uploaded_file.file_path,
        detected_delimiter=uploaded_file.detected_delimiter,
    )

    upsert_schema_mapping(
        db=db,
        file_id=file_id,
        is_orange_money=bool(detection_result.get("is_orange_money", False)),
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
        # JSON, not str(list), so the frontend/report can consume it safely.
        all_detected_columns=json.dumps(
            detection_result.get("all_detected_columns", []),
            ensure_ascii=False,
        ),
    )
    db.commit()

    return {
        "status": "ok",
        "file_id": file_id,
        **detection_result,
    }


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

    uploaded_file = _get_file(db, file_id)

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
        is_orange_money=bool(schema_mapping.is_orange_money),
        status_column=schema_mapping.status_column,
        detected_delimiter=uploaded_file.detected_delimiter,
    )

    upsert_active_lines_detection(
        db=db,
        file_id=file_id,
        total_lines_count=detection_result.get("total_lines_count", 0),
        active_lines_count=detection_result.get("active_lines_count", 0),
        active_lines_percentage=detection_result.get(
            "active_lines_percentage",
            0.0,
        ),
        active_status_column=detection_result.get("active_status_column"),
        active_status_values=detection_result.get("active_status_values"),
        active_lines_filter_method=detection_result.get(
            "active_lines_filter_method",
            "error",
        ),
        active_status_reasoning=detection_result.get(
            "active_status_reasoning"
        ),
        detection_status=detection_result.get(
            "detection_status",
            "error",
        ),
        detection_error=detection_result.get("detection_error"),
    )
    db.commit()

    return {
        "status": "ok",
        **detection_result,
    }


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
) -> Dict[str, Any]:
    """Run KYC analysis while keeping the dataset out of RAM."""
    from src.agents.analysis_agent import aggregate_analysis_results, run_analysis_agent
    from src.repositories.analysis_result_repo import upsert_analysis_results

    uploaded_file = _get_file(db, file_id)

    schema_mapping = (
        db.query(SchemaMapping).filter(SchemaMapping.file_id == file_id).first()
    )
    if not schema_mapping or schema_mapping.mapping_status != "validated":
        raise HTTPException(status_code=400, detail="Schema must be validated before analysis")

    country_detection = (
        db.query(CountryDetection).filter(CountryDetection.file_id == file_id).first()
    )
    if not country_detection or country_detection.country_detection_status != "validated":
        raise HTTPException(status_code=400, detail="Country must be validated before analysis")

    active_lines = (
        db.query(ActiveLinesDetection)
        .filter(ActiveLinesDetection.file_id == file_id)
        .first()
    )
    if not active_lines or active_lines.detection_status not in {"completed", "validated"}:
        raise HTTPException(status_code=400, detail="Active lines must be detected before analysis")

    initial_state = {
        "file_id": file_id,
        "thread_id": uploaded_file.thread_id or file_id,
        "data": [],
        "file_path": uploaded_file.file_path,
        "detected_delimiter": uploaded_file.detected_delimiter or ",",
        "country": country_detection.detected_country,
        "active_rows_count": int(active_lines.active_lines_count or 0),
        "active_status_column": active_lines.active_status_column,
        "active_status_values": active_lines.active_status_values or [],
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

    try:
        analysis_result = run_analysis_agent(
            initial_state=initial_state,
            thread_id=initial_state["thread_id"],
        )
        aggregated = aggregate_analysis_results(analysis_result)

        if aggregated.get("status") == "error":
            raise RuntimeError(aggregated.get("error", "Analysis agent failed"))

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
            overall_risk_score=aggregated.get("overall_risk_score", 0),
            overall_risk_level=aggregated.get("overall_risk_level", "UNKNOWN"),
            anomalies=aggregated.get("anomalies_by_field", {}),
        )
        db.commit()

        return {
            "status": "completed",
            "file_id": file_id,
            **aggregated,
            "detailed_results": {
                "msisdn": analysis_result.get("msisdn_analysis"),
                "first_name": analysis_result.get("first_name_analysis"),
                "last_name": analysis_result.get("last_name_analysis"),
                "id_type": analysis_result.get("id_type_analysis"),
                "id_number": analysis_result.get("id_number_analysis"),
                "dob": analysis_result.get("dob_analysis"),
                "address": analysis_result.get("address_analysis"),
                "city": analysis_result.get("city_analysis"),
            },
        }

    except Exception as exc:
        db.rollback()
        upsert_analysis_results(
            db=db,
            file_id=file_id,
            analysis_status="error",
            analysis_error=str(exc),
        )
        db.commit()
        raise HTTPException(status_code=500, detail=f"KYC analysis failed: {exc}") from exc


@router.get("/report/{file_id}", response_model=ReportResponse)
def get_report(
    file_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Build the report from persisted results.

    The frontend should call this endpoint instead of rebuilding a report
    from individual agent responses.
    """
    uploaded_file = _get_file(db, file_id)

    analysis = (
        db.query(AnalysisResult)
        .filter(AnalysisResult.file_id == file_id)
        .first()
    )
    if not analysis or analysis.analysis_status != "completed":
        raise HTTPException(
            status_code=400,
            detail="Analysis must be completed before generating the report",
        )

    schema_mapping = (
        db.query(SchemaMapping)
        .filter(SchemaMapping.file_id == file_id)
        .first()
    )
    country = (
        db.query(CountryDetection)
        .filter(CountryDetection.file_id == file_id)
        .first()
    )
    active_lines = (
        db.query(ActiveLinesDetection)
        .filter(ActiveLinesDetection.file_id == file_id)
        .first()
    )

    columns = []
    if schema_mapping and schema_mapping.all_detected_columns:
        try:
            columns = json.loads(schema_mapping.all_detected_columns)
        except (json.JSONDecodeError, TypeError):
            columns = [
                part.strip()
                for part in schema_mapping.all_detected_columns.strip("[]").split(",")
                if part.strip()
            ]

    detailed_results = {
        "msisdn": analysis.msisdn_analysis,
        "first_name": analysis.first_name_analysis,
        "last_name": analysis.last_name_analysis,
        "id_type": analysis.id_type_analysis,
        "id_number": analysis.id_number_analysis,
        "dob": analysis.dob_analysis,
        "address": analysis.address_analysis,
        "city": analysis.city_analysis,
    }

    executive_summary: Dict[str, Any] = {}
    for field_result in detailed_results.values():
        if isinstance(field_result, dict):
            summary = field_result.get("executive_summary")
            if isinstance(summary, dict):
                executive_summary.update(summary)

    total_rows = active_lines.total_lines_count if active_lines else 0
    active_rows = active_lines.active_lines_count if active_lines else 0

    completed_field_results = [
        value for value in detailed_results.values()
        if isinstance(value, dict) and value.get("status") == "completed"
    ]
    compliance_rates = [
        float(value["compliance_rate"])
        for value in completed_field_results
        if value.get("compliance_rate") is not None
    ]
    overall_compliance_rate = (
        round(sum(compliance_rates) / len(compliance_rates), 2)
        if compliance_rates
        else 0.0
    )
    total_anomalies = sum(
        len(items) for items in (analysis.anomalies or {}).values()
        if isinstance(items, list)
    )
    fields_analyzed = {
        "completed": len(completed_field_results),
        "total": len(detailed_results),
    }

    return {
        "file_id": file_id,
        "file_name": uploaded_file.original_filename,
        "file_size_bytes": uploaded_file.size_bytes,
        "extension": uploaded_file.extension,
        "delimiter": uploaded_file.detected_delimiter,
        "row_count": total_rows,
        "column_count": len(columns),
        "columns": columns,
        "schema": {
            "is_orange_money": (
                bool(schema_mapping.is_orange_money)
                if schema_mapping
                else False
            ),
            "confidence_score": (
                schema_mapping.confidence_score if schema_mapping else None
            ),
            "mapping_status": (
                schema_mapping.mapping_status if schema_mapping else "unknown"
            ),
            "mapping": {
                "nom": schema_mapping.nom_column if schema_mapping else None,
                "prenom": schema_mapping.prenom_column if schema_mapping else None,
                "msisdn": schema_mapping.msisdn_column if schema_mapping else None,
                "dob": schema_mapping.dob_column if schema_mapping else None,
                "id_type": schema_mapping.id_type_column if schema_mapping else None,
                "id_number": schema_mapping.id_number_column if schema_mapping else None,
                "status": schema_mapping.status_column if schema_mapping else None,
                "address": schema_mapping.address_column if schema_mapping else None,
                "city": schema_mapping.city_column if schema_mapping else None,
            },
        },
        "country": {
            "country": country.detected_country if country else None,
            "confidence": (
                country.country_detection_confidence if country else None
            ),
            "status": (
                country.country_detection_status if country else "unknown"
            ),
            "reasoning": (
                country.country_detection_reasoning if country else None
            ),
        },
        "active_lines": {
            "total_lines_count": total_rows,
            "active_lines_count": active_rows,
            "active_lines_percentage": (
                active_lines.active_lines_percentage if active_lines else 0
            ),
            "status_column": (
                active_lines.active_status_column if active_lines else None
            ),
            "status_values": (
                active_lines.active_status_values if active_lines else []
            ),
            "detection_status": (
                active_lines.detection_status if active_lines else "unknown"
            ),
        },
        "summary": {
            "overall_compliance_rate": overall_compliance_rate,
            "overall_risk_score": analysis.overall_risk_score or 0.0,
            "overall_risk_level": analysis.overall_risk_level or "UNKNOWN",
            "total_anomalies": total_anomalies,
            "active_rows_count": active_rows,
            "fields_analyzed": fields_analyzed,
        },
        "detailed_results": detailed_results,
        "anomalies": analysis.anomalies or {},
        "executive_summary": executive_summary,
    }


@router.get("/analyses")
def list_analyses(
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Return paginated analysis history for the dashboard."""
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)

    query = (
        db.query(UploadedFile, AnalysisResult, ActiveLinesDetection)
        .join(AnalysisResult, AnalysisResult.file_id == UploadedFile.file_id)
        .outerjoin(
            ActiveLinesDetection,
            ActiveLinesDetection.file_id == UploadedFile.file_id,
        )
        .filter(UploadedFile.deleted_at.is_(None))
        .order_by(AnalysisResult.analyzed_at.desc())
    )

    total = query.count()
    rows = query.offset((page - 1) * page_size).limit(page_size).all()

    analyses = []
    for uploaded_file, analysis, active_lines in rows:
        anomalies = analysis.anomalies or {}
        anomaly_count = sum(
            len(items) for items in anomalies.values()
            if isinstance(items, list)
        )
        analyses.append({
            "id": uploaded_file.file_id,
            "fileId": uploaded_file.file_id,
            "fileName": uploaded_file.original_filename,
            "fileType": uploaded_file.extension.lstrip(".").lower(),
            "fileSize": uploaded_file.size_bytes,
            "riskScore": float(analysis.overall_risk_score or 0),
            "riskLevel": (analysis.overall_risk_level or "UNKNOWN").upper(),
            "rowsAnalyzed": int(
                active_lines.active_lines_count
                if active_lines
                else 0
            ),
            "totalRows": int(
                active_lines.total_lines_count
                if active_lines
                else 0
            ),
            "anomalyCount": anomaly_count,
            "status": analysis.analysis_status,
            "createdAt": analysis.analyzed_at.isoformat() if analysis.analyzed_at else uploaded_file.created_at.isoformat(),
        })

    return {
        "status": "ok",
        "analyses": analyses,
        "page": page,
        "page_size": page_size,
        "total": total,
    }


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
