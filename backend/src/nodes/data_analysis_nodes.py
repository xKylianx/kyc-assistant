import json
import duckdb
from src.config.config import AnalysisAgentState
from langchain_openai import ChatOpenAI
import os
import pandas as pd
from collections import Counter
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

ANALYSIS_CHUNK_SIZE = 50_000


def _sql_ident(name: str) -> str:
    return '"' + str(name).replace('"', '""') + '"'


def _sql_literal(value: str) -> str:
    return "'" + str(value).replace("'", "''") + "'"


class ChunkedColumn:
    """
    Lazy column reader backed by DuckDB. Iteration fetches at most
    ANALYSIS_CHUNK_SIZE rows at a time, keeping large CSV analysis bounded
    in memory instead of calling fetchall().
    """

    def __init__(
        self,
        file_path: str,
        column: str,
        delimiter: str = ",",
        active_status_column: str | None = None,
        active_status_values: list | None = None,
        drop_nulls: bool = False,
        uppercase: bool = False,
        expected_length: int | None = None,
        chunk_size: int = ANALYSIS_CHUNK_SIZE,
    ):
        self.file_path = file_path
        self.column = column
        self.delimiter = delimiter or ","
        self.active_status_column = active_status_column
        self.active_status_values = active_status_values or []
        self.drop_nulls = drop_nulls
        self.uppercase = uppercase  # NOTE: manquait dans l'__init__ d'origine
        self.expected_length = expected_length
        self.chunk_size = chunk_size

    def _relation(self) -> str:
        path = str(self.file_path).replace("'", "''")
        delim = str(self.delimiter).replace("'", "''")
        # all_varchar=True est essentiel : sans lui, DuckDB détecte
        # automatiquement les colonnes qui ressemblent à des dates/nombres
        # (ex: dob au format ISO) et les caste en TIMESTAMP en interne,
        # ce qui reformate silencieusement la valeur avant même le CAST
        # explicite en VARCHAR — cassant toute détection de format côté Python.
        return (
            f"read_csv_auto({_sql_literal(path)}, delim={_sql_literal(delim)}, "
            f"header=True, all_varchar=True, ignore_errors=True)"
        )

    def _conditions(self) -> list[str]:
        conditions = []
        if self.active_status_column and self.active_status_values:
            values = ", ".join(_sql_literal(v) for v in self.active_status_values)
            conditions.append(f"{_sql_ident(self.active_status_column)} IN ({values})")
        if self.drop_nulls:
            conditions.append(f"{_sql_ident(self.column)} IS NOT NULL")
            conditions.append(
                f"TRIM(CAST({_sql_ident(self.column)} AS VARCHAR)) <> ''"
            )
        return conditions

    def _where_sql(self) -> str:
        conditions = self._conditions()
        if not conditions:
            return ""
        return " WHERE " + " AND ".join(conditions)

    def __iter__(self):
        con = duckdb.connect(database=":memory:")
        try:
            query = (
                f"SELECT CAST({_sql_ident(self.column)} AS VARCHAR) "
                f"FROM {self._relation()}{self._where_sql()}"
            )
            print(query)
            cursor = con.execute(query)
            while True:
                rows = cursor.fetchmany(self.chunk_size)
                if not rows:
                    break
                for (value,) in rows:
                    normalized = "" if value is None else str(value).strip()
                    yield normalized.upper() if self.uppercase else normalized
        finally:
            con.close()

    def __len__(self) -> int:
        if self.expected_length is not None and not self.drop_nulls:
            return self.expected_length

        con = duckdb.connect(database=":memory:")
        try:
            query = f"SELECT COUNT(*) FROM {self._relation()}{self._where_sql()}"
            print(query)
            return int(con.execute(query).fetchone()[0])
        finally:
            con.close()


# Initialize the LLM (adjust based on your setup)
model = ChatOpenAI(
     model= os.getenv("LLM_PROXY_MODEL"),  # Adjust based on your config
     api_key=os.getenv("OPENAI_API_KEY"),
     base_url = os.getenv("BASE_URL"),
)

model_5_1 = ChatOpenAI(
        model= os.getenv("LLM_PROXY_MODEL"),
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url = os.getenv("BASE_URL"),
)

