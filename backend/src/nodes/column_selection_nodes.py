import json
import duckdb
from src.config.config import PrepAgentState
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# Initialize the LLM (adjust based on your setup)
model = ChatOpenAI(
     model= "openai/gpt-5-chat",
     api_key=os.getenv("OPENAI_API_KEY"),
     base_url = os.getenv("BASE_URL"),
)



def select_columns_kyc(state: PrepAgentState) -> PrepAgentState:
    """
    Select only the relevant columns for KYC analysis from the dataset.
    
    Use the LLM to assist in identifying which columns are most relevant for KYC analysis 
    based on the dataset's schema and content. This step is crucial for focusing the analysis 
    on the most pertinent data and improving the efficiency of subsequent controls.
    
    If the dataset is not recognized as Orange Money, this function will be used to allow 
    human validation of the columns to be used in the KYC process. The LLM can provide 
    recommendations based on the column names and sample data, but the final selection 
    can be adjusted by a human reviewer if necessary.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated agent state with selected columns for KYC analysis
    """
    # print("=" * 60)
    # print("SELECTING COLUMNS FOR KYC ANALYSIS")
    # print("=" * 60)

    # Check if review is required for column selection
    # print(f"Review required for column selection: {state.get('review_required')}")

    # Only run this node if NOT Orange Money
    if state.get("is_orange_money", False):
        print("✓ Orange Money detected - skipping LLM column selection")

        #Define the columns relevant for KYC analysis based on the known schema of Orange Money datasets. These columns are predefined and do not require LLM analysis, as they are already known to be relevant for KYC processes.
        first_name_column = ["USER_FIRST_NAME"]
        last_name_column = ["USER_LAST_NAME"]
        msisdn_column = ["MSISDN"]
        status_column = ["ACCOUNT_STATUS"]
        dob_column = ["DOB"]
        adress_columns = ["ADDRESS1", "ADDRESS2"]
        city_column = ["CITY"]
        id_type_columns = ["ID_TYPE"]
        id_number_columns = ["ID_NUMBER"]

        # Update the state with the selected columns for KYC analysis and the reasoning for each selection. This information will be used in subsequent nodes for KYC analysis and validation.
        state.update({
            "first_name_column": first_name_column,
            "first_name_column_reasoning": "Predefined column for first name in Orange Money datasets",
            "last_name_column": last_name_column,
            "last_name_column_reasoning": "Predefined column for last name in Orange Money datasets",
            "msisdn_column": msisdn_column,
            "msisdn_column_reasoning": "Predefined column for MSISDN in Orange Money datasets",
            "status_column": status_column,
            "status_column_reasoning": "Predefined column for account status in Orange Money datasets",
            "dob_column": dob_column,
            "dob_column_reasoning": "Predefined column for date of birth in Orange Money datasets",
            "adress_columns": adress_columns,
            "adress_columns_reasoning": "Predefined columns for address in Orange Money datasets",
            "city_column": city_column,
            "city_column_reasoning": "Predefined column for city in Orange Money datasets",
            "id_type_columns": id_type_columns,
            "id_type_columns_reasoning": "Predefined columns for type of ID in Orange Money datasets",
            "id_number_columns": id_number_columns,
            "id_number_columns_reasoning": "Predefined columns for ID number in Orange Money datasets",
        })
        return {
            "column_selection_status": "skipped",
            "column_selection_error": None,
            "review_required": False,
        }
    
    
    else:
        # If not Orange Money, we can use the LLM to recommend columns based on the dataset's schema and content
        print("Dataset is not recognized as Orange Money. Using LLM to recommend columns for KYC analysis.")
        # For simplicity, we'll just return empty lists here, but in a real implementation, you would call the LLM to get recommendations based on the column names and sample data.
        first_name_column = []
        last_name_column = []
        msisdn_column = []
        status_column = []
        dob_column = []
        adress_columns = []
        city_column = []
        id_type_columns = []
        id_number_columns = []
        column_selection_details = {}

        required_fields = [
            "First Name",
            "Last Name",
            "MSISDN",
            "Status",
            "Date of Birth (DOB)",
            "Address",
            "City",
            "Type of ID",
            "ID Number",
            "Client ID"
        ]

        #Get the fist 10 rows of the dataset for the LLM to analyze and recommend columns for KYC analysis using duckdb for efficiency. We will read only the first 10 rows of the dataset to provide a sample for the LLM to analyze, which will help it make informed recommendations about which columns are most relevant for KYC analysis based on the actual data content and structure.
        sample_data = []
        con = duckdb.connect()
        try:
            query = f"""
                SELECT * FROM read_csv('{state.get("file_path")}', 
                    delim='{state.get("csv_dialect", {}).get("delimiter", ",")}',
                    header=true) 
                LIMIT 10
            """
            df_sample = con.execute(query).fetchdf()
            df_sample = df_sample.astype(str)  # Convert all data to string for JSON serialization
            sample_data = df_sample.to_dict(orient='records')
        except Exception as e:
            print(f"⚠ Error reading sample data for LLM analysis: {e}")
            import traceback
            traceback.print_exc()

        try:
            prompt = f"""You are a data analyst expert. Your task is to match the available columns in a dataset to KYC (Know Your Customer) required fields.

    Required KYC Fields:
    {json.dumps(required_fields, indent=2)}

    Available Columns in the Dataset:
    {json.dumps(state.get("columns", []), indent=2)}

    Sample Data:
    {json.dumps(sample_data, indent=2)}

    For each required KYC field, identify the most relevant column(s) from the available dataset columns. Provide your recommendations in the following format:
    Field: Name of the required KYC field (e.g., "First Name")
    Recommended Column(s): [List of recommended column names from the dataset that best match the required KYC field]
    Reasoning: Brief explanation of why the recommended column(s) are relevant for the required KYC field, based on the column names and sample data.

    That's the only format required in the response, do not provide any additional text or explanation outside of this format. Focus on identifying the best matching columns for each KYC field based on the column names and the sample data provided.
    If you cannot find a relevant column for a required KYC field, indicate that as well."""

            print("\nGetting column recommendations from LLM...")
            response = model.invoke(prompt)
            
            # ← CORRECTION : Extraire le contenu textuel de l'objet AIMessage
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            print(f"\nLLM Response:\n{response_text}")

            # Parse the LLM response to extract recommended columns and reasoning for each KYC field
            column_selection_details = {}
            current_field = None
            current_columns = []
            current_reasoning = ""
            
            # ← Utiliser response_text au lieu de response
            for line in response_text.split('\n'):
                line = line.strip()
                
                if line.startswith("Field:"):
                    # Save previous field if exists
                    if current_field:
                        column_selection_details[current_field] = {
                            "Recommanded_Columns": current_columns,
                            "Reasoning": current_reasoning
                        }
                    
                    current_field = line.replace("Field:", "").strip()
                    current_columns = []
                    current_reasoning = ""
                    
                elif line.startswith("Recommended Column(s):") and current_field:
                    columns_str = line.replace("Recommended Column(s):", "").strip()
                    # Remove brackets if present
                    columns_str = columns_str.strip("[]")
                    current_columns = [col.strip().strip("'\"") for col in columns_str.split(',') if col.strip()]
                    
                elif line.startswith("Reasoning:") and current_field:
                    current_reasoning = line.replace("Reasoning:", "").strip()
            
            # Don't forget the last field
            if current_field:
                column_selection_details[current_field] = {
                    "Recommanded_Columns": current_columns,
                    "Reasoning": current_reasoning
                }

            # Map the recommended columns to our KYC analysis variables
            first_name_column = column_selection_details.get("First Name", {}).get("Recommanded_Columns", [])
            last_name_column = column_selection_details.get("Last Name", {}).get("Recommanded_Columns", [])
            msisdn_column = column_selection_details.get("MSISDN", {}).get("Recommanded_Columns", [])
            status_column = column_selection_details.get("Status", {}).get("Recommanded_Columns", [])
            dob_column = column_selection_details.get("Date of Birth (DOB)", {}).get("Recommanded_Columns", [])
            adress_columns = column_selection_details.get("Address", {}).get("Recommanded_Columns", [])
            city_column = column_selection_details.get("City", {}).get("Recommanded_Columns", [])
            id_type_columns = column_selection_details.get("Type of ID", {}).get("Recommanded_Columns", [])
            id_number_columns = column_selection_details.get("ID Number", {}).get("Recommanded_Columns", [])

            # Print the details for verification
            print(f"\n{'='*60}")
            print("Recommended columns for KYC analysis based on LLM analysis:")
            print(f"{'='*60}")
            for field, details in column_selection_details.items():
                print(f"\n{field}:")
                print(f"  Recommanded_Columns: {details['Recommanded_Columns']}")
                print(f"  Reasoning: {details['Reasoning']}")

            #test
            print("First Name Columns:", first_name_column)
            print("Last Name Columns:", last_name_column)
            print("MSISDN Columns:", msisdn_column)
            print("Status Columns:", status_column)
            print("DOB Columns:", dob_column)
            print("Address Columns:", adress_columns)
            print("City Columns:", city_column)
            
            #update the state with the recommended columns and reasoning
            return state | {
                "first_name_columns": first_name_column,
                "first_name_columns_reasoning": column_selection_details.get("First Name", {}).get("Reasoning", ""),
                "last_name_columns": last_name_column,
                "last_name_columns_reasoning": column_selection_details.get("Last Name", {}).get("Reasoning", ""),
                "msisdn_columns": msisdn_column,
                "msisdn_columns_reasoning": column_selection_details.get("MSISDN", {}).get("Reasoning", ""),
                "status_columns": status_column,
                "status_columns_reasoning": column_selection_details.get("Status", {}).get("Reasoning", ""),
                "dob_columns": dob_column,
                "dob_columns_reasoning": column_selection_details.get("Date of Birth (DOB)", {}).get("Reasoning", ""),
                "address_columns": adress_columns,
                "address_columns_reasoning": column_selection_details.get("Address", {}).get("Reasoning", ""),
                "city_columns": city_column,
                "city_columns_reasoning": column_selection_details.get("City", {}).get("Reasoning", ""),
                "id_type_columns": id_type_columns,
                "id_type_columns_reasoning": column_selection_details.get("Type of ID", {}).get("Reasoning", ""),
                "id_number_columns": id_number_columns,
                "id_number_columns_reasoning": column_selection_details.get("ID Number", {}).get("Reasoning", ""),
                }  
                
        except Exception as e:
            print(f"✗ Error during LLM column recommendation: {e}")
            import traceback
            traceback.print_exc()
            first_name_column = []
            last_name_column = []
            msisdn_column = []
            status_column = []
            dob_column = []
            adress_columns = []
            city_column = []
            id_type_columns = []
            id_number_columns = []
            column_selection_details = {
                "Error": {
                    "Recommanded_Columns": [],
                    "Reasoning": "Error during LLM analysis - columns could not be recommended"
                }
            }


def _parse_llm_response(response_text: str) -> dict:
    """
    Parse the LLM response to extract recommended columns for each KYC field.
    Extracts the reasoning also
    
    Args:
        response_text: The raw text response from the LLM
    Returns:
        A dictionary mapping each KYC field to its recommended columns
    """
    recommended_columns = {}
    current_field = None

    for line in response_text.split('\n'):
        line = line.strip()
    
        if line.startswith("Field:"):
            current_field = line.replace("Field:", "").strip()
        
        elif line.startswith("Recommended Column(s):") and current_field:
            columns_str = line.replace("Recommended Column(s):", "").strip()
        
            # Remove brackets if present
            columns_str = columns_str.strip("[]")
        
            # Split by comma and clean up
            columns_list = [col.strip().strip("'\"") for col in columns_str.split(',') if col.strip()]
        
            recommended_columns[current_field] = columns_list

    return recommended_columns
