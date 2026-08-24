from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
import json

from src.db.models.analysis_result import AnalysisResult


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
    anomalies: Optional[List[Dict]] = None,
    analysis_error: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Insère ou met à jour les résultats d'analyse KYC.
    """
    
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
        existing.anomalies = anomalies
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
            anomalies=anomalies,
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
