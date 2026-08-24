from src.config.config import PrepAgentState
import duckdb
import os

SUPPORTED_EXTENSIONS = {".csv", ".txt"}

ORANGE_MONEY_SCHEMA = {
    "required_columns": {
        "USER_ID",
        "MSISDN",
        "USER_FIRST_NAME",
        "USER_LAST_NAME",
        "ACCOUNT_STATUS",
        "CREATION_DATE",
    },
    "expected_columns": {
        "PROFILE_ID",
        "PARENT_USER_ID",
        "PARENT_USER_MSISDN",
        "USER_NAME_PREFIX",
        "USER_SHORT_NAME",
        "DOB",
        "REGISTERED_ON",
        "ADDRESS1",
        "ADDRESS2",
        "STATE",
        "CITY",
        "COUNTRY",
        "SSN",
        "DESIGNATION",
        "DIVISION",
        "CONTACT_PERSON",
        "CONTACT_NO",
        "EMPLOYEE_CODE",
        "SEX",
        "ID_NUMBER",
        "E_MAIL",
        "WEB_LOGIN",
        "CREATED_BY",
        "CREATED_BY_MSISDN",
        "NOMADE_CREATED_BY",
        "LEVEL1_APP_DATE",
        "LEVEL1_APP_BY",
        "LEVEL2_APP_DATE",
        "LEVEL2_APP_BY",
        "OWNER_ID",
        "OWNER_MSISDN",
        "USER_DOMAIN_CODE",
        "USER_CATEGORY_CODE",
        "USER_GRADE_NAME",
        "MODIFIED_BY",
        "MODIFIED_ON",
        "MODIFIED_APPROVED_BY",
        "MODIFIED_APPROVED_ON",
        "DELETED_ON",
        "DEACTIVATION_BY",
        "DEPARTMENT",
        "REGISTRATION_FORM_NUMBER",
        "REMARKS",
        "GEOGRAPHICAL_DOMAIN",
        "GROUP_ROLE",
        "FIRST_TRANSACTION_ON",
        "COMPANY_CODE",
        "USER_TYPE",
        "ACTION_TYPE",
        "AGENT_CODE",
        "CREATION_TYPE",
        "BULK_ID",
        "IDENTITY_PROOF_TYPE",
        "ADDRESS_PROOF_TYPE",
        "PHOTO_PROOF_TYPE",
        "ID_TYPE",
        "ID_NO",
        "ID_ISSUE_PLACE",
        "ID_ISSUE_DATE",
        "ID_ISSUE_COUNTRY",
        "ID_EXPIRY_DATE",
        "RESIDENCE_COUNTRY",
        "NATIONALITY",
        "EMPLOYER_NAME",
        "POSTAL_CODE",
        "SOUSCRIPTION_TYPE",
        "MOBILE_GROUP_ROLE",
    },
    "expected_types": {
        "USER_ID": "VARCHAR",
        "PROFILE_ID": "VARCHAR",
        "PARENT_USER_ID": "VARCHAR",
        "PARENT_USER_MSISDN": "BIGINT",
        "MSISDN": "BIGINT",
        "USER_NAME_PREFIX": "VARCHAR",
        "USER_FIRST_NAME": "VARCHAR",
        "USER_LAST_NAME": "VARCHAR",
        "USER_SHORT_NAME": "VARCHAR",
        "DOB": "DATE",
        "REGISTERED_ON": "TIMESTAMP",
        "ADDRESS1": "VARCHAR",
        "ADDRESS2": "VARCHAR",
        "STATE": "VARCHAR",
        "CITY": "VARCHAR",
        "COUNTRY": "VARCHAR",
        "SSN": "VARCHAR",
        "DESIGNATION": "VARCHAR",
        "DIVISION": "VARCHAR",
        "CONTACT_PERSON": "VARCHAR",
        "CONTACT_NO": "VARCHAR",
        "EMPLOYEE_CODE": "VARCHAR",
        "SEX": "VARCHAR",
        "ID_NUMBER": "VARCHAR",
        "E_MAIL": "VARCHAR",
        "WEB_LOGIN": "VARCHAR",
        "ACCOUNT_STATUS": "VARCHAR",
        "CREATION_DATE": "TIMESTAMP",
        "CREATED_BY": "VARCHAR",
        "CREATED_BY_MSISDN": "VARCHAR",
        "NOMADE_CREATED_BY": "BIGINT",
        "LEVEL1_APP_DATE": "VARCHAR",
        "LEVEL1_APP_BY": "VARCHAR",
        "LEVEL2_APP_DATE": "VARCHAR",
        "LEVEL2_APP_BY": "VARCHAR",
        "OWNER_ID": "VARCHAR",
        "OWNER_MSISDN": "BIGINT",
        "USER_DOMAIN_CODE": "VARCHAR",
        "USER_CATEGORY_CODE": "VARCHAR",
        "USER_GRADE_NAME": "VARCHAR",
        "MODIFIED_BY": "VARCHAR",
        "MODIFIED_ON": "TIMESTAMP",
        "MODIFIED_APPROVED_BY": "VARCHAR",
        "MODIFIED_APPROVED_ON": "VARCHAR",
        "DELETED_ON": "TIMESTAMP",
        "DEACTIVATION_BY": "VARCHAR",
        "DEPARTMENT": "VARCHAR",
        "REGISTRATION_FORM_NUMBER": "VARCHAR",
        "REMARKS": "VARCHAR",
        "GEOGRAPHICAL_DOMAIN": "VARCHAR",
        "GROUP_ROLE": "VARCHAR",
        "FIRST_TRANSACTION_ON": "VARCHAR",
        "COMPANY_CODE": "VARCHAR",
        "USER_TYPE": "VARCHAR",
        "ACTION_TYPE": "VARCHAR",
        "AGENT_CODE": "VARCHAR",
        "CREATION_TYPE": "VARCHAR",
        "BULK_ID": "VARCHAR",
        "IDENTITY_PROOF_TYPE": "VARCHAR",
        "ADDRESS_PROOF_TYPE": "VARCHAR",
        "PHOTO_PROOF_TYPE": "VARCHAR",
        "ID_TYPE": "VARCHAR",
        "ID_NO": "VARCHAR",
        "ID_ISSUE_PLACE": "VARCHAR",
        "ID_ISSUE_DATE": "DATE",
        "ID_ISSUE_COUNTRY": "VARCHAR",
        "ID_EXPIRY_DATE": "DATE",
        "RESIDENCE_COUNTRY": "VARCHAR",
        "NATIONALITY": "VARCHAR",
        "EMPLOYER_NAME": "VARCHAR",
        "POSTAL_CODE": "VARCHAR",
        "SOUSCRIPTION_TYPE": "VARCHAR",
        "MOBILE_GROUP_ROLE": "VARCHAR",
    },
}


