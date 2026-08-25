from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
import json

from src.db.models.analysis_result import AnalysisResult
from src.db.models.uploaded_file import UploadedFile
from src.db.models.country_detection import CountryDetection


def upsert_analysis_results(
    db: Session,
    file_id: str,
    analysis_status: str,
    msisdn_analysis: Optional[Dict] = None,
    first_name_analysis: Optional[Dict] = None,
    last_name_analysis: Optional[Dict] = None,
    id_type_analysis: Optional[Dict] = None,
    id_number_analysis: Optional[Dict] = None,
    dob_analysis: Optional[Dict] = None,
    address_analysis: Optional[Dict] = None,
    city_analysis: Optional[Dict] = None,
    overall_risk_score: Optional[float] = None,
    overall_risk_level: Optional[str] = None,
    overall_compliance_rate: Optional[float] = None,
    active_rows_count: Optional[int] = None,                  # NOUVEAU
    anomalies: Optional[List[Dict]] = None,
    anomalies_by_field: Optional[Dict[str, Any]] = None,
    executive_summary: Optional[Dict[str, Any]] = None,
    analysis_error: Optional[str] = None,
) -> Dict[str, Any]:
    existing = db.query(AnalysisResult).filter(
        AnalysisResult.file_id == file_id
    ).first()

    if existing:
        existing.analysis_status = analysis_status
        existing.msisdn_analysis = msisdn_analysis
        existing.first_name_analysis = first_name_analysis
        existing.last_name_analysis = last_name_analysis
        existing.id_type_analysis = id_type_analysis
        existing.id_number_analysis = id_number_analysis
        existing.dob_analysis = dob_analysis
        existing.address_analysis = address_analysis
        existing.city_analysis = city_analysis
        existing.overall_risk_score = overall_risk_score
        existing.overall_risk_level = overall_risk_level
        existing.overall_compliance_rate = overall_compliance_rate
        existing.active_rows_count = active_rows_count
        existing.anomalies = anomalies
        existing.anomalies_by_field = anomalies_by_field
        existing.executive_summary = executive_summary
        existing.analysis_error = analysis_error
        db.merge(existing)
    else:
        new_result = AnalysisResult(
            file_id=file_id,
            analysis_status=analysis_status,
            msisdn_analysis=msisdn_analysis,
            first_name_analysis=first_name_analysis,
            last_name_analysis=last_name_analysis,
            id_type_analysis=id_type_analysis,
            id_number_analysis=id_number_analysis,
            dob_analysis=dob_analysis,
            address_analysis=address_analysis,
            city_analysis=city_analysis,
            overall_risk_score=overall_risk_score,
            overall_risk_level=overall_risk_level,
            overall_compliance_rate=overall_compliance_rate,
            active_rows_count=active_rows_count,
            anomalies=anomalies,
            anomalies_by_field=anomalies_by_field,
            executive_summary=executive_summary,
            analysis_error=analysis_error,
        )
        db.add(new_result)

    db.flush()
    return {"file_id": file_id, "status": "success"}

def get_analysis_result(db: Session, file_id: str) -> Optional[AnalysisResult]:
    """Récupère les résultats d'analyse pour un fichier."""
    return db.query(AnalysisResult).filter(
        AnalysisResult.file_id == file_id
    ).first()

def list_analysis_results(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    country: Optional[str] = None,
    sort: str = "desc",
) -> Dict[str, Any]:
    """
    Liste paginée des analyses complétées, avec le fichier et le pays associés.
    Filtrable par pays et triable par date (asc = pour tracer une tendance
    chronologique de l'amélioration du KYC, desc = historique le plus récent d'abord).
    """
    query = (
        db.query(AnalysisResult, UploadedFile, CountryDetection)
        .join(UploadedFile, UploadedFile.file_id == AnalysisResult.file_id)
        .outerjoin(CountryDetection, CountryDetection.file_id == AnalysisResult.file_id)
        .filter(AnalysisResult.analysis_status == "completed")
    )

    if country:
        query = query.filter(CountryDetection.detected_country == country)

    total = query.count()

    order_col = AnalysisResult.analyzed_at
    query = query.order_by(order_col.asc() if sort == "asc" else order_col.desc())

    page = max(page, 1)
    page_size = max(min(page_size, 100), 1)
    rows = query.offset((page - 1) * page_size).limit(page_size).all()

    analyses = []
    for analysis, uploaded_file, country_detection in rows:
        analyses.append({
            "id": analysis.file_id,
            "fileId": analysis.file_id,
            "fileName": uploaded_file.original_filename if uploaded_file else None,
            "fileType": (uploaded_file.extension.lstrip(".") if uploaded_file and uploaded_file.extension else None),
            "country": country_detection.detected_country if country_detection else None,
            "riskScore": analysis.overall_risk_score,
            "riskLevel": analysis.overall_risk_level,
            "complianceRate": analysis.overall_compliance_rate,
            "rowsAnalyzed": analysis.active_rows_count,
            "createdAt": analysis.analyzed_at.isoformat() if analysis.analyzed_at else None,
        })

    return {
        "analyses": analyses,
        "total": total,
        "page": page,
        "pageSize": page_size,
    }
