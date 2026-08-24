from datetime import datetime
from typing import Optional, Dict, Any
import duckdb
from sqlalchemy.orm import Session

from src.config.config import PrepAgentState
from src.nodes.ingestion_nodes import ORANGE_MONEY_SCHEMA


def detect_schema(
    db: Session,
    file_id: str,
    file_path: str,
    detected_delimiter: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Détecte si les données correspondent au schéma Orange Money.
    
    Si ce n'est pas Orange Money, retourne les colonnes détectées
    pour mapping manuel vers les champs KYC requis.
    
    Args:
        db: Session SQLAlchemy
        file_id: ID du fichier uploadé
        file_path: Chemin du fichier CSV
        detected_delimiter: Délimiteur détecté (';', ',', etc.)
    
    Returns:
        Dict avec résultats de détection
    """
    
    if not file_path:
        return {
            "schema_detection_status": "error",
            "is_orange_money": False,
            "schema_detection_error": "Missing file_path",
            "review_required": True,
        }
    
    con = None
    try:
        con = duckdb.connect()
        
        # Lire le fichier CSV
        delimiter = detected_delimiter or ","
        df = con.execute(
            f"""
            SELECT * FROM read_csv_auto('{file_path}', delim='{delimiter}', sample_size=20000)
            LIMIT 1
            """
        ).fetchdf()
        
        actual_columns = {col: "VARCHAR" for col in df.columns}
        actual_column_names = set(actual_columns.keys())
        
        required_columns = set(ORANGE_MONEY_SCHEMA.get("required_columns", []))
        expected_columns = set(ORANGE_MONEY_SCHEMA.get("expected_columns", []))
        expected_types = ORANGE_MONEY_SCHEMA.get("expected_types", {})
        
        # Vérifier les colonnes requises
        missing_required = required_columns - actual_column_names
        found_required = required_columns & actual_column_names
        found_expected = expected_columns & actual_column_names
        
        # Vérifier les types de données
        type_mismatches = []
        for col_name, expected_type in expected_types.items():
            if col_name in actual_columns:
                actual_type = actual_columns[col_name]
                if actual_type != expected_type:
                    type_mismatches.append({
                        "column": col_name,
                        "expected_type": expected_type,
                        "actual_type": actual_type,
                    })
        
        # Déterminer si c'est Orange Money
        is_orange_money = len(missing_required) == 0
        
        # Score de confiance
        total_expected = len(required_columns) + len(expected_columns)
        matched_columns = len(found_required) + len(found_expected)
        confidence_score = (matched_columns / total_expected) * 100 if total_expected > 0 else 0
        
        if type_mismatches:
            confidence_score *= (1 - (len(type_mismatches) / total_expected) * 0.1)
        
        result = {
            "file_id": file_id,
            "schema_detection_status": "completed",
            "is_orange_money": is_orange_money,
            "confidence_score": round(confidence_score, 2),
            "matched_required_columns": sorted(list(found_required)),
            "missing_required_columns": sorted(list(missing_required)),
            "matched_expected_columns": sorted(list(found_expected)),
            "unmatched_columns": sorted(list(
                actual_column_names - required_columns - expected_columns
            )),
            "type_mismatches": type_mismatches,
            "total_columns_found": len(actual_column_names),
            "total_columns_expected": total_expected,
            "all_detected_columns": sorted(list(actual_column_names)),
            "schema_detection_error": None,
            "review_required": False,
            "detected_at": datetime.utcnow().isoformat(),
        }
        
        print(f"✓ Orange Money Detection: {is_orange_money}")
        print(f"✓ Confidence Score: {confidence_score}%")
        print(f"✓ Required Columns Found: {len(found_required)}/{len(required_columns)}")
        
        # Si Orange Money, assigner les colonnes automatiquement
        if is_orange_money:
            result.update({
                "nom_column": "USER_LAST_NAME",
                "prenom_column": "USER_FIRST_NAME",
                "msisdn_column": "MSISDN",
                "dob_column": "DOB",
                "id_type_column": "ID_TYPE",
                "id_number_column": "ID_NO",
                "status_column": "ACCOUNT_STATUS",
                "address_column": "ADDRESS1",
                "city_column": "CITY",
                "mapping_status": "auto_detected",
            })
            print("✓ Orange Money columns automatically assigned")
        else:
            result.update({
                "mapping_status": "pending_user_input",
            })
            print("⚠ Manual column mapping required")
        
        return result
        
    except Exception as e:
        print(f"✗ Error during schema detection: {e}")
        import traceback
        traceback.print_exc()
        return {
            "file_id": file_id,
            "schema_detection_status": "error",
            "is_orange_money": False,
            "schema_detection_error": str(e),
            "review_required": True,
            "mapping_status": "error",
        }
    finally:
        if con:
            con.close()
