from typing import TypedDict, Optional, List, Dict, Any

# ============================================================================
# PREP AGENT STATE
# ============================================================================

class PrepAgentState(TypedDict, total=False):
    """
    State for the Prep Agent.
    
    Handles:
    - Data ingestion
    - Schema detection
    - Column selection
    - Country detection
    - Active lines filtering
    """
    
    # ====================================================================
    # FILE INFORMATION
    # ====================================================================
    file_path: Optional[str]
    file_name: Optional[str]
    file_size_bytes: Optional[int]
    file_extension: Optional[str]
    row_count: Optional[int]
    
    # ====================================================================
    # INGESTION
    # ====================================================================
    ingest_status: Optional[str]
    ingest_error: Optional[str]
    csv_dialect: Optional[Dict[str, Any]]
    duckdb_read_options: Optional[Dict[str, Any]]
    
    # ====================================================================
    # SCHEMA DETECTION
    # ====================================================================
    schema_profile: Optional[Dict[str, Any]]
    schema_detection_status: Optional[str]
    confidence_score: Optional[int]
    is_orange_money: Optional[bool]
    matched_required_columns: Optional[List[str]]
    missing_required_columns: Optional[List[str]]
    
    # ====================================================================
    # COLUMN SELECTION
    # ====================================================================
    column_selection_status: Optional[str]  # "pending", "validated"
    
    first_name_columns: Optional[List[str]]
    first_name_columns_reasoning: Optional[str]
    last_name_columns: Optional[List[str]]
    last_name_columns_reasoning: Optional[str]
    msisdn_columns: Optional[List[str]]
    msisdn_columns_reasoning: Optional[str]
    id_type_columns: Optional[List[str]]
    id_type_columns_reasoning: Optional[str]
    id_number_columns: Optional[List[str]]
    id_number_columns_reasoning: Optional[str]
    dob_columns: Optional[List[str]]
    dob_columns_reasoning: Optional[str]
    address_columns: Optional[List[str]]
    address_columns_reasoning: Optional[str]
    city_columns: Optional[List[str]]
    city_columns_reasoning: Optional[str]
    status_columns: Optional[List[str]]
    status_columns_reasoning: Optional[str]

    # ====================================================================
    # COUNTRY DETECTION
    # ====================================================================
    detected_country: Optional[str]
    country_detection_status: Optional[str]
    country_detection_confidence: Optional[float]
    country_detection_reasoning: Optional[str]
    
    # ====================================================================
    # ACTIVE LINES FILTER
    # ====================================================================
    active_lines_count: Optional[int]
    total_lines_count: Optional[int]
    active_lines_percentage: Optional[float]
    active_lines_filter_method: Optional[str]
    active_lines_filter_error: Optional[str]
    active_status_column: Optional[str]          # ← ADD THIS
    active_status_values: Optional[List[str]]    # ← ADD THIS
    active_status_reasoning: Optional[str]       # ← ADD THIS

class AnalysisAgentState(TypedDict, total=False):
    """État pour l'agent d'analyse KYC."""
    
    # Métadonnées
    file_id: str
    thread_id: str
    country: str
    
    # Données
    data: List[Dict[str, Any]]  # Données en mémoire (DataFrame convertie)
    file_path: Optional[str]

    #Nombre de lignes actives
    active_rows_count: int
    
    # Mapping de schéma
    schema_mapping: Dict[str, str]  # {nom_column, prenom_column, msisdn_column, ...}
    
    # Résultats d'analyse par champ
    msisdn_analysis: Dict[str, Any]
    first_name_analysis: Dict[str, Any]
    last_name_analysis: Dict[str, Any]
    id_type_analysis: Dict[str, Any]
    id_number_analysis: Dict[str, Any]
    dob_analysis: Dict[str, Any]
    address_analysis: Dict[str, Any]
    city_analysis: Dict[str, Any]
    
    # Statut global
    analysis_status: str
    analysis_error: Optional[str]


