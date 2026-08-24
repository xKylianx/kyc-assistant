import duckdb
from src.config.config import PrepAgentState
from src.nodes.ingestion_nodes import ORANGE_MONEY_SCHEMA

def detect_schema(state: PrepAgentState) -> PrepAgentState:
    """
    Detect if the data matches the Orange Money schema by analyzing columns and data types.
    
    If the database is not Orange Money, the result will go to the next function for manual validation.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated agent state with schema detection results
    """

    file_path = state.get("file_path")
    ingest_status = state.get("ingest_status")
    csv_dialect = state.get("csv_dialect")
    schema_profile = state.get("schema_profile", {})
    
    # Verify that the previous ingestion step was successful
    if ingest_status != "success":
        return {
            "schema_detection_status": "skipped",
            "is_orange_money": False,
            "schema_detection_error": "Previous ingestion step failed",
            "review_required": True,
        }
    
    if not file_path:
        return {
            "schema_detection_status": "error",
            "is_orange_money": False,
            "schema_detection_error": "Missing file_path in state",
            "review_required": True,
        }
    
    con = None
    try:
        con = duckdb.connect()
        
        # Get schema information from the ingestion step
        if schema_profile:
            # Use the schema profile from the ingestion step
            actual_columns = schema_profile
        else:
            # Fallback: read the file to get columns
            delimiter = csv_dialect.get("delimiter", ",") if csv_dialect else ","
            df = con.execute(
                f"""
                SELECT * FROM read_csv_auto('{file_path}', delim='{delimiter}', sample_size=20000)
                LIMIT 1
                """
            ).fetchdf()
            actual_columns = {col: "VARCHAR" for col in df.columns}
        
        actual_column_names = set(actual_columns.keys())
        required_columns = ORANGE_MONEY_SCHEMA["required_columns"]
        expected_columns = ORANGE_MONEY_SCHEMA["expected_columns"]
        expected_types = ORANGE_MONEY_SCHEMA["expected_types"]
        
        # Check required columns
        missing_required = required_columns - actual_column_names
        found_required = required_columns & actual_column_names
        found_expected = expected_columns & actual_column_names
        
        # Check data types
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
        
        # Determine if it's Orange Money
        is_orange_money = len(missing_required) == 0
        
        # Calculate confidence score
        total_expected = len(required_columns) + len(expected_columns)
        matched_columns = len(found_required) + len(found_expected)
        confidence_score = (matched_columns / total_expected) * 100 if total_expected > 0 else 0
        
        # Adjust score based on type mismatches
        if type_mismatches:
            confidence_score *= (1 - (len(type_mismatches) / total_expected) * 0.1)
        
        result = {
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
            "csv_dialect_info": {
                "delimiter": csv_dialect.get("delimiter") if csv_dialect else None,
                "has_header": csv_dialect.get("has_header") if csv_dialect else None,
            },
            "schema_detection_error": None,
            "review_required": False,
        }
        
        print(f"✓ Orange Money Detection: {is_orange_money}")
        print(f"✓ Confidence Score: {confidence_score}%")
        print(f"✓ Required Columns Found: {len(found_required)}/{len(required_columns)}")

        # If the dataset is Orange Money, update the state with the columns to be used in the KYC process
        # Otherwise, the columns will be selected in the next function with human validation
        if is_orange_money:
            result["first_name_columns"] = ["USER_FIRST_NAME"]
            result["last_name_columns"] = ["USER_LAST_NAME"]
            result["msisdn_columns"] = ["MSISDN"]
            result["id_type_columns"] = ["ID_TYPE"]
            result["id_number_columns"] = ["ID_NO"]
            result["status_columns"] = ["ACCOUNT_STATUS"]
            result["dob_columns"] = ["DOB"]
            result["address_columns"] = ["ADDRESS1", "ADDRESS2"]
            result["city_columns"] = ["CITY"]
            
            print("✓ Orange Money columns automatically assigned")
        else:
            print("⚠ Manual column validation required")
            pass

        return result
        
    except Exception as e:
        print(f"✗ Error during schema detection: {e}")
        import traceback
        traceback.print_exc()
        return {
            "schema_detection_status": "error",
            "is_orange_money": False,
            "schema_detection_error": str(e),
            "review_required": True,
        }
    finally:
        if con:
            con.close()

def validate_schema(state: PrepAgentState) -> PrepAgentState:
    """
    Human-in-the-loop validation node.
    
    This node allows users to manually select columns for KYC analysis
    when the schema is not Orange Money.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated agent state with user-selected columns
    """
    print("=" * 60)
    print("Schema Validation - Waiting for user input...")
    print("=" * 60)
    
    # This node will be handled by Streamlit UI
    # The actual validation happens in the Streamlit app
    
    return {
        "schema_validation_status": "pending_user_input",
        "schema_validation_error": None,
    }