def count_rows_duckdb(file_path: str, delimiter: str) -> int:
    """
    Count the number of rows in a file using DuckDB for efficiency.
    
    Args:
        file_path: Path to the CSV file
        delimiter: CSV delimiter character
        
    Returns:
        Number of rows in the file (excluding header)
    """
    con = duckdb.connect()
    try:
        result = con.execute(
            f"SELECT COUNT(*) AS line_count FROM read_csv_auto('{file_path}', delim='{delimiter}', sample_size=20000)"
        ).fetchone()
        return result[0] if result else 0
    except Exception as e:
        print(f"Error occurred while counting rows with DuckDB: {e}")
        return 0
    finally:
        con.close()

def ingest_data(state: PrepAgentState) -> PrepAgentState:
    """
    Node 1 - Data Ingestion Node.
    
    Reads data from the file path in the state and updates the state with 
    relevant information about the file and its contents.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated agent state with file information
    """
    
    con = None
    try:
        # Extract file_path from state
        file_path = state.get('file_path')
        
        if not file_path:
            return {
                "ingest_status": "failed",
                "ingest_error": "No file path provided in state"
            }
        
        # Extract file information
        file_name = os.path.basename(file_path)
        file_extension = os.path.splitext(file_name)[1].lower()
        file_size_bytes = os.path.getsize(file_path)

        # Check if the file extension is supported
        if file_extension not in SUPPORTED_EXTENSIONS:
            return {
                "ingest_status": "failed",
                "ingest_error": f"Unsupported file extension: {file_extension}"
            }

        # Detect the delimiter using duckdb's sniff_csv function
        con = duckdb.connect()
        
        # Read the first line to detect delimiter manually (more reliable)
        delimiter = _detect_delimiter_from_file(file_path)
        
        print(f"DEBUG - Detected delimiter: {repr(delimiter)}")
        
        # Sniff CSV dialect using DuckDB for efficiency
        sniff_result = con.execute(
            f"SELECT * FROM sniff_csv('{str(file_path)}', delim='{delimiter}', sample_size=20000)"
        ).fetchdf().to_dict(orient="records")
        
        if not sniff_result:
            return {
                "ingest_status": "failed",
                "ingest_error": "Could not detect CSV dialect"
            }
        
        sniff = sniff_result[0]
        
        print(f"DEBUG - sniff_csv result: {sniff}")
        
        # Count rows using DuckDB for efficiency
        row_count = count_rows_duckdb(file_path, delimiter)
        
        # Extract column information
        columns_info = sniff.get('Columns', [])
        columns_dict = {col['name']: col['type'] for col in columns_info}

        # Return updated state with file information
        return {
            "file_path": file_path,
            "file_name": file_name,
            "file_size_bytes": file_size_bytes,
            "file_extension": file_extension,
            "row_count": row_count,
            "ingest_status": "success",
            "ingest_error": None,
            "csv_dialect": {
                "delimiter": delimiter,
                "quotechar": _parse_quote_char(sniff.get('Quote', '"')),
                "escapechar": _parse_escape_char(sniff.get('Escape')),
                "doublequote": True,
                "skipinitialspace": False,
                "has_header": sniff.get('HasHeader', True),
                "new_line_delimiter": sniff.get('NewLineDelimiter', '\n'),
            },
            "schema_profile": columns_dict,  # Store column types for later use
        }

    except Exception as e:
        print(f"Error during data ingestion: {e}")
        import traceback
        traceback.print_exc()
        return {
            "ingest_status": "failed",
            "ingest_error": str(e)
        }
    
    finally:
        if con:
            con.close()