def analyze_msisdn(state: AnalysisAgentState) -> AnalysisAgentState:
    """
    Analyse la colonne MSISDN pour format et validité.
    
    Utilise active_rows_count du state pour éviter les recalculs.
    TOUTES LES REQUÊTES S'EXÉCUTENT UNIQUEMENT SUR LES LIGNES ACTIVES.
    
    Args:
        state: AnalysisAgentState avec file_path, schema_mapping, country, active_rows_count
        
    Returns:
        État mis à jour avec résultats d'analyse MSISDN
    """
    
    print("\n" + "=" * 60)
    print("📱 ANALYZING MSISDN")
    print("=" * 60)

    
    # ✅ Récupérer active_rows_count depuis state
    active_rows_count = state.get("active_rows_count", 0)
    
    # Récupérer les colonnes MSISDN
    schema_mapping = state.get("schema_mapping", {})
    msisdn_column = schema_mapping.get("msisdn_column")
    
    if not msisdn_column:
        print("⚠️ No MSISDN column mapped - skipping analysis")
        state["msisdn_analysis"] = {
            "status": "skipped",
            "reason": "No MSISDN column mapped"
        }
        return state
    
    file_path = state.get("file_path")
    country = state.get("country", "Unknown")
    data = state.get("data", [])
    
    if not file_path and not data:
        print("❌ No file path or data provided")
        state["msisdn_analysis"] = {
            "status": "error",
            "error": "No file path or data provided"
        }
        return state
    
    try:
        con = duckdb.connect()
        
        print(f"📱 Analyzing MSISDN column: '{msisdn_column}'")
        print(f"🌍 Country: {country}")
        print(f"✓ Active rows: {active_rows_count:,}")
        
        if active_rows_count == 0:
            print("⚠️ No active records found")
            state["msisdn_analysis"] = {
                "status": "warning",
                "row_count": 0,
                "valid_count": 0,
                "compliance_rate": 0.0,
                "warning": "No active records found"
            }
            return state
        
        # ====================================================================
        # STEP 1: Extraire les valeurs MSISDN
        # ====================================================================
        
        print(f"\n📊 Extracting MSISDN values...")
        
        if data:
            # Données en mémoire
            msisdn_values = [
                str(record.get(msisdn_column, "")).strip()
                for record in data
                if record.get(msisdn_column)
            ]
        else:
            # Lire depuis fichier
            msisdn_values = ChunkedColumn(
                file_path, msisdn_column,
                delimiter=state.get("detected_delimiter") or ",",
                active_status_column=state.get("active_status_column"),
                active_status_values=state.get("active_status_values"),
                drop_nulls=True,
            )
        
        # Compter les valeurs null/vides
        null_count = active_rows_count - len(msisdn_values)
        non_null_count = len(msisdn_values)
        
        print(f"   ✓ Non-null values: {non_null_count:,}")
        print(f"   ✓ Null/empty values: {null_count:,}")
        
        if non_null_count == 0:
            print("⚠️ No non-null MSISDN values found")
            state["msisdn_analysis"] = {
                "status": "warning",
                "row_count": active_rows_count,
                "valid_count": 0,
                "compliance_rate": 0.0,
                "null_count": null_count,
                "warning": "No non-null MSISDN values found"
            }
            return state
        
        # ====================================================================
        # STEP 2: Déterminer la longueur attendue
        # ====================================================================
        
        print(f"\n📊 Determining expected MSISDN length...")
        
        # Calculer les longueurs
        lengths = [len(val) for val in msisdn_values]
        from collections import Counter
        length_counts = Counter(lengths)
        most_common_length = length_counts.most_common(1)[0][0]
        
        print(f"   ✓ Most common length: {most_common_length} digits")
        print(f"   ✓ Length distribution: {dict(length_counts)}")
        
        # ====================================================================
        # STEP 3: Valider le format
        # ====================================================================
        
        print(f"\n📊 Validating MSISDN format...")
        
        # Compter les valeurs numériques
        numeric_count = sum(1 for val in msisdn_values if val.isdigit())
        
        # Compter les valeurs avec la bonne longueur
        matching_length_count = sum(1 for val in msisdn_values if len(val) == most_common_length)
        
        # Valides = longueur correcte ET numériques
        valid_count = sum(
            1 for val in msisdn_values
            if len(val) == most_common_length and val.isdigit()
        )
        
        not_matching_length = non_null_count - matching_length_count
        not_numeric = non_null_count - numeric_count
        
        print(f"   ✓ Numeric-only: {numeric_count:,}")
        print(f"   ✓ Matching length: {matching_length_count:,}")
        print(f"   ✓ Valid (numeric + correct length): {valid_count:,}")
        
        # ====================================================================
        # STEP 4: Calculer le taux de conformité
        # ====================================================================
        
        if non_null_count > 0:
            compliance_rate = (valid_count / active_rows_count) * 100
        else:
            compliance_rate = 0.0
        
        # Déterminer le statut de conformité
        if compliance_rate >= 95:
            compliance_status = "excellent"
            risk_score = 0.1
        elif compliance_rate >= 90:
            compliance_status = "good"
            risk_score = 0.2
        elif compliance_rate >= 80:
            compliance_status = "fair"
            risk_score = 0.4
        else:
            compliance_status = "poor"
            risk_score = 0.7
        
        # ====================================================================
        # STEP 5: Détecter les anomalies
        # ====================================================================
        
        anomalies = []
        
        if null_count > (active_rows_count * 0.05):  # Plus de 5% de valeurs null
            anomalies.append({
                "type": "high_null_rate",
                "count": null_count,
                "percentage": round((null_count / active_rows_count) * 100, 2),
                "severity": "medium"
            })
        
        if not_numeric > (non_null_count * 0.1):  # Plus de 10% non-numériques
            anomalies.append({
                "type": "non_numeric_values",
                "count": not_numeric,
                "percentage": round((not_numeric / non_null_count) * 100, 2),
                "severity": "high"
            })
        
        if not_matching_length > (non_null_count * 0.1):  # Plus de 10% mauvaise longueur
            anomalies.append({
                "type": "incorrect_length",
                "count": not_matching_length,
                "percentage": round((not_matching_length / non_null_count) * 100, 2),
                "severity": "medium"
            })
        
        # ====================================================================
        # STEP 6: Construire le résultat
        # ====================================================================
        
        analysis_result = {
            "status": "completed",
            "country": country,
            "column_analyzed": msisdn_column,
            
            # Comptages
            "row_count": active_rows_count,
            "non_null_count": non_null_count,
            "null_count": null_count,
            "valid_count": valid_count,
            
            # Conformité
            "compliance_rate": round(compliance_rate, 2),
            "compliance_status": compliance_status,
            "risk_score": risk_score,
            
            # Détails du format
            "format_details": {
                "expected_length": most_common_length,
                "expected_format": "numeric only",
                "matching_length_count": matching_length_count,
                "matching_length_percentage": round((matching_length_count / non_null_count * 100) if non_null_count > 0 else 0, 2),
                "numeric_count": numeric_count,
                "numeric_percentage": round((numeric_count / non_null_count * 100) if non_null_count > 0 else 0, 2),
            },
            
            # Contrôles
            "controls": {
                "Null Values": null_count,
                "Most Common Length": most_common_length,
                "Not Matching Length": not_matching_length,
                "Not Numeric": not_numeric,
            },
            
            # Résumé
            "summary": {
                "total_active_records": active_rows_count,
                "records_with_data": non_null_count,
                "records_with_valid_format": valid_count,
                "records_with_issues": null_count + (non_null_count - valid_count),
            },
            
            # Anomalies
            "anomalies": anomalies,
        }
        
        state["msisdn_analysis"] = analysis_result
        
        print(f"\n✅ MSISDN Analysis Complete")
        print(f"   Compliance: {compliance_rate:.2f}%")
        print(f"   Status: {compliance_status.upper()}")
        print(f"   Risk Score: {risk_score}")
        print(f"   Anomalies: {len(anomalies)}")
        print("=" * 60)
        
        con.close()
        return state
        
    except Exception as e:
        print(f"\n✗ Error during MSISDN analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        
        state["msisdn_analysis"] = {
            "status": "error",
            "error": str(e)
        }
        
        print("=" * 60)
        return state

def analyze_first_name(state: AnalysisAgentState) -> AnalysisAgentState:
    """
    Analyse la colonne prénom pour validité et problèmes courants.
    
    Utilise active_rows_count du state pour éviter les recalculs.
    TOUTES LES REQUÊTES S'EXÉCUTENT UNIQUEMENT SUR LES LIGNES ACTIVES.
    
    Args:
        state: AnalysisAgentState avec file_path, schema_mapping, country, active_rows_count
        
    Returns:
        État mis à jour avec résultats d'analyse prénom
    """
    
    print("\n" + "=" * 60)
    print("👤 ANALYZING FIRST NAME")
    print("=" * 60)
    
    # ✅ Récupérer active_rows_count depuis state
    active_rows_count = state.get("active_rows_count", 0)
    
    # Récupérer la colonne prénom
    schema_mapping = state.get("schema_mapping", {})
    first_name_column = schema_mapping.get("prenom_column")
    
    if not first_name_column:
        print("⚠️ No first name column mapped - skipping analysis")
        state["first_name_analysis"] = {
            "status": "skipped",
            "reason": "No first name column mapped"
        }
        return state
    
    file_path = state.get("file_path")
    country = state.get("country", "Unknown")
    data = state.get("data", [])
    
    if not file_path and not data:
        print("❌ No file path or data provided")
        state["first_name_analysis"] = {
            "status": "error",
            "error": "No file path or data provided"
        }
        return state
    
    try:
        print(f"👤 Analyzing first name column: '{first_name_column}'")
        print(f"🌍 Country: {country}")
        print(f"✓ Active rows: {active_rows_count:,}")
        
        if active_rows_count == 0:
            print("⚠️ No active records found")
            state["first_name_analysis"] = {
                "status": "warning",
                "row_count": 0,
                "valid_names_count": 0,
                "compliance_rate": 0.0,
                "warning": "No active records found"
            }
            return state
        
        # ====================================================================
        # STEP 1: Charger les données
        # ====================================================================
        
        print(f"\n📊 Extracting first names...")
        
        if data:
            # Données en mémoire
            first_names = [
                str(record.get(first_name_column, "")).strip()
                for record in data
            ]
        else:
            # Lire depuis fichier
            con = duckdb.connect()
            first_names = ChunkedColumn(
                file_path, first_name_column,
                delimiter=state.get("detected_delimiter") or ",",
                active_status_column=state.get("active_status_column"),
                active_status_values=state.get("active_status_values"),
                expected_length=active_rows_count,
            )
            con.close()
        
        print(f"   ✓ Total records: {active_rows_count:,}")
        
        # ====================================================================
        # STEP 2: Analyser les prénoms
        # ====================================================================
        
        print(f"\n📊 Analyzing first names...")
        
        # Compteurs
        null_count = sum(1 for name in first_names if not name or name == "")
        single_char_count = sum(1 for name in first_names if len(name) == 1)
        numeric_only_count = sum(1 for name in first_names if name.isdigit() and name != "")
        whitespace_only_count = sum(1 for name in first_names if name.strip() == "" and name != "")
        extremely_long_count = sum(1 for name in first_names if len(name) > 100)
        
        # Compter les noms avec caractères spéciaux (non-alphanumériques sauf espaces)
        special_char_count = 0
        for name in first_names:
            if name and not all(c.isalpha() or c.isspace() for c in name):
                special_char_count += 1
        
        print(f"   ✓ Null/empty: {null_count:,}")
        print(f"   ✓ Single character: {single_char_count:,}")
        print(f"   ✓ Numeric only: {numeric_only_count:,}")
        print(f"   ✓ Whitespace only: {whitespace_only_count:,}")
        print(f"   ✓ Special characters: {special_char_count:,}")
        print(f"   ✓ Extremely long (>100 chars): {extremely_long_count:,}")
        
        # ====================================================================
        # STEP 3: Calculer les noms valides
        # ====================================================================
        
        # Valides = pas de problèmes détectés
        invalid_count = (
            null_count + 
            single_char_count + 
            numeric_only_count + 
            whitespace_only_count + 
            special_char_count + 
            extremely_long_count
        )
        
        valid_names_count = active_rows_count - invalid_count
        
        if active_rows_count > 0:
            compliance_rate = (valid_names_count / active_rows_count) * 100
        else:
            compliance_rate = 0.0
        
        print(f"\n📊 Validation Results:")
        print(f"   ✓ Valid names: {valid_names_count:,}")
        print(f"   ✓ Invalid names: {invalid_count:,}")
        print(f"   ✓ Compliance rate: {compliance_rate:.2f}%")
        
        # ====================================================================
        # STEP 4: Déterminer le statut de conformité
        # ====================================================================
        
        if compliance_rate >= 95:
            compliance_status = "excellent"
            risk_score = 0.1
        elif compliance_rate >= 90:
            compliance_status = "good"
            risk_score = 0.2
        elif compliance_rate >= 80:
            compliance_status = "fair"
            risk_score = 0.4
        else:
            compliance_status = "poor"
            risk_score = 0.6
        
        # ====================================================================
        # STEP 5: Détecter les anomalies
        # ====================================================================
        
        anomalies = []
        
        if null_count > (active_rows_count * 0.05):  # Plus de 5% null
            anomalies.append({
                "type": "high_null_rate",
                "count": null_count,
                "percentage": round((null_count / active_rows_count) * 100, 2),
                "severity": "high"
            })
        
        if single_char_count > (active_rows_count * 0.05):  # Plus de 5% single char
            anomalies.append({
                "type": "single_character_names",
                "count": single_char_count,
                "percentage": round((single_char_count / active_rows_count) * 100, 2),
                "severity": "medium"
            })
        
        if numeric_only_count > (active_rows_count * 0.01):  # Plus de 1% numeric only
            anomalies.append({
                "type": "numeric_only_names",
                "count": numeric_only_count,
                "percentage": round((numeric_only_count / active_rows_count) * 100, 2),
                "severity": "high"
            })
        
        if special_char_count > (active_rows_count * 0.1):  # Plus de 10% special chars
            anomalies.append({
                "type": "special_characters",
                "count": special_char_count,
                "percentage": round((special_char_count / active_rows_count) * 100, 2),
                "severity": "medium"
            })
        
        if extremely_long_count > (active_rows_count * 0.01):  # Plus de 1% extremely long
            anomalies.append({
                "type": "extremely_long_names",
                "count": extremely_long_count,
                "percentage": round((extremely_long_count / active_rows_count) * 100, 2),
                "severity": "low"
            })
        
        # ====================================================================
        # STEP 6: Construire le résultat
        # ====================================================================
        
        analysis_result = {
            "status": "completed",
            "country": country,
            "column_analyzed": first_name_column,
            
            # Comptages
            "row_count": active_rows_count,
            "null_count": null_count,
            #"non_null_count": non_null_count,
            "valid_count": valid_names_count,
            "invalid_names_count": invalid_count,
            
            # Conformité
            "compliance_rate": round(compliance_rate, 2),
            "compliance_status": compliance_status,
            "risk_score": risk_score,
            
            # Contrôles détaillés
            "controls": {
                "Null Values": null_count,
                "Single Character Names": single_char_count,
                "Numeric Only Names": numeric_only_count,
                "Whitespace Only Names": whitespace_only_count,
                "Contains Special Characters": special_char_count,
                "Extremely Long Names (>100 chars)": extremely_long_count,
            },
            
            # Résumé
            "summary": {
                "total_active_records": active_rows_count,
                "records_with_data": active_rows_count - null_count,
                "records_with_valid_format": valid_names_count,
                "records_with_issues": invalid_count,
            },
            
            # Anomalies
            "anomalies": anomalies,
        }
        
        state["first_name_analysis"] = analysis_result
        
        print(f"\n✅ First Name Analysis Complete")
        print(f"   Compliance: {compliance_rate:.2f}%")
        print(f"   Status: {compliance_status.upper()}")
        print(f"   Risk Score: {risk_score}")
        print(f"   Anomalies: {len(anomalies)}")
        print("=" * 60)
        
        return state
        
    except Exception as e:
        print(f"\n✗ Error during first name analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        
        state["first_name_analysis"] = {
            "status": "error",
            "error": str(e)
        }
        
        print("=" * 60)
        return state

def analyze_last_name(state: AnalysisAgentState) -> AnalysisAgentState:
    """
    Analyse la colonne nom de famille pour validité et problèmes courants.
    
    Utilise active_rows_count du state pour éviter les recalculs.
    TOUTES LES REQUÊTES S'EXÉCUTENT UNIQUEMENT SUR LES LIGNES ACTIVES.
    
    Args:
        state: AnalysisAgentState avec file_path, schema_mapping, country, active_rows_count
        
    Returns:
        État mis à jour avec résultats d'analyse nom de famille
    """
    
    print("\n" + "=" * 60)
    print("👤 ANALYZING LAST NAME")
    print("=" * 60)

    
    # ✅ Récupérer active_rows_count depuis state
    active_rows_count = state.get("active_rows_count", 0)
    
    # Récupérer la colonne nom de famille
    schema_mapping = state.get("schema_mapping", {})
    last_name_column = schema_mapping.get("nom_column")
    
    if not last_name_column:
        print("⚠️ No last name column mapped - skipping analysis")
        state["last_name_analysis"] = {
            "status": "skipped",
            "reason": "No last name column mapped"
        }
        return state
    
    file_path = state.get("file_path")
    country = state.get("country", "Unknown")
    data = state.get("data", [])
    
    if not file_path and not data:
        print("❌ No file path or data provided")
        state["last_name_analysis"] = {
            "status": "error",
            "error": "No file path or data provided"
        }
        return state
    
    try:
        print(f"👤 Analyzing last name column: '{last_name_column}'")
        print(f"🌍 Country: {country}")
        print(f"✓ Active rows: {active_rows_count:,}")
        
        if active_rows_count == 0:
            print("⚠️ No active records found")
            state["last_name_analysis"] = {
                "status": "warning",
                "row_count": 0,
                "valid_names_count": 0,
                "compliance_rate": 0.0,
                "warning": "No active records found"
            }
            return state
        
        # ====================================================================
        # STEP 1: Charger les données
        # ====================================================================
        
        print(f"\n📊 Extracting last names...")
        
        if data:
            # Données en mémoire
            last_names = [
                str(record.get(last_name_column, "")).strip()
                for record in data
            ]
        else:
            # Lire depuis fichier
            con = duckdb.connect()
            last_names = ChunkedColumn(
                file_path, last_name_column,
                delimiter=state.get("detected_delimiter") or ",",
                active_status_column=state.get("active_status_column"),
                active_status_values=state.get("active_status_values"),
                expected_length=active_rows_count,
            )
            con.close()
        
        print(f"   ✓ Total records: {active_rows_count:,}")
        
        # ====================================================================
        # STEP 2: Analyser les noms de famille
        # ====================================================================
        
        print(f"\n📊 Analyzing last names...")
        
        # Compteurs
        null_count = sum(1 for name in last_names if not name or name == "")
        single_char_count = sum(1 for name in last_names if len(name) == 1)
        numeric_only_count = sum(1 for name in last_names if name.isdigit() and name != "")
        whitespace_only_count = sum(1 for name in last_names if name.strip() == "" and name != "")
        extremely_long_count = sum(1 for name in last_names if len(name) > 100)
        
        # Compter les noms avec caractères spéciaux (non-alphanumériques sauf espaces et tirets)
        # Les tirets sont autorisés dans les noms de famille (ex: Jean-Pierre)
        special_char_count = 0
        for name in last_names:
            if name and not all(c.isalpha() or c.isspace() or c == '-' for c in name):
                special_char_count += 1
        
        print(f"   ✓ Null/empty: {null_count:,}")
        print(f"   ✓ Single character: {single_char_count:,}")
        print(f"   ✓ Numeric only: {numeric_only_count:,}")
        print(f"   ✓ Whitespace only: {whitespace_only_count:,}")
        print(f"   ✓ Special characters: {special_char_count:,}")
        print(f"   ✓ Extremely long (>100 chars): {extremely_long_count:,}")
        
        # ====================================================================
        # STEP 3: Calculer les noms valides
        # ====================================================================
        
        # Valides = pas de problèmes détectés
        invalid_count = (
            null_count + 
            single_char_count + 
            numeric_only_count + 
            whitespace_only_count + 
            special_char_count + 
            extremely_long_count
        )
        
        valid_names_count = active_rows_count - invalid_count
        
        if active_rows_count > 0:
            compliance_rate = (valid_names_count / active_rows_count) * 100
        else:
            compliance_rate = 0.0
        
        print(f"\n📊 Validation Results:")
        print(f"   ✓ Valid names: {valid_names_count:,}")
        print(f"   ✓ Invalid names: {invalid_count:,}")
        print(f"   ✓ Compliance rate: {compliance_rate:.2f}%")
        
        # ====================================================================
        # STEP 4: Déterminer le statut de conformité
        # ====================================================================
        
        if compliance_rate >= 95:
            compliance_status = "excellent"
            risk_score = 0.1
        elif compliance_rate >= 90:
            compliance_status = "good"
            risk_score = 0.2
        elif compliance_rate >= 80:
            compliance_status = "fair"
            risk_score = 0.4
        else:
            compliance_status = "poor"
            risk_score = 0.6
        
        # ====================================================================
        # STEP 5: Détecter les anomalies
        # ====================================================================
        
        anomalies = []
        
        if null_count > (active_rows_count * 0.05):  # Plus de 5% null
            anomalies.append({
                "type": "high_null_rate",
                "count": null_count,
                "percentage": round((null_count / active_rows_count) * 100, 2),
                "severity": "high"
            })
        
        if single_char_count > (active_rows_count * 0.05):  # Plus de 5% single char
            anomalies.append({
                "type": "single_character_names",
                "count": single_char_count,
                "percentage": round((single_char_count / active_rows_count) * 100, 2),
                "severity": "medium"
            })
        
        if numeric_only_count > (active_rows_count * 0.01):  # Plus de 1% numeric only
            anomalies.append({
                "type": "numeric_only_names",
                "count": numeric_only_count,
                "percentage": round((numeric_only_count / active_rows_count) * 100, 2),
                "severity": "high"
            })
        
        if special_char_count > (active_rows_count * 0.15):  # Plus de 15% special chars (plus tolérant que prénom)
            anomalies.append({
                "type": "special_characters",
                "count": special_char_count,
                "percentage": round((special_char_count / active_rows_count) * 100, 2),
                "severity": "low",
                "note": "Tirets autorisés dans les noms de famille"
            })
        
        if extremely_long_count > (active_rows_count * 0.01):  # Plus de 1% extremely long
            anomalies.append({
                "type": "extremely_long_names",
                "count": extremely_long_count,
                "percentage": round((extremely_long_count / active_rows_count) * 100, 2),
                "severity": "low"
            })
        
        # ====================================================================
        # STEP 6: Construire le résultat
        # ====================================================================
        
        analysis_result = {
            "status": "completed",
            "country": country,
            "column_analyzed": last_name_column,
            
            # Comptages
            "row_count": active_rows_count,
            "valid_count": valid_names_count,
            "invalid_names_count": invalid_count,
            "null_count": null_count,
            #"non_null_count": non_null_count,

            
            # Conformité
            "compliance_rate": round(compliance_rate, 2),
            "compliance_status": compliance_status,
            "risk_score": risk_score,
            
            # Contrôles détaillés
            "controls": {
                "Null Values": null_count,
                "Single Character Names": single_char_count,
                "Numeric Only Names": numeric_only_count,
                "Whitespace Only Names": whitespace_only_count,
                "Contains Special Characters": special_char_count,
                "Extremely Long Names (>100 chars)": extremely_long_count,
            },
            
            # Résumé
            "summary": {
                "total_active_records": active_rows_count,
                "records_with_data": active_rows_count - null_count,
                "records_with_valid_format": valid_names_count,
                "records_with_issues": invalid_count,
            },
            
            # Anomalies
            "anomalies": anomalies,
        }
        
        state["last_name_analysis"] = analysis_result
        
        print(f"\n✅ Last Name Analysis Complete")
        print(f"   Compliance: {compliance_rate:.2f}%")
        print(f"   Status: {compliance_status.upper()}")
        print(f"   Risk Score: {risk_score}")
        print(f"   Anomalies: {len(anomalies)}")
        print("=" * 60)
        
        return state
        
    except Exception as e:
        print(f"\n✗ Error during last name analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        
        state["last_name_analysis"] = {
            "status": "error",
            "error": str(e)
        }
        
        print("=" * 60)
        return state

def analyze_id_type(state: AnalysisAgentState) -> AnalysisAgentState:
    """
    Analyse la colonne type d'ID pour déterminer le type dominant et la validité.
    
    Utilise active_rows_count du state pour éviter les recalculs.
    TOUTES LES REQUÊTES S'EXÉCUTENT UNIQUEMENT SUR LES LIGNES ACTIVES.
    
    Args:
        state: AnalysisAgentState avec file_path, schema_mapping, country, active_rows_count
        
    Returns:
        État mis à jour avec résultats d'analyse type d'ID
    """
    
    print("\n" + "=" * 60)
    print("🆔 ANALYZING ID TYPE")
    print("=" * 60)
    
    # ✅ Récupérer active_rows_count depuis state
    active_rows_count = state.get("active_rows_count", 0)
    
    # Récupérer la colonne type d'ID
    schema_mapping = state.get("schema_mapping", {})
    id_type_column = schema_mapping.get("id_type_column")
    
    if not id_type_column:
        print("⚠️ No ID type column mapped - skipping analysis")
        state["id_type_analysis"] = {
            "status": "skipped",
            "reason": "No ID type column mapped"
        }
        return state
    
    file_path = state.get("file_path")
    country = state.get("country", "Unknown")
    data = state.get("data", [])
    
    if not file_path and not data:
        print("❌ No file path or data provided")
        state["id_type_analysis"] = {
            "status": "error",
            "error": "No file path or data provided"
        }
        return state
    
    try:
        from src.config.id_validation_rules import get_expected_id_types
        from collections import Counter
        
        print(f"🆔 Analyzing ID type column: '{id_type_column}'")
        print(f"🌍 Country: {country}")
        print(f"✓ Active rows: {active_rows_count:,}")
        
        if active_rows_count == 0:
            print("⚠️ No active records found")
            state["id_type_analysis"] = {
                "status": "warning",
                "row_count": 0,
                "warning": "No active records found"
            }
            return state
        
        # ====================================================================
        # STEP 1: Charger les données
        # ====================================================================
        
        print(f"\n📊 Extracting ID types...")
        
        if data:
            # Données en mémoire
            id_types = [
                str(record.get(id_type_column, "")).strip().upper()
                for record in data
            ]
        else:
            # Lire depuis fichier
            con = duckdb.connect()
            id_types = ChunkedColumn(
                file_path, id_type_column,
                delimiter=state.get("detected_delimiter") or ",",
                active_status_column=state.get("active_status_column"),
                active_status_values=state.get("active_status_values"),
                uppercase=True,
                expected_length=active_rows_count,
            )
            con.close()
        
        print(f"   ✓ Total records: {active_rows_count:,}")
        
        # ====================================================================
        # STEP 2: Analyser les types d'ID
        # ====================================================================
        
        print(f"\n📊 Analyzing ID types...")
        
        # Compter les valeurs null/vides
        null_count = sum(1 for id_type in id_types if not id_type or id_type == "")
        non_null_count = active_rows_count - null_count
        
        print(f"   ✓ Null/empty: {null_count:,}")
        print(f"   ✓ Non-null: {non_null_count:,}")
        
        if non_null_count == 0:
            print("⚠️ No non-null ID types found")
            state["id_type_analysis"] = {
                "status": "warning",
                "row_count": active_rows_count,
                "null_count": null_count,
                "warning": "No non-null ID types found"
            }
            return state
        
        # ====================================================================
        # STEP 3: Déterminer les types dominants
        # ====================================================================
        
        # Compter les occurrences
        id_type_counts = Counter([t for t in id_types if t])
        most_common = id_type_counts.most_common()
        
        print(f"\n📊 ID Type Distribution:")
        for id_type, count in most_common:
            percentage = (count / non_null_count) * 100
            print(f"   • {id_type}: {count:,} ({percentage:.2f}%)")
        
        # Type dominant
        dominant_id_type = most_common[0][0] if most_common else None
        dominant_count = most_common[0][1] if most_common else 0
        dominant_percentage = (dominant_count / non_null_count * 100) if non_null_count > 0 else 0
        
        # Nombre de types distincts
        distinct_id_types_count = len(id_type_counts)
        
        # ====================================================================
        # STEP 4: Valider contre les types attendus
        # ====================================================================
        
        expected_types = get_expected_id_types(country)
        print(f"\n📊 Expected ID types for {country}: {expected_types}")
        
        # Normaliser les types attendus
        expected_types_normalized = [t.upper() for t in expected_types]
        
        # Compter les types valides vs invalides
        valid_type_count = sum(
            1 for id_type in id_types
            if id_type and id_type in expected_types_normalized
        )
        
        invalid_type_count = sum(
            1 for id_type in id_types
            if id_type and id_type not in expected_types_normalized
        )
        
        print(f"   ✓ Valid types: {valid_type_count:,}")
        print(f"   ✓ Invalid types: {invalid_type_count:,}")
        
        # ====================================================================
        # STEP 5: Calculer la conformité
        # ====================================================================
        
        if non_null_count > 0:
            compliance_rate = (valid_type_count / active_rows_count) * 100
        else:
            compliance_rate = 0.0
        
        # Déterminer le statut
        if compliance_rate >= 95:
            compliance_status = "excellent"
            risk_score = 0.1
        elif compliance_rate >= 90:
            compliance_status = "good"
            risk_score = 0.2
        elif compliance_rate >= 80:
            compliance_status = "fair"
            risk_score = 0.4
        else:
            compliance_status = "poor"
            risk_score = 0.6
        
        # ====================================================================
        # STEP 6: Détecter les anomalies
        # ====================================================================
        
        anomalies = []
        
        if null_count > (active_rows_count * 0.05):
            anomalies.append({
                "type": "high_null_rate",
                "count": null_count,
                "percentage": round((null_count / active_rows_count) * 100, 2),
                "severity": "medium"
            })
        
        if invalid_type_count > (non_null_count * 0.1):
            anomalies.append({
                "type": "invalid_id_types",
                "count": invalid_type_count,
                "percentage": round((invalid_type_count / non_null_count) * 100, 2),
                "severity": "high",
                "details": {
                    "expected": expected_types,
                    "found": [t for t, _ in most_common]
                }
            })
        
        if distinct_id_types_count > len(expected_types) + 2:
            anomalies.append({
                "type": "too_many_distinct_types",
                "count": distinct_id_types_count,
                "expected": len(expected_types),
                "severity": "medium",
                "note": "More distinct ID types than expected for this country"
            })
        
        # ====================================================================
        # STEP 7: Construire la distribution détaillée
        # ====================================================================
        
        # Créer une distribution avec les types null/empty
        id_type_distribution = dict(most_common)
        if null_count > 0:
            id_type_distribution["NULL_OR_EMPTY"] = null_count
        
        # ====================================================================
        # STEP 8: Construire le résultat
        # ====================================================================
        
        analysis_result = {
            "status": "completed",
            "country": country,
            "column_analyzed": id_type_column,
            
            # Comptages
            "row_count": active_rows_count,
            "null_count": null_count,
            "non_null_count": non_null_count,
            "valid_type_count": valid_type_count,
            "invalid_type_count": invalid_type_count,
            
            # Type dominant
            "dominant_id_type": dominant_id_type,
            "dominant_count": dominant_count,
            "dominant_percentage": round(dominant_percentage, 2),
            
            # Types distincts
            "distinct_id_types_count": distinct_id_types_count,
            
            # Conformité
            "compliance_rate": round(compliance_rate, 2),
            "compliance_status": compliance_status,
            "risk_score": risk_score,
            
            # Distribution
            "id_type_distribution": id_type_distribution,
            "expected_id_types": expected_types,
            
            # Contrôles
            "controls": {
                "Null or Empty ID Types": null_count,
                "Distinct ID Types Count": distinct_id_types_count,
                "Invalid ID Types": invalid_type_count,
            },
            
            # Résumé
            "summary": {
                "total_active_records": active_rows_count,
                "records_with_data": non_null_count,
                "records_with_valid_type": valid_type_count,
                "records_with_issues": null_count + invalid_type_count,
                "most_common_id_type": dominant_id_type,
                "most_common_id_type_count": dominant_count,
                "most_common_id_type_percentage": round(dominant_percentage, 2),
            },
            
            # Anomalies
            "anomalies": anomalies,
        }
        
        state["id_type_analysis"] = analysis_result
        
        # Stocker le type d'ID dominant pour utilisation dans analyze_id_number
        state["detected_id_type"] = dominant_id_type
        
        print(f"\n✅ ID Type Analysis Complete")
        print(f"   Dominant Type: {dominant_id_type} ({dominant_percentage:.2f}%)")
        print(f"   Distinct Types: {distinct_id_types_count}")
        print(f"   Compliance: {compliance_rate:.2f}%")
        print(f"   Status: {compliance_status.upper()}")
        print(f"   Anomalies: {len(anomalies)}")
        print("=" * 60)
        
        return state
        
    except Exception as e:
        print(f"\n✗ Error during ID type analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        
        state["id_type_analysis"] = {
            "status": "error",
            "error": str(e)
        }
        
        print("=" * 60)
        return state

def analyze_id_number(state: AnalysisAgentState) -> AnalysisAgentState:
    """
    Analyse la colonne numéro d'ID.
    
    Si un type d'ID dominant a été détecté (analyze_id_type), valide contre
    les règles de ce type précis. Sinon (type absent/non fiable — cas
    fréquent avec des données de qualité variable), valide chaque numéro
    contre TOUS les formats connus du pays et considère valide tout numéro
    qui matche au moins un format.
    
    TOUTES LES REQUÊTES S'EXÉCUTENT UNIQUEMENT SUR LES LIGNES ACTIVES.
    """
    
    print("\n" + "=" * 60)
    print("🔢 ANALYZING ID NUMBER")
    print("=" * 60)

    active_rows_count = state.get("active_rows_count", 0)
    
    schema_mapping = state.get("schema_mapping", {})
    id_number_column = schema_mapping.get("id_number_column")
    
    if not id_number_column:
        print("⚠️ No ID number column mapped - skipping analysis")
        state["id_number_analysis"] = {
            "status": "skipped",
            "reason": "No ID number column mapped"
        }
        return state
    
    file_path = state.get("file_path")
    country = state.get("country", "Unknown")
    detected_id_type = state.get("detected_id_type")
    data = state.get("data", [])
    
    if not file_path and not data:
        print("❌ No file path or data provided")
        state["id_number_analysis"] = {
            "status": "error",
            "error": "No file path or data provided"
        }
        return state
    
    try:
        from src.config.id_validation_rules import (
            get_id_validation_rules,
            validate_id_number,
            validate_id_number_any_type,
        )
        from collections import Counter
        import re
        
        print(f"🔢 Analyzing ID number column: '{id_number_column}'")
        print(f"🌍 Country: {country}")
        print(f"🆔 ID Type: {detected_id_type}")
        print(f"✓ Active rows: {active_rows_count:,}")
        
        if active_rows_count == 0:
            print("⚠️ No active records found")
            state["id_number_analysis"] = {
                "status": "warning",
                "row_count": 0,
                "warning": "No active records found"
            }
            return state
        
        print(f"\n📊 Extracting ID numbers...")
        
        if data:
            id_numbers = [
                str(record.get(id_number_column, "")).strip()
                for record in data
            ]
        else:
            id_numbers = ChunkedColumn(
                file_path, id_number_column,
                delimiter=state.get("detected_delimiter") or ",",
                active_status_column=state.get("active_status_column"),
                active_status_values=state.get("active_status_values"),
                expected_length=active_rows_count,
            )
        
        print(f"   ✓ Total records: {active_rows_count:,}")
        
        # Détermine le mode de validation : type précis connu, ou fallback
        # multi-types si le type d'ID est absent/non reconnu pour ce pays.
        single_type_rules = get_id_validation_rules(country, detected_id_type)
        use_any_type_mode = not detected_id_type or not single_type_rules or "format" not in single_type_rules
        
        if use_any_type_mode:
            print(f"\n⚠️ ID type absent ou non reconnu — validation multi-types activée")
            print(f"   Un numéro sera considéré valide s'il correspond à au moins")
            print(f"   un des formats connus pour {country}.")
        else:
            print(f"\n📋 Validation Rules ({detected_id_type}):")
            print(f"   • Format: {single_type_rules.get('format')}")
            print(f"   • Pattern: {single_type_rules.get('pattern')}")
            print(f"   • Length: {single_type_rules.get('length', 'Variable')}")
        
        print(f"\n📊 Analyzing ID numbers...")
        
        null_count = sum(1 for id_num in id_numbers if not id_num or id_num == "")
        non_null_count = active_rows_count - null_count
        
        print(f"   ✓ Null/empty: {null_count:,}")
        print(f"   ✓ Non-null: {non_null_count:,}")
        
        if non_null_count == 0:
            print("⚠️ No non-null ID numbers found")
            state["id_number_analysis"] = {
                "status": "warning",
                "row_count": active_rows_count,
                "null_count": null_count,
                "warning": "No non-null ID numbers found"
            }
            return state
        
        print(f"\n📊 Validating ID numbers...")
        
        valid_count = 0
        invalid_count = 0
        validation_errors = Counter()
        matched_type_distribution = Counter()  # utile seulement en mode multi-types
        length_distribution = Counter()
        duplicate_ids = Counter()
        
        valid_ids = []
        
        for id_num in id_numbers:
            if not id_num:
                continue
            
            if use_any_type_mode:
                validation_result = validate_id_number_any_type(id_num, country)
                if validation_result["valid"]:
                    valid_count += 1
                    valid_ids.append(id_num)
                    duplicate_ids[id_num] += 1
                    matched_type_distribution[validation_result["matched_type"]] += 1
                else:
                    invalid_count += 1
                    validation_errors[validation_result.get("error", "Unknown error")] += 1
            else:
                validation_result = validate_id_number(id_num, country, detected_id_type)
                if validation_result["valid"]:
                    valid_count += 1
                    valid_ids.append(id_num)
                    duplicate_ids[id_num] += 1
                else:
                    invalid_count += 1
                    error = validation_result.get("error", "Unknown error")
                    validation_errors[error] += 1
            
            length_distribution[len(id_num)] += 1
        
        print(f"   ✓ Valid: {valid_count:,}")
        print(f"   ✓ Invalid: {invalid_count:,}")
        
        if use_any_type_mode and matched_type_distribution:
            print(f"\n   Répartition des formats détectés parmi les valides:")
            for type_key, count in matched_type_distribution.most_common():
                print(f"   • {type_key}: {count:,}")
        
        if validation_errors:
            print(f"\n   Validation Errors (Top 5):")
            for error, count in validation_errors.most_common(5):
                print(f"   • {error}: {count:,}")
        
        print(f"\n📊 Detecting duplicates...")
        
        duplicate_count = sum(1 for id_num, count in duplicate_ids.items() if count > 1)
        duplicate_records_count = sum(count - 1 for count in duplicate_ids.values() if count > 1)
        
        print(f"   ✓ Unique valid IDs: {len(set(valid_ids)):,}")
        print(f"   ✓ Duplicate IDs: {duplicate_count:,}")
        print(f"   ✓ Duplicate records: {duplicate_records_count:,}")
        
        top_duplicates = duplicate_ids.most_common(5)
        if top_duplicates:
            print(f"\n   Top Duplicates:")
            for id_num, count in top_duplicates:
                if count > 1:
                    print(f"   • {id_num}: {count} occurrences")
        
        print(f"\n📊 Length Distribution:")
        for length, count in sorted(length_distribution.items()):
            percentage = (count / non_null_count) * 100
            print(f"   • {length} chars: {count:,} ({percentage:.2f}%)")
        
        most_common_length = length_distribution.most_common(1)[0][0] if length_distribution else 0
        expected_length = None if use_any_type_mode else single_type_rules.get("length")
        
        print(f"\n📊 Detecting suspicious patterns...")
        
        suspicious_patterns = {
            "sequential": 0,
            "repeated": 0,
            "all_zeros": 0,
            "all_nines": 0,
        }
        
        for id_num in valid_ids:
            if re.match(r'^[0-9]{2,}$', id_num):
                digits = [int(d) for d in id_num]
                if all(digits[i] == digits[i-1] + 1 for i in range(1, len(digits))):
                    suspicious_patterns["sequential"] += 1
            
            if len(set(id_num)) == 1:
                if id_num[0] == '0':
                    suspicious_patterns["all_zeros"] += 1
                elif id_num[0] == '9':
                    suspicious_patterns["all_nines"] += 1
                else:
                    suspicious_patterns["repeated"] += 1
        
        print(f"   ✓ Sequential patterns: {suspicious_patterns['sequential']:,}")
        print(f"   ✓ Repeated digits: {suspicious_patterns['repeated']:,}")
        print(f"   ✓ All zeros: {suspicious_patterns['all_zeros']:,}")
        print(f"   ✓ All nines: {suspicious_patterns['all_nines']:,}")
        
        if active_rows_count > 0:
            compliance_rate = (valid_count / active_rows_count) * 100
        else:
            compliance_rate = 0.0
        
        if compliance_rate >= 95:
            compliance_status = "excellent"
            risk_score = 0.1
        elif compliance_rate >= 90:
            compliance_status = "good"
            risk_score = 0.2
        elif compliance_rate >= 80:
            compliance_status = "fair"
            risk_score = 0.4
        else:
            compliance_status = "poor"
            risk_score = 0.7
        
        anomalies = []
        
        if null_count > (active_rows_count * 0.05):
            anomalies.append({
                "type": "high_null_rate",
                "count": null_count,
                "percentage": round((null_count / active_rows_count) * 100, 2),
                "severity": "high"
            })
        
        if invalid_count > (active_rows_count * 0.1):
            anomalies.append({
                "type": "invalid_format",
                "count": invalid_count,
                "percentage": round((invalid_count / non_null_count) * 100, 2),
                "severity": "high",
                "details": dict(validation_errors.most_common(3))
            })
        
        if expected_length and most_common_length != expected_length:
            anomalies.append({
                "type": "unexpected_length",
                "expected": expected_length,
                "found": most_common_length,
                "severity": "medium"
            })
        
        if duplicate_records_count > (non_null_count * 0.05):
            anomalies.append({
                "type": "high_duplicate_rate",
                "count": duplicate_records_count,
                "percentage": round((duplicate_records_count / non_null_count) * 100, 2),
                "severity": "high",
                "details": {
                    "unique_ids": len(set(valid_ids)),
                    "duplicate_ids": duplicate_count,
                    "top_duplicates": dict(top_duplicates[:3])
                }
            })
        
        suspicious_total = sum(suspicious_patterns.values())
        if valid_count > 0 and suspicious_total > (valid_count * 0.05):
            anomalies.append({
                "type": "suspicious_patterns",
                "count": suspicious_total,
                "percentage": round((suspicious_total / valid_count) * 100, 2),
                "severity": "medium",
                "details": suspicious_patterns
            })
        
        if use_any_type_mode:
            anomalies.append({
                "type": "id_type_undetected",
                "count": null_count if detected_id_type is None else 0,
                "percentage": 0,
                "severity": "low",
                "note": (
                    "Le type d'ID n'a pas pu être déterminé de façon fiable "
                    "(colonne vide ou incohérente). Les numéros ont été "
                    "validés contre tous les formats connus du pays."
                )
            })
        
        analysis_result = {
            "status": "completed",
            "country": country,
            "id_type": detected_id_type,
            "validation_mode": "any_type" if use_any_type_mode else "single_type",
            "column_analyzed": id_number_column,
            
            "row_count": active_rows_count,
            "null_count": null_count,
            "non_null_count": non_null_count,
            "valid_count": valid_count,
            "invalid_count": invalid_count,
            
            "compliance_rate": round(compliance_rate, 2),
            "compliance_status": compliance_status,
            "risk_score": risk_score,
            
            "format_details": {
                "expected_format": None if use_any_type_mode else single_type_rules.get("format"),
                "expected_length": expected_length,
                "most_common_length": most_common_length,
                "pattern": None if use_any_type_mode else single_type_rules.get("pattern"),
            },
            
            "matched_type_distribution": dict(matched_type_distribution) if use_any_type_mode else None,
            
            "length_distribution": dict(length_distribution),
            
            "duplicates": {
                "unique_valid_ids": len(set(valid_ids)),
                "duplicate_ids_count": duplicate_count,
                "duplicate_records_count": duplicate_records_count,
                "duplicate_percentage": round((duplicate_records_count / non_null_count * 100) if non_null_count > 0 else 0, 2),
                "top_duplicates": dict(top_duplicates[:5])
            },
            
            "suspicious_patterns": suspicious_patterns,
            "validation_errors": dict(validation_errors.most_common(10)),
            
            "controls": {
                "Null Values": null_count,
                "Invalid Format": invalid_count,
                "Duplicate Records": duplicate_records_count,
                "Suspicious Patterns": suspicious_total,
            },
            
            "summary": {
                "total_records": active_rows_count,
                "records_with_data": non_null_count,
                "records_with_valid_format": valid_count,
                "records_with_issues": null_count + invalid_count + duplicate_records_count,
                "data_quality_score": round(compliance_rate, 2),
            },
            
            "anomalies": anomalies,
        }
        
        state["id_number_analysis"] = analysis_result
        
        print(f"\n✅ ID Number Analysis Complete")
        print(f"   Mode: {'Multi-types' if use_any_type_mode else detected_id_type}")
        print(f"   Compliance: {compliance_rate:.2f}%")
        print(f"   Status: {compliance_status.upper()}")
        print(f"   Risk Score: {risk_score}")
        print(f"   Unique IDs: {len(set(valid_ids)):,}")
        print(f"   Duplicates: {duplicate_records_count:,}")
        print(f"   Anomalies: {len(anomalies)}")
        print("=" * 60)
        
        return state
        
    except Exception as e:
        print(f"\n✗ Error during ID number analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        
        state["id_number_analysis"] = {
            "status": "error",
            "error": str(e)
        }
        
        print("=" * 60)
        return state
def analyze_dob(state: AnalysisAgentState) -> AnalysisAgentState:
    """
    Analyse la colonne date de naissance pour validité et problèmes courants.
    
    Détecte les formats (même si données non propres), valide les âges, détecte les anomalies.
    Utilise active_rows_count du state pour éviter les recalculs.
    TOUTES LES REQUÊTES S'EXÉCUTENT UNIQUEMENT SUR LES LIGNES ACTIVES.
    
    Args:
        state: AnalysisAgentState avec file_path, schema_mapping, country, active_rows_count
        
    Returns:
        État mis à jour avec résultats d'analyse DOB
    """
    
    print("\n" + "=" * 60)
    print("📅 ANALYZING DATE OF BIRTH")
    print("=" * 60)

    # ✅ Récupérer active_rows_count depuis state
    active_rows_count = state.get("active_rows_count", 0)
    
    # Récupérer la colonne DOB
    schema_mapping = state.get("schema_mapping", {})
    dob_column = schema_mapping.get("dob_column")
    
    if not dob_column:
        print("⚠️ No DOB column mapped - skipping analysis")
        state["dob_analysis"] = {
            "status": "skipped",
            "reason": "No DOB column mapped"
        }
        return state
    
    file_path = state.get("file_path")
    country = state.get("country", "Unknown")
    data = state.get("data", [])
    
    if not file_path and not data:
        print("❌ No file path or data provided")
        state["dob_analysis"] = {
            "status": "error",
            "error": "No file path or data provided"
        }
        return state
    
    try:
        from src.config.dob_validation_rules import (
            get_dob_validation_rules,
            detect_dob_format,
            validate_dob
        )
        from collections import Counter
        from datetime import datetime
        
        print(f"📅 Analyzing DOB column: '{dob_column}'")
        print(f"🌍 Country: {country}")
        print(f"✓ Active rows: {active_rows_count:,}")
        
        # Récupérer les règles du pays
        rules = get_dob_validation_rules(country)
        min_age = rules["min_age"]
        max_age = rules["max_age"]
        
        print(f"\n📋 Validation Rules:")
        print(f"   • Min age: {min_age}")
        print(f"   • Max age: {max_age}")
        
        if active_rows_count == 0:
            print("⚠️ No active records found")
            state["dob_analysis"] = {
                "status": "warning",
                "row_count": 0,
                "warning": "No active records found"
            }
            return state
        
        # ====================================================================
        # STEP 1: Charger les données
        # ====================================================================
        
        print(f"\n📊 Extracting DOB values...")
        
        if data:
            # Données en mémoire
            dob_values = [
                str(record.get(dob_column, "")).strip()
                for record in data
            ]
        else:
            # Lire depuis fichier
            con = duckdb.connect()
            dob_values = ChunkedColumn(
                file_path, dob_column,
                delimiter=state.get("detected_delimiter") or ",",
                active_status_column=state.get("active_status_column"),
                active_status_values=state.get("active_status_values"),
                expected_length=active_rows_count,
            )
            con.close()
        
        print(f"   ✓ Total records: {active_rows_count:,}")
        
        # ====================================================================
        # STEP 2: Analyser les DOB
        # ====================================================================
        
        print(f"\n📊 Analyzing DOB values...")
        
        # Compteurs
        null_count = sum(1 for dob in dob_values if not dob or dob == "")
        non_null_count = active_rows_count - null_count
        
        print(f"   ✓ Null/empty: {null_count:,}")
        print(f"   ✓ Non-null: {non_null_count:,}")
        
        if non_null_count == 0:
            print("⚠️ No non-null DOB values found")
            state["dob_analysis"] = {
                "status": "warning",
                "row_count": active_rows_count,
                "null_count": null_count,
                "warning": "No non-null DOB values found"
            }
            return state
        
        # ====================================================================
        # STEP 3: Détecter les formats et valider
        # ====================================================================
        
        print(f"\n📊 Detecting DOB formats and validating...")
        
        format_counts = Counter()
        valid_count = 0
        invalid_count = 0
        validation_errors = Counter()
        age_distribution = Counter()
        
        for dob in dob_values:
            if not dob:
                continue
            
            # Détecter le format directement dans le node
            detected_format = detect_dob_format(dob)
            
            if detected_format != "UNKNOWN":
                format_counts[detected_format] += 1
            
            # Valider
            validation_result = validate_dob(dob, country)
            
            if validation_result["valid"]:
                valid_count += 1
                age = validation_result.get("age")
                if age is not None:
                    age_distribution[age] += 1
            else:
                invalid_count += 1
                error = validation_result.get("error", "Unknown error")
                validation_errors[error] += 1
        
        print(f"   ✓ Valid: {valid_count:,}")
        print(f"   ✓ Invalid: {invalid_count:,}")
        
        # Afficher les formats détectés
        print(f"\n   Detected Formats:")
        for fmt, count in format_counts.most_common():
            percentage = (count / non_null_count) * 100
            print(f"   • {fmt}: {count:,} ({percentage:.2f}%)")
        
        # Afficher les erreurs
        if validation_errors:
            print(f"\n   Validation Errors (Top 5):")
            for error, count in validation_errors.most_common(5):
                print(f"   • {error}: {count:,}")
        
        # ====================================================================
        # STEP 4: Analyser la distribution des âges
        # ====================================================================
        
        print(f"\n📊 Age Distribution:")
        
        if age_distribution:
            min_age_found = min(age_distribution.keys())
            max_age_found = max(age_distribution.keys())
            avg_age = sum(age * count for age, count in age_distribution.items()) / sum(age_distribution.values())
            
            print(f"   • Min age: {min_age_found}")
            print(f"   • Max age: {max_age_found}")
            print(f"   • Average age: {avg_age:.1f}")
            
            # Top 5 âges
            print(f"\n   Top 5 Ages:")
            for age, count in age_distribution.most_common(5):
                percentage = (count / valid_count) * 100
                print(f"   • Age {age}: {count:,} ({percentage:.2f}%)")
        
        # ====================================================================
        # STEP 5: Compter les anomalies d'âge
        # ====================================================================
        
        print(f"\n📊 Counting age anomalies...")
        
        under_min_age_count = sum(
            1 for error in validation_errors.elements()
            if "below minimum" in error
        )
        
        over_max_age_count = sum(
            1 for error in validation_errors.elements()
            if "exceeds maximum" in error
        )
        
        future_date_count = sum(
            1 for error in validation_errors.elements()
            if "future" in error
        )
        
        print(f"   ✓ Under minimum age ({min_age}): {under_min_age_count:,}")
        print(f"   ✓ Over maximum age ({max_age}): {over_max_age_count:,}")
        print(f"   ✓ Future dates: {future_date_count:,}")
        
        # ====================================================================
        # STEP 6: Calculer la conformité
        # ====================================================================
        
        if non_null_count > 0:
            #The compliante rate should be calculated based on the valid_count and the total number of active records, excluding the anomalies.
            compliance_rate = (valid_count / active_rows_count) * 100
        else:
            compliance_rate = 0.0
        
        # Déterminer le statut
        if compliance_rate >= 95:
            compliance_status = "excellent"
            risk_score = 0.1
        elif compliance_rate >= 90:
            compliance_status = "good"
            risk_score = 0.2
        elif compliance_rate >= 80:
            compliance_status = "fair"
            risk_score = 0.4
        else:
            compliance_status = "poor"
            risk_score = 0.6
        
        # ====================================================================
        # STEP 7: Détecter les anomalies
        # ====================================================================
        
        anomalies = []
        
        if null_count > (active_rows_count * 0.05):
            anomalies.append({
                "type": "high_null_rate",
                "count": null_count,
                "percentage": round((null_count / active_rows_count) * 100, 2),
                "severity": "high"
            })
        
        if invalid_count > (non_null_count * 0.1):
            anomalies.append({
                "type": "invalid_format",
                "count": invalid_count,
                "percentage": round((invalid_count / non_null_count) * 100, 2),
                "severity": "high",
                "details": dict(validation_errors.most_common(3))
            })
        
        if under_min_age_count > (non_null_count * 0.05):
            anomalies.append({
                "type": "under_minimum_age",
                "count": under_min_age_count,
                "percentage": round((under_min_age_count / non_null_count) * 100, 2),
                "severity": "high",
                "min_age": min_age
            })
        
        if over_max_age_count > (non_null_count * 0.05):
            anomalies.append({
                "type": "over_maximum_age",
                "count": over_max_age_count,
                "percentage": round((over_max_age_count / non_null_count) * 100, 2),
                "severity": "medium",
                "max_age": max_age
            })
        
        if future_date_count > 0:
            anomalies.append({
                "type": "future_dates",
                "count": future_date_count,
                "percentage": round((future_date_count / non_null_count) * 100, 2),
                "severity": "high"
            })
        
        if len(format_counts) > 2:
            anomalies.append({
                "type": "multiple_formats",
                "count": len(format_counts),
                "formats": dict(format_counts),
                "severity": "medium",
                "note": "Multiple date formats detected - consider standardization"
            })
        
        # ====================================================================
        # STEP 8: Construire le résultat
        # ====================================================================
        
        analysis_result = {
            "status": "completed",
            "country": country,
            "column_analyzed": dob_column,
            
            # Comptages
            "row_count": active_rows_count,
            "null_count": null_count,
            "non_null_count": non_null_count,
            "valid_count": valid_count,
            "invalid_count": invalid_count,
            
            # Conformité
            "compliance_rate": round(compliance_rate, 2),
            "compliance_status": compliance_status,
            "risk_score": risk_score,
            
            # Formats détectés
            "detected_formats": dict(format_counts),
            "format_count": len(format_counts),
            
            # Distribution des âges
            "age_distribution": dict(age_distribution) if age_distribution else {},
            "age_statistics": {
                "min_age": min(age_distribution.keys()) if age_distribution else None,
                "max_age": max(age_distribution.keys()) if age_distribution else None,
                "avg_age": round(sum(age * count for age, count in age_distribution.items()) / sum(age_distribution.values()), 1) if age_distribution else None,
            },
            
            # Anomalies d'âge
            "age_anomalies": {
                "under_minimum_age": under_min_age_count,
                "over_maximum_age": over_max_age_count,
                "future_dates": future_date_count,
            },
            
            # Erreurs de validation
            "validation_errors": dict(validation_errors.most_common(10)),
            
            # Contrôles
            "controls": {
                "Null or Empty DOB": null_count,
                "Invalid Format": invalid_count,
                "Under Minimum Age": under_min_age_count,
                "Over Maximum Age": over_max_age_count,
                "Future Dates": future_date_count,
            },
            
            # Résumé
            "summary": {
                "total_active_records": active_rows_count,
                "records_with_data": non_null_count,
                "records_with_valid_format": valid_count,
                "records_with_issues": null_count + invalid_count,
                "data_quality_score": round(compliance_rate, 2),
            },
            
            # Anomalies
            "anomalies": anomalies,
        }
        
        state["dob_analysis"] = analysis_result
        
        print(f"\n✅ DOB Analysis Complete")
        print(f"   Compliance: {compliance_rate:.2f}%")
        print(f"   Status: {compliance_status.upper()}")
        print(f"   Risk Score: {risk_score}")
        print(f"   Formats: {len(format_counts)}")
        print(f"   Anomalies: {len(anomalies)}")
        print("=" * 60)
        
        return state
        
    except Exception as e:
        print(f"\n✗ Error during DOB analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        
        state["dob_analysis"] = {
            "status": "error",
            "error": str(e)
        }
        
        print("=" * 60)
        return state

def analyze_city(state: AnalysisAgentState) -> AnalysisAgentState:
    """
    Analyse la colonne ville pour validité et problèmes courants.
    
    Contrôles simples : null, caractères numériques, caractères spéciaux.
    Utilise active_rows_count du state pour éviter les recalculs.
    TOUTES LES REQUÊTES S'EXÉCUTENT UNIQUEMENT SUR LES LIGNES ACTIVES.
    
    Args:
        state: AnalysisAgentState avec file_path, schema_mapping, country, active_rows_count
        
    Returns:
        État mis à jour avec résultats d'analyse ville
    """
    
    print("\n" + "=" * 60)
    print("🏙️ ANALYZING CITY")
    print("=" * 60)
    
    # ✅ Récupérer active_rows_count depuis state
    active_rows_count = state.get("active_rows_count", 0)
    
    # Récupérer la colonne ville
    schema_mapping = state.get("schema_mapping", {})
    city_column = schema_mapping.get("city_column")
    
    if not city_column:
        print("⚠️ No city column mapped - skipping analysis")
        state["city_analysis"] = {
            "status": "skipped",
            "reason": "No city column mapped"
        }
        return state
    
    file_path = state.get("file_path")
    country = state.get("country", "Unknown")
    data = state.get("data", [])
    
    if not file_path and not data:
        print("❌ No file path or data provided")
        state["city_analysis"] = {
            "status": "error",
            "error": "No file path or data provided"
        }
        return state
    
    try:
        from collections import Counter
        import re
        
        print(f"🏙️ Analyzing city column: '{city_column}'")
        print(f"🌍 Country: {country}")
        print(f"✓ Active rows: {active_rows_count:,}")
        
        if active_rows_count == 0:
            print("⚠️ No active records found")
            state["city_analysis"] = {
                "status": "warning",
                "row_count": 0,
                "warning": "No active records found"
            }
            return state
        
        # ====================================================================
        # STEP 1: Charger les données
        # ====================================================================
        
        print(f"\n📊 Extracting city values...")
        
        if data:
            # Données en mémoire
            city_values = [
                str(record.get(city_column, "")).strip()
                for record in data
            ]
        else:
            # Lire depuis fichier
            con = duckdb.connect()
            city_values = ChunkedColumn(
                file_path, city_column,
                delimiter=state.get("detected_delimiter") or ",",
                active_status_column=state.get("active_status_column"),
                active_status_values=state.get("active_status_values"),
                expected_length=active_rows_count,
            )
            con.close()
        
        print(f"   ✓ Total records: {active_rows_count:,}")
        
        # ====================================================================
        # STEP 2: Analyser les villes
        # ====================================================================
        
        print(f"\n📊 Analyzing city values...")
        
        # Compteurs
        null_count = sum(1 for city in city_values if not city or city == "")
        non_null_count = active_rows_count - null_count
        
        print(f"   ✓ Null/empty: {null_count:,}")
        print(f"   ✓ Non-null: {non_null_count:,}")
        
        if non_null_count == 0:
            print("⚠️ No non-null city values found")
            state["city_analysis"] = {
                "status": "warning",
                "row_count": active_rows_count,
                "null_count": null_count,
                "warning": "No non-null city values found"
            }
            return state
        
        # ====================================================================
        # STEP 3: Appliquer les contrôles
        # ====================================================================
        
        print(f"\n📊 Applying validation controls...")
        
        # Compteurs pour les contrôles
        numeric_city_count = 0
        special_char_city_count = 0
        length_distribution = Counter()
        city_frequency = Counter()
        
        for city in city_values:
            if not city:
                continue
            
            # Distribution des longueurs
            length_distribution[len(city)] += 1
            
            # Fréquence des villes
            city_frequency[city.upper()] += 1
            
            # Contrôle 1: Contient des chiffres
            if re.search(r'\d', city):
                numeric_city_count += 1
            
            # Contrôle 2: Contient des caractères spéciaux (sauf espaces, tirets, apostrophes)
            if not re.match(r"^[a-zA-Z\s\-'àâäéèêëïîôöùûüœæçÀÂÄÉÈÊËÏÎÔÖÙÛÜŒÆÇ]+$", city):
                special_char_city_count += 1
        
        print(f"   ✓ Null or empty: {null_count:,}")
        print(f"   ✓ With numeric characters: {numeric_city_count:,}")
        print(f"   ✓ With special characters: {special_char_city_count:,}")
        
        # ====================================================================
        # STEP 4: Calculer les villes valides
        # ====================================================================
        
        # Valides = pas de problèmes détectés
        invalid_count = null_count + numeric_city_count + special_char_city_count
        valid_count = active_rows_count - invalid_count
        
        print(f"\n📊 Validation Results:")
        print(f"   ✓ Valid cities: {valid_count:,}")
        print(f"   ✓ Invalid cities: {invalid_count:,}")
        
        # ====================================================================
        # STEP 5: Analyser la distribution des longueurs
        # ====================================================================
        
        print(f"\n📊 Length Distribution (Top 10):")
        for length, count in sorted(length_distribution.items(), key=lambda x: x[1], reverse=True)[:10]:
            percentage = (count / non_null_count) * 100
            print(f"   • {length} chars: {count:,} ({percentage:.2f}%)")
        
        if length_distribution:
            avg_length = sum(length * count for length, count in length_distribution.items()) / non_null_count
            min_length = min(length_distribution.keys())
            max_length = max(length_distribution.keys())
        else:
            avg_length = 0
            min_length = 0
            max_length = 0
        
        print(f"   • Min length: {min_length}")
        print(f"   • Max length: {max_length}")
        print(f"   • Average length: {avg_length:.1f}")
        
        # ====================================================================
        # STEP 6: Analyser les villes les plus fréquentes
        # ====================================================================
        
        print(f"\n📊 Top 10 Cities:")
        for city, count in city_frequency.most_common(10):
            percentage = (count / non_null_count) * 100
            print(f"   • {city}: {count:,} ({percentage:.2f}%)")
        
        # Compter les villes uniques
        unique_cities_count = len(city_frequency)
        
        # ====================================================================
        # STEP 7: Calculer la conformité
        # ====================================================================
        
        if active_rows_count > 0:
            compliance_rate = (valid_count / active_rows_count) * 100
        else:
            compliance_rate = 0.0
        
        # Déterminer le statut
        if compliance_rate >= 95:
            compliance_status = "excellent"
            risk_score = 0.1
        elif compliance_rate >= 90:
            compliance_status = "good"
            risk_score = 0.2
        elif compliance_rate >= 80:
            compliance_status = "fair"
            risk_score = 0.4
        else:
            compliance_status = "poor"
            risk_score = 0.6
        
        # ====================================================================
        # STEP 8: Détecter les anomalies
        # ====================================================================
        
        anomalies = []
        
        if null_count > (active_rows_count * 0.05):
            anomalies.append({
                "type": "high_null_rate",
                "count": null_count,
                "percentage": round((null_count / active_rows_count) * 100, 2),
                "severity": "medium"
            })
        
        if numeric_city_count > (non_null_count * 0.1):
            anomalies.append({
                "type": "numeric_characters",
                "count": numeric_city_count,
                "percentage": round((numeric_city_count / non_null_count) * 100, 2),
                "severity": "medium"
            })
        
        if special_char_city_count > (non_null_count * 0.1):
            anomalies.append({
                "type": "special_characters",
                "count": special_char_city_count,
                "percentage": round((special_char_city_count / non_null_count) * 100, 2),
                "severity": "low"
            })
        
        # Vérifier si une ville domine trop
        if city_frequency:
            top_city_count = city_frequency.most_common(1)[0][1]
            top_city_percentage = (top_city_count / non_null_count) * 100
            if top_city_percentage > 50:
                anomalies.append({
                    "type": "dominant_city",
                    "city": city_frequency.most_common(1)[0][0],
                    "count": top_city_count,
                    "percentage": round(top_city_percentage, 2),
                    "severity": "low",
                    "note": "One city represents more than 50% of records"
                })
        
        # ====================================================================
        # STEP 9: Construire le résultat
        # ====================================================================
        
        analysis_result = {
            "status": "completed",
            "country": country,
            "column_analyzed": city_column,
            
            # Comptages
            "row_count": active_rows_count,
            "null_count": null_count,
            "non_null_count": non_null_count,
            "valid_count": valid_count,
            "invalid_count": invalid_count,
            
            # Villes
            "unique_cities_count": unique_cities_count,
            
            # Conformité
            "compliance_rate": round(compliance_rate, 2),
            "compliance_status": compliance_status,
            "risk_score": risk_score,
            
            # Longueurs
            "length_statistics": {
                "min_length": min_length,
                "max_length": max_length,
                "avg_length": round(avg_length, 1),
            },
            
            # Top villes
            "top_cities": dict(city_frequency.most_common(10)),
            
            # Contrôles
            "controls": {
                "Null or Empty Cities": null_count,
                "City Names with Numeric Characters": numeric_city_count,
                "City Names with Special Characters": special_char_city_count,
            },
            
            # Résumé
            "summary": {
                "total_active_records": active_rows_count,
                "records_with_data": non_null_count,
                "records_with_valid_format": valid_count,
                "records_with_issues": invalid_count,
                "data_quality_score": round(compliance_rate, 2),
            },
            
            # Anomalies
            "anomalies": anomalies,
        }
        
        state["city_analysis"] = analysis_result
        
        print(f"\n✅ City Analysis Complete")
        print(f"   Compliance: {compliance_rate:.2f}%")
        print(f"   Status: {compliance_status.upper()}")
        print(f"   Risk Score: {risk_score}")
        print(f"   Unique Cities: {unique_cities_count:,}")
        print(f"   Anomalies: {len(anomalies)}")
        print("=" * 60)
        
        return state
        
    except Exception as e:
        print(f"\n✗ Error during city analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        
        state["city_analysis"] = {
            "status": "error",
            "error": str(e)
        }
        
        print("=" * 60)
        return state

def analyze_address(state: AnalysisAgentState) -> AnalysisAgentState:
    """
    Analyse la colonne adresse pour validité et problèmes courants.
    
    Contrôles simples : null, numériques uniquement, trop court, caractères répétés.
    Gère les adresses multiples (concaténation).
    Utilise active_rows_count du state pour éviter les recalculs.
    TOUTES LES REQUÊTES S'EXÉCUTENT UNIQUEMENT SUR LES LIGNES ACTIVES.
    
    Args:
        state: AnalysisAgentState avec file_path, schema_mapping, country, active_rows_count
        
    Returns:
        État mis à jour avec résultats d'analyse adresse
    """
    
    print("\n" + "=" * 60)
    print("📍 ANALYZING ADDRESS")
    print("=" * 60)

    # ✅ Récupérer active_rows_count depuis state
    active_rows_count = state.get("active_rows_count", 0)
    
    # Récupérer la colonne adresse
    schema_mapping = state.get("schema_mapping", {})
    address_column = schema_mapping.get("address_column")
    
    if not address_column:
        print("⚠️ No address column mapped - skipping analysis")
        state["address_analysis"] = {
            "status": "skipped",
            "reason": "No address column mapped"
        }
        return state
    
    file_path = state.get("file_path")
    country = state.get("country", "Unknown")
    data = state.get("data", [])
    
    if not file_path and not data:
        print("❌ No file path or data provided")
        state["address_analysis"] = {
            "status": "error",
            "error": "No file path or data provided"
        }
        return state
    
    try:
        from collections import Counter
        import re
        
        print(f"📍 Analyzing address column: '{address_column}'")
        print(f"🌍 Country: {country}")
        print(f"✓ Active rows: {active_rows_count:,}")
        
        if active_rows_count == 0:
            print("⚠️ No active records found")
            state["address_analysis"] = {
                "status": "warning",
                "row_count": 0,
                "warning": "No active records found"
            }
            return state
        
        # ====================================================================
        # STEP 1: Charger les données
        # ====================================================================
        
        print(f"\n📊 Extracting address values...")
        
        if data:
            # Données en mémoire
            address_values = [
                str(record.get(address_column, "")).strip()
                for record in data
            ]
        else:
            # Lire depuis fichier
            con = duckdb.connect()
            address_values = ChunkedColumn(
                file_path, address_column,
                delimiter=state.get("detected_delimiter") or ",",
                active_status_column=state.get("active_status_column"),
                active_status_values=state.get("active_status_values"),
                expected_length=active_rows_count,
            )
            con.close()
        
        print(f"   ✓ Total records: {active_rows_count:,}")
        
        # ====================================================================
        # STEP 2: Analyser les adresses
        # ====================================================================
        
        print(f"\n📊 Analyzing address values...")
        
        # Compteurs
        null_count = sum(1 for addr in address_values if not addr or addr == "")
        non_null_count = active_rows_count - null_count
        
        print(f"   ✓ Null/empty: {null_count:,}")
        print(f"   ✓ Non-null: {non_null_count:,}")
        
        if non_null_count == 0:
            print("⚠️ No non-null address values found")
            state["address_analysis"] = {
                "status": "warning",
                "row_count": active_rows_count,
                "null_count": null_count,
                "warning": "No non-null address values found"
            }
            return state
        
        # ====================================================================
        # STEP 3: Appliquer les contrôles
        # ====================================================================
        
        print(f"\n📊 Applying validation controls...")
        
        # Compteurs pour les contrôles
        numeric_address_count = 0
        short_address_count = 0
        repeated_char_address_count = 0
        length_distribution = Counter()
        
        for addr in address_values:
            if not addr:
                continue
            
            # Distribution des longueurs
            length_distribution[len(addr)] += 1
            
            # Contrôle 1: Contient uniquement des chiffres
            if re.match(r'^\d+$', addr):
                numeric_address_count += 1
            
            # Contrôle 2: Trop court (moins de 3 caractères)
            if len(addr) < 3:
                short_address_count += 1
            
            # Contrôle 3: Caractères répétés (aaa, 111, etc.)
            if re.match(r'^([a-zA-Z0-9])\1{2,}$', addr):
                repeated_char_address_count += 1
        
        print(f"   ✓ Null or empty: {null_count:,}")
        print(f"   ✓ With only numeric characters: {numeric_address_count:,}")
        print(f"   ✓ Less than 3 characters: {short_address_count:,}")
        print(f"   ✓ With repeated characters: {repeated_char_address_count:,}")
        
        # ====================================================================
        # STEP 4: Calculer les adresses valides
        # ====================================================================
        
        # Valides = pas de problèmes détectés
        invalid_count = null_count + numeric_address_count + short_address_count + repeated_char_address_count
        valid_count = active_rows_count - invalid_count
        
        print(f"\n📊 Validation Results:")
        print(f"   ✓ Valid addresses: {valid_count:,}")
        print(f"   ✓ Invalid addresses: {invalid_count:,}")
        
        # ====================================================================
        # STEP 5: Analyser la distribution des longueurs
        # ====================================================================
        
        print(f"\n📊 Length Distribution (Top 10):")
        for length, count in sorted(length_distribution.items(), key=lambda x: x[1], reverse=True)[:10]:
            percentage = (count / non_null_count) * 100
            print(f"   • {length} chars: {count:,} ({percentage:.2f}%)")
        
        if length_distribution:
            avg_length = sum(length * count for length, count in length_distribution.items()) / non_null_count
            min_length = min(length_distribution.keys())
            max_length = max(length_distribution.keys())
        else:
            avg_length = 0
            min_length = 0
            max_length = 0
        
        print(f"   • Min length: {min_length}")
        print(f"   • Max length: {max_length}")
        print(f"   • Average length: {avg_length:.1f}")
        
        # ====================================================================
        # STEP 6: Calculer la conformité
        # ====================================================================
        
        if active_rows_count > 0:
            compliance_rate = (valid_count / active_rows_count) * 100
        else:
            compliance_rate = 0.0
        
        # Déterminer le statut
        if compliance_rate >= 95:
            compliance_status = "excellent"
            risk_score = 0.1
        elif compliance_rate >= 90:
            compliance_status = "good"
            risk_score = 0.2
        elif compliance_rate >= 80:
            compliance_status = "fair"
            risk_score = 0.4
        else:
            compliance_status = "poor"
            risk_score = 0.6
        
        # ====================================================================
        # STEP 7: Détecter les anomalies
        # ====================================================================
        
        anomalies = []
        
        if null_count > (active_rows_count * 0.05):
            anomalies.append({
                "type": "high_null_rate",
                "count": null_count,
                "percentage": round((null_count / active_rows_count) * 100, 2),
                "severity": "medium"
            })
        
        if numeric_address_count > (non_null_count * 0.05):
            anomalies.append({
                "type": "numeric_only_addresses",
                "count": numeric_address_count,
                "percentage": round((numeric_address_count / non_null_count) * 100, 2),
                "severity": "high"
            })
        
        if short_address_count > (non_null_count * 0.1):
            anomalies.append({
                "type": "short_addresses",
                "count": short_address_count,
                "percentage": round((short_address_count / non_null_count) * 100, 2),
                "severity": "medium"
            })
        
        if repeated_char_address_count > (non_null_count * 0.05):
            anomalies.append({
                "type": "repeated_characters",
                "count": repeated_char_address_count,
                "percentage": round((repeated_char_address_count / non_null_count) * 100, 2),
                "severity": "high"
            })
        
        # ====================================================================
        # STEP 8: Construire le résultat
        # ====================================================================
        
        analysis_result = {
            "status": "completed",
            "country": country,
            "column_analyzed": address_column,
            
            # Comptages
            "row_count": active_rows_count,
            "null_count": null_count,
            "non_null_count": non_null_count,
            "valid_count": valid_count,
            "invalid_count": invalid_count,
            
            # Conformité
            "compliance_rate": round(compliance_rate, 2),
            "compliance_status": compliance_status,
            "risk_score": risk_score,
            
            # Longueurs
            "length_statistics": {
                "min_length": min_length,
                "max_length": max_length,
                "avg_length": round(avg_length, 1),
            },
            
            # Contrôles
            "controls": {
                "Null or Empty Address": null_count,
                "Address with Only Numeric Characters": numeric_address_count,
                "Address Less Than 3 Characters": short_address_count,
                "Address with Repeated Characters": repeated_char_address_count,
            },
            
            # Résumé
            "summary": {
                "total_active_records": active_rows_count,
                "records_with_data": non_null_count,
                "records_with_valid_format": valid_count,
                "records_with_issues": invalid_count,
                "data_quality_score": round(compliance_rate, 2),
            },
            
            # Anomalies
            "anomalies": anomalies,
        }
        
        state["address_analysis"] = analysis_result
        
        print(f"\n✅ Address Analysis Complete")
        print(f"   Compliance: {compliance_rate:.2f}%")
        print(f"   Status: {compliance_status.upper()}")
        print(f"   Risk Score: {risk_score}")
        print(f"   Anomalies: {len(anomalies)}")
        print("=" * 60)
        
        return state
        
    except Exception as e:
        print(f"\n✗ Error during address analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        
        state["address_analysis"] = {
            "status": "error",
            "error": str(e)
        }
        
        print("=" * 60)
        return state