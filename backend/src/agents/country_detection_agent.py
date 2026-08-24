import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

import duckdb
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from sqlalchemy.orm import Session

load_dotenv()

# Initialize LLM
llm = ChatOpenAI(
    model="openai/gpt-5-chat",  # Ajustez selon votre config
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("BASE_URL"),
)


def detect_country(
    db: Session,
    file_id: str,
    file_path: str,
    file_name: str,
    detected_delimiter: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Détecte le pays associé au dataset en utilisant l'analyse LLM.
    
    Args:
        db: Session SQLAlchemy
        file_id: ID du fichier
        file_path: Chemin du fichier CSV
        file_name: Nom du fichier
        detected_delimiter: Délimiteur détecté
    
    Returns:
        Dict avec résultats de détection du pays
    """
    
    print("=" * 60)
    print("🌍 COUNTRY DETECTION")
    print("=" * 60)
    
    try:
        if not file_path:
            print("✗ No file path provided for country detection")
            return {
                "file_id": file_id,
                "detected_country": "Unknown",
                "country_detection_confidence": 0.0,
                "country_detection_error": "Missing file_path",
                "country_detection_status": "error",
                "detected_at": datetime.utcnow().isoformat(),
            }
        
        print(f"📄 File: {file_name}")
        print(f"🔤 Delimiter: {detected_delimiter or 'unknown'}")
        
        # Lire un échantillon des données
        con = None
        sample_data = []
        columns = []
        
        try:
            con = duckdb.connect()
            
            delimiter = detected_delimiter or ","
            query = f"""
                SELECT * FROM read_csv_auto('{file_path}', 
                    delim='{delimiter}',
                    sample_size=20000) 
                LIMIT 10
            """
            
            print(f"📖 Reading sample data...")
            df_sample = con.execute(query).fetchdf()
            
            # Convertir en string pour JSON serialization
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
        
        # Construire le prompt
        prompt = f"""You are a geospatial data analyst. Analyze this dataset and determine the country.

**File Name:** {file_name}
**Delimiter:** {detected_delimiter or 'unknown'}

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
        
        # Appeler le LLM
        print("\n🤖 Analyzing dataset with LLM...")
        response = llm.invoke(prompt)
        response_text = response.content.strip()
        
        print(f"\n📋 LLM Response:\n{response_text}\n")
        
        # Parser la réponse
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
        
        result = {
            "file_id": file_id,
            "detected_country": country,
            "country_detection_confidence": round(confidence, 2),
            "country_detection_reasoning": reasoning,
            "country_detection_status": "completed",
            "country_detection_error": None,
            "detected_at": datetime.utcnow().isoformat(),
        }
        
        print("=" * 60)
        return result
        
    except Exception as e:
        print(f"❌ Error during country detection: {e}")
        import traceback
        traceback.print_exc()
        
        print("=" * 60)
        
        return {
            "file_id": file_id,
            "detected_country": "Unknown",
            "country_detection_confidence": 0.0,
            "country_detection_error": str(e),
            "country_detection_status": "error",
            "detected_at": datetime.utcnow().isoformat(),
        }
