from __future__ import annotations

from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.services.orchestrator_service import orchestrator_service
from src.agents.schema_detection_agent import detect_schema
from src.repositories.schema_mapping_repo import upsert_schema_mapping
from src.db.models.uploaded_file import UploadedFile

from src.api.schemas.prep import PrepRequest
from src.api.core.exceptions import ValidationError, ProcessingError

router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])


@router.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@router.post("/prep")
def run_prep(req: PrepRequest, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Lance le prep agent, enrichit le prep_state et persiste certaines métadonnées en base.
    Retourne un format de réponse standardisé.
    """
    ps = req.prep_state

    # Exemple de validation métier simple (en plus de Pydantic)
    if not ps.file_id or not ps.file_path:
        raise ValidationError(
            message="file_id and file_path are required",
            details={"file_id": ps.file_id, "file_path": ps.file_path},
        )

    try:
        result = orchestrator_service.run_prep(db=db, prep_state=ps.model_dump())

        return {
            "status": "ok",
            "data": {
                "prep_state": result
            },
            "meta": {
                "endpoint": "/orchestrator/prep"
            }
        }

    except ValidationError:
        # On laisse remonter tel quel pour le handler global
        raise
    except Exception as e:
        raise ProcessingError(
            message="Failed to process prep",
            details={"file_id": ps.file_id, "reason": str(e)},
        )

@router.post("/schema-detect")
def schema_detect(
    file_id: str,
    db: Session = Depends(get_db),
):
    """
    Détecte le schéma du fichier uploadé.
    Vérifie si c'est Orange Money ou mappe les colonnes KYC.
    """
    
    # Récupérer les métadonnées du fichier
    uploaded_file = db.query(UploadedFile).filter(
        UploadedFile.file_id == file_id
    ).first()
    
    if not uploaded_file:
        raise HTTPException(status_code=404, detail=f"File {file_id} not found")
    
    # Lancer la détection de schéma
    detection_result = detect_schema(
        db=db,
        file_id=file_id,
        file_path=uploaded_file.file_path,
        detected_delimiter=uploaded_file.detected_delimiter,
    )
    # Persister les résultats
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
):
    """
    Reçoit la validation humaine du mapping de schéma.
    """
    from src.repositories.schema_mapping_repo import upsert_schema_mapping
    
    # Mettre à jour avec les colonnes validées par l'utilisateur
    upsert_schema_mapping(
        db=db,
        file_id=file_id,
        is_orange_money=False,  # Ou détecté avant
        confidence_score=1.0,  # Validé manuellement
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
    )
    db.commit()
    
    return {"status": "schema_validated", "file_id": file_id}


@router.post("/country-detect")
def country_detect(
    file_id: str,
    db: Session = Depends(get_db),
):
    """
    Détecte le pays associé au fichier uploadé.
    Utilise l'analyse LLM pour identifier le pays basé sur les données.
    """
    from src.agents.country_detection_agent import detect_country
    from src.repositories.country_detection_repo import upsert_country_detection
    
    # Récupérer les métadonnées du fichier
    uploaded_file = db.query(UploadedFile).filter(
        UploadedFile.file_id == file_id
    ).first()
    
    if not uploaded_file:
        raise HTTPException(status_code=404, detail=f"File {file_id} not found")
    
    # Lancer la détection de pays
    detection_result = detect_country(
        db=db,
        file_id=file_id,
        file_path=uploaded_file.file_path,
        file_name=uploaded_file.original_filename,
        detected_delimiter=uploaded_file.detected_delimiter,
    )
    
    # Persister les résultats
    upsert_country_detection(
        db=db,
        file_id=file_id,
        detected_country=detection_result.get("detected_country", "Unknown"),
        country_detection_confidence=detection_result.get("country_detection_confidence"),
        country_detection_status=detection_result.get("country_detection_status", "error"),
        country_detection_reasoning=detection_result.get("country_detection_reasoning"),
        country_detection_error=detection_result.get("country_detection_error"),
    )
    db.commit()
    
    return detection_result

@router.post("/validate-country")
def validate_country(
    file_id: str,
    country: str,
    db: Session = Depends(get_db),
):
    """
    Reçoit la validation humaine du pays détecté.
    """
    from src.repositories.country_detection_repo import upsert_country_detection
    
    # Mettre à jour avec le pays validé par l'utilisateur
    upsert_country_detection(
        db=db,
        file_id=file_id,
        detected_country=country,
        country_detection_confidence=1.0,  # Validé manuellement
        country_detection_status="validated",
        country_detection_reasoning="User validated",
    )
    db.commit()
    
    return {"status": "country_validated", "file_id": file_id, "country": country}

@router.post("/analyze")
def analyze(
    file_id: str,
    db: Session = Depends(get_db),
):
    """
    Lance l'analyse KYC complète sur un fichier.
    
    Prérequis:
    - Fichier uploadé (/orchestrator/prep)
    - Schéma validé (/orchestrator/validate-schema)
    - Pays validé (/orchestrator/validate-country)
    """
    from src.agents.analysis_agent import run_analysis_agent, aggregate_analysis_results
    from src.repositories.analysis_result_repo import upsert_analysis_results
    from src.db.models.uploaded_file import UploadedFile
    from src.db.models.schema_mapping import SchemaMapping
    from src.db.models.country_detection import CountryDetection
    import pandas as pd
    
    # 1. Récupérer les métadonnées
    uploaded_file = db.query(UploadedFile).filter(
        UploadedFile.file_id == file_id
    ).first()
    
    if not uploaded_file:
        raise HTTPException(status_code=404, detail=f"File {file_id} not found")
    
    # 2. Récupérer le mapping de schéma validé
    schema_mapping = db.query(SchemaMapping).filter(
        SchemaMapping.file_id == file_id
    ).first()
    
    if not schema_mapping or schema_mapping.mapping_status != "validated":
        raise HTTPException(
            status_code=400, 
            detail="Schema must be validated before analysis"
        )
    
    # 3. Récupérer le pays validé
    country_detection = db.query(CountryDetection).filter(
        CountryDetection.file_id == file_id
    ).first()
    
    if not country_detection or country_detection.country_detection_status != "validated":
        raise HTTPException(
            status_code=400,
            detail="Country must be validated before analysis"
        )
    
    # 4. Charger les données
    try:
        delimiter = uploaded_file.detected_delimiter or ","
        df = pd.read_csv(uploaded_file.file_path, delimiter=delimiter)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")
    
    # 5. Préparer l'état initial pour l'agent
    initial_state = {
        "file_id": file_id,
        "data": df.to_dict(orient="records"),
        "country": country_detection.detected_country,
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
    
    # 6. Lancer l'agent d'analyse
    analysis_result = run_analysis_agent(
        initial_state=initial_state,
        thread_id=uploaded_file.thread_id,
    )
    
    # 7. Agréger les résultats
    aggregated = aggregate_analysis_results(analysis_result)
    
    # 8. Persister en DB
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
        anomalies=aggregated["anomalies"],
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
            "address": analysis_result.get("address_analysis"),
            "city": analysis_result.get("city_analysis"),
        }
    }

@router.post("/active-lines-detect")
def active_lines_detect(
    file_id: str,
    db: Session = Depends(get_db),
):
    """
    Détecte les lignes actives et identifie les valeurs de statut.
    
    Prérequis: /orchestrator/schema-detect
    """
    from src.agents.active_lines_detection_agent import detect_active_lines
    from src.repositories.active_lines_detection_repo import upsert_active_lines_detection
    from src.db.models.uploaded_file import UploadedFile
    from src.db.models.schema_mapping import SchemaMapping
    
    # Récupérer le fichier
    uploaded_file = db.query(UploadedFile).filter(
        UploadedFile.file_id == file_id
    ).first()
    
    if not uploaded_file:
        raise HTTPException(status_code=404, detail=f"File {file_id} not found")
    
    # Récupérer le schéma
    schema_mapping = db.query(SchemaMapping).filter(
        SchemaMapping.file_id == file_id
    ).first()
    
    if not schema_mapping:
        raise HTTPException(status_code=400, detail="Schema must be detected first")
    
    # Lancer la détection
    detection_result = detect_active_lines(
        db=db,
        file_id=file_id,
        file_path=uploaded_file.file_path,
        is_orange_money=schema_mapping.is_orange_money,
        status_column=schema_mapping.status_column,
        detected_delimiter=uploaded_file.detected_delimiter,
    )
    
    # Persister
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
    
    return detection_result

@router.post("/analyze")
def analyze(
    file_id: str,
    db: Session = Depends(get_db),
):
    """
    Lance l'analyse KYC complète sur un fichier.
    """
    from src.agents.analysis_agent import run_analysis_agent, aggregate_analysis_results
    from src.repositories.analysis_result_repo import upsert_analysis_results
    from src.db.models.uploaded_file import UploadedFile
    from src.db.models.schema_mapping import SchemaMapping
    from src.db.models.country_detection import CountryDetection
    from src.db.models.active_lines_detection import ActiveLinesDetection
    import pandas as pd
    
    # 1. Récupérer les métadonnées
    uploaded_file = db.query(UploadedFile).filter(
        UploadedFile.file_id == file_id
    ).first()
    
    if not uploaded_file:
        raise HTTPException(status_code=404, detail=f"File {file_id} not found")
    
    # 2. Récupérer le mapping de schéma validé
    schema_mapping = db.query(SchemaMapping).filter(
        SchemaMapping.file_id == file_id
    ).first()
    
    if not schema_mapping or schema_mapping.mapping_status != "validated":
        raise HTTPException(
            status_code=400, 
            detail="Schema must be validated before analysis"
        )
    
    # 3. Récupérer le pays validé
    country_detection = db.query(CountryDetection).filter(
        CountryDetection.file_id == file_id
    ).first()
    
    if not country_detection or country_detection.country_detection_status != "validated":
        raise HTTPException(
            status_code=400,
            detail="Country must be validated before analysis"
        )
    
    # 4. Récupérer la détection de lignes actives
    active_lines = db.query(ActiveLinesDetection).filter(
        ActiveLinesDetection.file_id == file_id
    ).first()
    
    if not active_lines:
        raise HTTPException(
            status_code=400,
            detail="Active lines must be detected before analysis"
        )
    
    # 5. Charger et filtrer les données
    try:
        delimiter = uploaded_file.detected_delimiter or ","
        df = pd.read_csv(uploaded_file.file_path, delimiter=delimiter)
        
        # Filtrer les lignes actives
        if active_lines.active_status_column and active_lines.active_status_values:
            status_col = active_lines.active_status_column
            status_vals = active_lines.active_status_values
            df = df[df[status_col].isin(status_vals)]
        
        data = df.to_dict(orient="records")
        active_rows_count = len(data)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")
    
    # 6. Préparer l'état initial
    initial_state = {
        "file_id": file_id,
        "thread_id": uploaded_file.thread_id,
        "data": data,
        "file_path": uploaded_file.file_path,
        "country": country_detection.detected_country,
        "active_rows_count": active_rows_count,
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
    
    # 7. Lancer l'agent d'analyse
    analysis_result = run_analysis_agent(
        initial_state=initial_state,
        thread_id=uploaded_file.thread_id,
    )
    
    # 8. Agréger les résultats
    aggregated = aggregate_analysis_results(analysis_result)
    
    # 9. Persister en DB
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
        anomalies=aggregated.get("critical_fields", []),
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
        }
    }