def _detect_delimiter_from_file(file_path: str) -> str:
    """
    Detect the delimiter by reading the first line of the file.
    
    This is more reliable than relying on sniff_csv() alone, especially
    when the file has a BOM character.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        The detected delimiter character
    """
    try:
        # Read the first line with UTF-8-sig encoding to handle BOM
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            first_line = f.readline().strip()
        
        print(f"DEBUG - First line: {repr(first_line[:100])}")
        
        # Common delimiters to check (in order of likelihood)
        common_delimiters = [';', ',', '\t', '|', ':']
        
        # Count occurrences of each delimiter
        delimiter_counts = {delim: first_line.count(delim) for delim in common_delimiters}
        
        print(f"DEBUG - Delimiter counts: {delimiter_counts}")
        
        # Return the delimiter with the highest count (excluding those with 0 count)
        valid_delimiters = {k: v for k, v in delimiter_counts.items() if v > 0}
        
        if valid_delimiters:
            detected = max(valid_delimiters, key=valid_delimiters.get)
            print(f"DEBUG - Selected delimiter: {repr(detected)}")
            return detected
        
        # Default to comma if no delimiter found
        return ','
        
    except Exception as e:
        print(f"Error detecting delimiter: {e}")
        return ','


def _parse_delimiter(delimiter_str: str) -> str:
    """
    Parse the delimiter string returned by DuckDB's sniff_csv.
    
    DuckDB returns delimiters as string representations like ';' or ','.
    This function extracts the actual character.
    
    Args:
        delimiter_str: Raw delimiter string from sniff_csv
        
    Returns:
        The actual delimiter character
    """
    if not delimiter_str:
        return ','
    
    # Remove quotes if present
    delimiter_str = delimiter_str.strip().strip("'\"")
    
    # Handle common escape sequences
    escape_sequences = {
        '\\t': '\t',
        '\\n': '\n',
        '\\r': '\r',
        '\\\\': '\\',
    }
    
    for escape, actual in escape_sequences.items():
        if delimiter_str == escape:
            return actual
    
    # Return the first character if it's a valid delimiter
    if delimiter_str and len(delimiter_str) > 0:
        return delimiter_str[0]
    
    return ','


def _parse_quote_char(quote_str: str) -> str:
    """
    Parse the quote character returned by DuckDB's sniff_csv.
    
    Args:
        quote_str: Raw quote string from sniff_csv
        
    Returns:
        The actual quote character or None
    """
    if not quote_str or quote_str == '(empty)':
        return '"'
    
    quote_str = quote_str.strip().strip("'\"")
    
    if quote_str and len(quote_str) > 0:
        return quote_str[0]
    
    return '"'


def _parse_escape_char(escape_str: str) -> str:
    """
    Parse the escape character returned by DuckDB's sniff_csv.
    
    Args:
        escape_str: Raw escape string from sniff_csv
        
    Returns:
        The actual escape character or None
    """
    if not escape_str or escape_str == '(empty)':
        return None
    
    escape_str = escape_str.strip().strip("'\"")
    
    if escape_str and len(escape_str) > 0:
        return escape_str[0]
    
    return None
