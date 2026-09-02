import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

import duckdb
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from sqlalchemy.orm import Session

load_dotenv()

llm = ChatOpenAI(
    model=os.getenv("LLM_PROXY_MODEL"),
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("BASE_URL"),
)


def _read_csv_sql(file_path: str, delimiter: str) -> str:
    """
    Fragment SQL réutilisable pour lire le CSV avec tolérance aux lignes
    malformées (nombre de colonnes incohérent) — cohérent avec prep_agent.py
    et ChunkedColumn dans data_analysis_nodes.py.
    """
    return f"read_csv_auto('{file_path}', delim='{delimiter}', ignore_errors=true, null_padding=true)"


def detect_active_lines(
    db: Session,
    file_id: str,
    file_path: str,
    is_orange_money: bool,
    status_column: Optional[str] = None,
    detected_delimiter: Optional[str] = None,
) -> Dict[str, Any]:
    
    print("\n" + "=" * 60)
    print("🔥 FILTERING ACTIVE LINES")
    print("=" * 60)
    
    if not file_path:
        print("❌ No file path provided")
        return {
            "file_id": file_id,
            "total_lines_count": 0,
            "active_lines_count": 0,
            "active_lines_percentage": 0.0,
            "detection_status": "error",
            "detection_error": "Missing file_path",
            "detected_at": datetime.utcnow().isoformat(),
        }
    
    try:
        con = duckdb.connect()
        delimiter = detected_delimiter or ","
        relation = _read_csv_sql(file_path, delimiter)
        
        # STEP 1: Compter les lignes totales
        total_result = con.execute(
            f"SELECT COUNT(*) FROM {relation}"
        ).fetchall()
        
        total_rows = total_result[0][0] if total_result else 0
        print(f"✓ Total rows: {total_rows:,}")
        
        # STEP 2: Orange Money case
        if is_orange_money:
            print("\n🍊 Orange Money detected")
            print("✓ Using ACCOUNT_STATUS = 'Y' for active records")
            
            active_result = con.execute(
                f"SELECT COUNT(*) FROM {relation} WHERE ACCOUNT_STATUS = 'Y'"
            ).fetchall()
            
            active_rows = active_result[0][0] if active_result else 0
            
            result = {
                "file_id": file_id,
                "total_lines_count": total_rows,
                "active_lines_count": active_rows,
                "active_lines_percentage": round((active_rows / total_rows * 100) if total_rows > 0 else 0, 2),
                "active_status_column": "ACCOUNT_STATUS",
                "active_status_values": ["Y"],
                "active_lines_filter_method": "orange_money",
                "active_status_reasoning": "Orange Money schema uses ACCOUNT_STATUS = 'Y' for active records",
                "detection_status": "completed",
                "detection_error": None,
                "detected_at": datetime.utcnow().isoformat(),
            }
            
            print(f"✓ Active rows: {active_rows:,} ({result['active_lines_percentage']}%)")
            con.close()
            return result
        
        # STEP 3: Détecter la colonne de statut pour non-Orange Money
        print("\n🔍 Detecting status column...")
        
        df_header = con.execute(
            f"SELECT * FROM {relation} LIMIT 1"
        ).fetchdf()
        
        all_columns = df_header.columns.tolist()
        
        status_column_candidates = [
            "statut", "statut_in", "status", "state", "account_status",
            "customer_status", "subscription_status", "active", "is_active",
            "enabled", "disabled", "flag", "indicator"
        ]
        
        detected_status_column = status_column or None
        
        if not detected_status_column:
            for candidate in status_column_candidates:
                for col_name in all_columns:
                    if col_name.lower() == candidate.lower():
                        detected_status_column = col_name
                        print(f"✓ Found status column: '{detected_status_column}'")
                        break
                if detected_status_column:
                    break
        
        if not detected_status_column:
            print("⚠️ No status column detected - treating all records as active")
            result = {
                "file_id": file_id,
                "total_lines_count": total_rows,
                "active_lines_count": total_rows,
                "active_lines_percentage": 100.0,
                "active_status_column": None,
                "active_status_values": [],
                "active_lines_filter_method": "no_status_column",
                "active_status_reasoning": "No status column found - all records considered active",
                "detection_status": "completed",
                "detection_error": None,
                "detected_at": datetime.utcnow().isoformat(),
            }
            con.close()
            return result
        
        # STEP 4: Obtenir les valeurs uniques
        print(f"\n📊 Analyzing status column: '{detected_status_column}'")
        
        unique_values_result = con.execute(
            f'SELECT DISTINCT "{detected_status_column}" FROM {relation} ORDER BY "{detected_status_column}"'
        ).fetchall()
        
        unique_values = [str(row[0]) for row in unique_values_result if row[0] is not None]
        print(f"✓ Unique values: {unique_values}")
        
        # STEP 5: LLM pour déterminer les valeurs actives
        print(f"\n🤖 Using LLM to determine active status values...")
        
        active_values, reasoning = _detect_active_values_with_llm(
            status_column=detected_status_column,
            unique_values=unique_values
        )
        
        print(f"✓ LLM determined active values: {active_values}")
        print(f"✓ Reasoning: {reasoning}")
        
        # STEP 6: Compter les lignes actives
        if active_values:
            values_str = ", ".join([f"'{val}'" for val in active_values])
            where_clause = f'WHERE "{detected_status_column}" IN ({values_str})'
            
            active_result = con.execute(
                f"SELECT COUNT(*) FROM {relation} {where_clause}"
            ).fetchall()
            
            active_rows = active_result[0][0] if active_result else 0
            
            result = {
                "file_id": file_id,
                "total_lines_count": total_rows,
                "active_lines_count": active_rows,
                "active_lines_percentage": round((active_rows / total_rows * 100) if total_rows > 0 else 0, 2),
                "active_status_column": detected_status_column,
                "active_status_values": active_values,
                "active_lines_filter_method": "llm_identified",
                "active_status_reasoning": reasoning,
                "detection_status": "completed",
                "detection_error": None,
                "detected_at": datetime.utcnow().isoformat(),
            }
            
            print(f"\n✓ Active rows: {active_rows:,} ({result['active_lines_percentage']}%)")
        else:
            result = {
                "file_id": file_id,
                "total_lines_count": total_rows,
                "active_lines_count": total_rows,
                "active_lines_percentage": 100.0,
                "active_status_column": detected_status_column,
                "active_status_values": [],
                "active_lines_filter_method": "llm_failed",
                "active_status_reasoning": "LLM could not determine active status values",
                "detection_status": "completed",
                "detection_error": None,
                "detected_at": datetime.utcnow().isoformat(),
            }
            print("⚠️ LLM could not determine active values - treating all records as active")
        
        con.close()
        print("\n✅ Active Lines Detection Complete")
        print("=" * 60)
        
        return result
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        print("=" * 60)
        
        return {
            "file_id": file_id,
            "total_lines_count": 0,
            "active_lines_count": 0,
            "active_lines_percentage": 0.0,
            "detection_status": "error",
            "detection_error": str(e),
            "detected_at": datetime.utcnow().isoformat(),
        }


def _detect_active_values_with_llm(
    status_column: str,
    unique_values: list
) -> Tuple[list, str]:
    prompt = f"""You are a data analyst expert. Determine which status values represent "active" records.

Status Column Name: {status_column}
Unique Values: {unique_values}

Respond in JSON format:
{{
    "active_values": ["value1", "value2"],
    "reasoning": "Your explanation"
}}

If unsure, return empty active_values list."""
    
    try:
        response = llm.invoke(prompt)
        response_text = response.content
        
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start != -1 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            result = json.loads(json_str)
            
            return result.get("active_values", []), result.get("reasoning", "")
        else:
            return [], "Could not parse LLM response"
    
    except Exception as e:
        print(f"⚠️ LLM error: {str(e)}")
        return [], f"LLM error: {str(e)}"