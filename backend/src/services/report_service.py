from __future__ import annotations

import io
from typing import Dict, Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.db.models.uploaded_file import UploadedFile
from src.db.models.country_detection import CountryDetection
from src.db.models.schema_mapping import SchemaMapping
from src.repositories.analysis_result_repo import get_analysis_result

# Le backend produit des sévérités "low"/"medium"/"high" (data_analysis_nodes.py),
# le frontend attend "info"/"warning"/"error" (types/analysis.ts). On mappe ici
# pour ne pas avoir à dupliquer cette logique côté client.
SEVERITY_MAP = {"low": "info", "medium": "warning", "high": "error"}


def build_report(db: Session, file_id: str) -> Dict[str, Any]:
    analysis = get_analysis_result(db, file_id)
    if not analysis or analysis.analysis_status != "completed":
        raise HTTPException(
            status_code=404,
            detail=f"Aucune analyse complétée trouvée pour le fichier {file_id}",
        )

    uploaded_file = db.query(UploadedFile).filter(
        UploadedFile.file_id == file_id
    ).first()
    country_detection = db.query(CountryDetection).filter(
        CountryDetection.file_id == file_id
    ).first()
    schema_mapping = db.query(SchemaMapping).filter(
        SchemaMapping.file_id == file_id
    ).first()

    anomalies_by_field = analysis.anomalies_by_field or {}

    flattened_anomalies = []
    for field, field_anomalies in anomalies_by_field.items():
        for a in field_anomalies or []:
            flattened_anomalies.append({
                "field": field,
                "type": a.get("type"),
                "count": a.get("count", 0),
                "percentage": a.get("percentage", 0),
                "severity": SEVERITY_MAP.get(a.get("severity"), "info"),
            })

    critical_count = sum(1 for a in flattened_anomalies if a["severity"] == "error")
    warning_count = sum(1 for a in flattened_anomalies if a["severity"] == "warning")
    info_count = sum(1 for a in flattened_anomalies if a["severity"] == "info")
    # Approximation : pas de granularité "ligne" côté backend actuellement,
    # on additionne les enregistrements concernés par chaque anomalie détectée.
    affected_rows = sum(a["count"] for a in flattened_anomalies)

    return {
        "file_id": file_id,
        "file_name": uploaded_file.original_filename if uploaded_file else None,
        "detected_country": country_detection.detected_country if country_detection else None,
        "is_orange_money": schema_mapping.is_orange_money if schema_mapping else None,
        "analysis_status": analysis.analysis_status,
        "overall_risk_score": analysis.overall_risk_score,
        "overall_risk_level": analysis.overall_risk_level,
        "overall_compliance_rate": analysis.overall_compliance_rate,
        "executive_summary": analysis.executive_summary,
        "anomalies": flattened_anomalies,
        "summary": {
            "total_anomalies": len(flattened_anomalies),
            "critical_anomalies": critical_count,
            "warning_anomalies": warning_count,
            "info_anomalies": info_count,
            "affected_rows": affected_rows,
            "compliance_score": analysis.overall_compliance_rate,
        },
        "field_results": {
            "msisdn": analysis.msisdn_analysis,
            "first_name": analysis.first_name_analysis,
            "last_name": analysis.last_name_analysis,
            "id_type": analysis.id_type_analysis,
            "id_number": analysis.id_number_analysis,
            "dob": analysis.dob_analysis,
            "address": analysis.address_analysis,
            "city": analysis.city_analysis,
        },
        "analyzed_at": analysis.analyzed_at.isoformat() if analysis.analyzed_at else None,
    }


def render_report_pdf(report: Dict[str, Any]) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.pdfgen import canvas

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 2 * cm

    def line(text: str, size: int = 11, dy: float = 0.6 * cm, bold: bool = False):
        nonlocal y
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        c.drawString(2 * cm, y, text)
        y -= dy
        if y < 2 * cm:
            c.showPage()
            y = height - 2 * cm

    line("Rapport d'analyse KYC", size=16, bold=True, dy=1 * cm)
    line(f"Fichier : {report.get('file_name') or report['file_id']}")
    line(f"Pays détecté : {report.get('detected_country') or 'N/A'}")
    line(f"Score de risque global : {report.get('overall_risk_score')}")
    line(f"Niveau de risque : {report.get('overall_risk_level')}")
    line(f"Taux de conformité : {report.get('overall_compliance_rate')}%")
    line("")

    summary = report.get("summary", {})
    line("Résumé des anomalies", size=13, bold=True, dy=0.8 * cm)
    line(f"Total : {summary.get('total_anomalies', 0)}")
    line(f"Critiques : {summary.get('critical_anomalies', 0)}")
    line(f"Avertissements : {summary.get('warning_anomalies', 0)}")
    line(f"Infos : {summary.get('info_anomalies', 0)}")
    line("")

    line("Détail des anomalies", size=13, bold=True, dy=0.8 * cm)
    for a in report.get("anomalies", []):
        line(
            f"- [{a['severity'].upper()}] {a['field']} / {a['type']} "
            f"({a['count']} enregistrements, {a['percentage']}%)",
            size=10,
            dy=0.5 * cm,
        )

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()