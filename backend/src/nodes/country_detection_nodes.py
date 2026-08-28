import json
import duckdb
import os
from dotenv import load_dotenv
from src.config.config import PrepAgentState
from langchain_openai import ChatOpenAI

# Load environment variables from .env file
load_dotenv()


# Initialize the LLM (adjust based on your setup)
model = ChatOpenAI(
     model= os.getenv("LLM_PROXY_MODEL"),  # Adjust based on your config
     api_key=os.getenv("OPENAI_API_KEY"),
     base_url = os.getenv("BASE_URL"),
)
def country_detector(state: PrepAgentState) -> PrepAgentState:
    """
    Detect the country associated with the dataset using LLM analysis.
    
    Always completes detection regardless of dataset type.
    
    Args:
        state: Current agent state containing file information
        
    Returns:
        Updated agent state with detected country and confidence score
    """
    print("=" * 60)
    print("🌍 COUNTRY DETECTION")
    print("=" * 60)

    try:
        file_path = state.get("file_path")
        file_name = state.get("file_name", "Unknown")
        csv_dialect = state.get("csv_dialect", {})
        schema_profile = state.get("schema_profile", {})
        
        if not file_path:
            print("✗ No file path provided for country detection")
            state["detected_country"] = "Unknown"
            state["country_detection_confidence"] = 0.0
            state["country_detection_error"] = "Missing file_path in state"
            state["country_detection_status"] = "error"
            return state
        
        print(f"📄 File: {file_name}")
        print(f"🔤 Delimiter: {csv_dialect.get('delimiter', 'unknown')}")
        
        # ====================================================================
        # STEP 1: USE LLM FOR OTHER DATASETS
        # ====================================================================
        
        print("\n🤖 Not Orange Money, using LLM for detection...")
        
        if not model:
            raise ValueError("LLM model not initialized")
        
        # Read a sample of the data
        con = None
        sample_data = []
        columns = []
        
        try:
            con = duckdb.connect()
            
            # Read first 10 rows for analysis
            delimiter = csv_dialect.get("delimiter", ",")
            query = f"""
                SELECT * FROM read_csv_auto('{file_path}', 
                    delim='{delimiter}',
                    sample_size=20000) 
                LIMIT 10
            """
            
            print(f"📖 Reading sample data...")
            df_sample = con.execute(query).fetchdf()
            
            # Convert all columns to string to ensure JSON serialization works
            df_sample = df_sample.astype(str)
            sample_data = df_sample.to_dict(orient='records')
            columns = df_sample.columns.tolist()
            
            print(f"✓ Sample records: {len(sample_data)}")
            print(f"✓ Columns analyzed: {len(columns)}")
            
        except Exception as e:
            print(f"⚠️ Error reading sample data: {e}")
            import traceback
            traceback.print_exc()
            sample_data = []
            columns = []
        finally:
            if con:
                con.close()
        
        # Build the prompt
        prompt = f"""You are a geospatial data analyst. Analyze this dataset and determine the country.

**File Name:** {file_name}
**Delimiter:** {csv_dialect.get('delimiter', 'unknown')}

**Column Names:**
{json.dumps(columns, indent=2)}

**Sample Data (first 10 rows):**
{json.dumps(sample_data, indent=2)}

**Analysis Criteria:**
1. Geographic indicators (country names, city names, regions)
2. Phone number formats (country codes, length patterns, prefixes)
3. ID patterns (national ID formats, passport formats unique to countries)
4. Address formats and postal systems
5. Currency codes or monetary amounts
6. Language patterns in text fields
7. Date formats
8. Domain names or email patterns
9. Specific business identifiers (operator names, regulatory bodies)

**Response Format:**
Provide your analysis in this exact format:
COUNTRY: [Country Name]
CONFIDENCE: [0.0-1.0]
REASONING: [Brief explanation of key indicators]

If you cannot determine the country with reasonable confidence, return:
COUNTRY: Unknown
CONFIDENCE: 0.0
REASONING: [Explanation of why determination was not possible]"""
        
        # Get LLM response
        print("\n🤖 Analyzing dataset with LLM...")
        response = model.invoke(prompt)
        response_text = response.content.strip()
        
        print(f"\n📋 LLM Response:\n{response_text}\n")
        
        # Parse response
        country = "Unknown"
        confidence = 0.0
        reasoning = ""
        
        for line in response_text.split('\n'):
            line = line.strip()
            if line.startswith('COUNTRY:'):
                country = line.replace('COUNTRY:', '').strip()
            elif line.startswith('CONFIDENCE:'):
                try:
                    confidence_str = line.replace('CONFIDENCE:', '').strip()
                    confidence = float(confidence_str)
                except ValueError:
                    confidence = 0.0
            elif line.startswith('REASONING:'):
                reasoning = line.replace('REASONING:', '').strip()
        
        print(f"✅ Detection Complete")
        print(f"  🌍 Country: {country}")
        print(f"  📊 Confidence: {confidence:.1%}")
        if reasoning:
            print(f"  💡 Reasoning: {reasoning}")
        
        # Update state
        state["detected_country"] = country
        state["country_detection_confidence"] = round(confidence, 2)
        state["country_detection_reasoning"] = reasoning
        state["country_detection_status"] = "completed"
        state["country_detection_error"] = None
        
        print("=" * 60)
        
        return state
        
    except Exception as e:
        print(f"❌ Error during country detection: {e}")
        import traceback
        traceback.print_exc()
        
        # Update state with error
        state["detected_country"] = "Unknown"
        state["country_detection_confidence"] = 0.0
        state["country_detection_error"] = str(e)
        state["country_detection_status"] = "error"
        
        print("=" * 60)
        
        return state