class PlotAgentState(TypedDict, total=False):
    """
    State for the Plot Agent.
    
    This state contains all the analysis results and generates visualizations.
    """
    
    # ====================================================================
    # FILE & CONTEXT INFORMATION (from Analysis Agent)
    # ====================================================================
    file_path: Optional[str]
    file_name: Optional[str]
    row_count: Optional[int]
    csv_dialect: Optional[Dict[str, Any]]
    
    detected_country: Optional[str]
    active_lines_count: Optional[int]
    total_lines_count: Optional[int]
    active_lines_percentage: Optional[float]
    
    # ====================================================================
    # COLUMN SELECTIONS (from Analysis Agent)
    # ====================================================================
    first_name_columns: Optional[List[str]]
    last_name_columns: Optional[List[str]]
    msisdn_columns: Optional[List[str]]
    id_type_columns: Optional[List[str]]
    id_number_columns: Optional[List[str]]
    dob_columns: Optional[List[str]]
    address_columns: Optional[List[str]]
    city_columns: Optional[List[str]]
    
    # ====================================================================
    # ANALYSIS RESULTS (from Analysis Agent)
    # ====================================================================
    
    # MSISDN Analysis
    msisdn_analysis: Optional[Dict[str, Any]]
    msisdn_analysis_status: Optional[str]
    msisdn_analysis_error: Optional[str]
    
    # First Name Analysis
    first_name_analysis: Optional[Dict[str, Any]]
    first_name_analysis_status: Optional[str]
    first_name_analysis_error: Optional[str]
    
    # Last Name Analysis
    last_name_analysis: Optional[Dict[str, Any]]
    last_name_analysis_status: Optional[str]
    last_name_analysis_error: Optional[str]
    
    # ID Type Analysis
    id_type_analysis: Optional[Dict[str, Any]]
    id_type_analysis_status: Optional[str]
    id_type_analysis_error: Optional[str]
    
    # ID Number Analysis
    id_number_analysis: Optional[Dict[str, Any]]
    id_number_analysis_status: Optional[str]
    id_number_analysis_error: Optional[str]
    
    # DOB Analysis
    dob_analysis: Optional[Dict[str, Any]]
    dob_analysis_status: Optional[str]
    dob_analysis_error: Optional[str]
    
    # Address Analysis
    address_analysis: Optional[Dict[str, Any]]
    address_analysis_status: Optional[str]
    address_analysis_error: Optional[str]
    
    # City Analysis
    city_analysis: Optional[Dict[str, Any]]
    city_analysis_status: Optional[str]
    city_analysis_error: Optional[str]
    
    # ====================================================================
    # PLOT GENERATION RESULTS
    # ====================================================================
    
    # MSISDN Plot
    msisdn_plot: Optional[str]  # Base64 encoded image
    msisdn_plot_status: Optional[str]  # "completed", "skipped", "error"
    msisdn_plot_error: Optional[str]
    
    # First Name Plot
    first_name_plot: Optional[str]  # Base64 encoded image
    first_name_plot_status: Optional[str]
    first_name_plot_error: Optional[str]
    
    # Last Name Plot
    last_name_plot: Optional[str]  # Base64 encoded image
    last_name_plot_status: Optional[str]
    last_name_plot_error: Optional[str]
    
    # ID Type Plot
    id_type_plot: Optional[str]  # Base64 encoded image
    id_type_plot_status: Optional[str]
    id_type_plot_error: Optional[str]
    
    # ID Number Plot
    id_number_plot: Optional[str]  # Base64 encoded image
    id_number_plot_status: Optional[str]
    id_number_plot_error: Optional[str]
    
    # DOB Plot
    dob_plot: Optional[str]  # Base64 encoded image
    dob_plot_status: Optional[str]
    dob_plot_error: Optional[str]
    
    # Address Plot
    address_plot: Optional[str]  # Base64 encoded image
    address_plot_status: Optional[str]
    address_plot_error: Optional[str]
    
    # City Plot
    city_plot: Optional[str]  # Base64 encoded image
    city_plot_status: Optional[str]
    city_plot_error: Optional[str]
    
    # ====================================================================
    # COMPLIANCE SUMMARY
    # ====================================================================
    compliance_summary: Optional[Dict[str, Any]]
    compliance_summary_status: Optional[str]  # "completed", "error"
    compliance_summary_error: Optional[str]
    
    # Summary structure:
    # {
    #     "overall_compliance": float,  # 0-100
    #     "field_compliance": {
    #         "📱 MSISDN": float,
    #         "👤 First Name": float,
    #         ...
    #     },
    #     "total_fields_analyzed": int,
    #     "fields_with_issues": int,
    # }
    
    # ====================================================================
    # RECOMMENDATIONS
    # ====================================================================
    recommendations: Optional[List[str]]
    recommendations_status: Optional[str]
    recommendations_error: Optional[str]
    
    # ====================================================================
    # OVERALL STATUS
    # ====================================================================
    plot_agent_status: Optional[str]  # "pending", "in_progress", "completed", "error"
    plot_agent_error: Optional[str]