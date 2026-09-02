// Types pour l'upload et l'analyse KYC — alignés sur les payloads réels du backend

export interface FileInfo {
  fileName: string;
  fileSize: number;
  fileType: 'csv' | 'xlsx' | 'xls';
  delimiter?: string;
  rowCount: number;
  preview: string[][];
}

// Réponse de POST /files/upload
export interface UploadResult {
  fileId: string;
  fileName: string;
  storedFileName: string;
  filePath: string;
  sizeBytes: number;
  extension: string;
  status: string;
  createdAt: string;
  prepState: PrepState;
}

// prep_state transmis à POST /orchestrator/prep
export interface PrepState {
  thread_id: string;
  user_id: string;
  file_id: string;
  file_name: string;
  file_path: string;
  prep_status: 'uploaded' | 'success' | 'error';
  prep_error: string | null;
}

// Réponse de POST /orchestrator/prep
export interface PrepResult {
  fileId: string;
  prepStatus: 'success' | 'error';
  prepError: string | null;
  datasetProfile?: {
    rowCount: number;
    columnCount: number;
    columns: string[];
    dtypes: Record<string, string>;
    missingRatioByColumn: Record<string, number>;
    sampleRows: Record<string, unknown>[];
  };
  prepMeta?: {
    engineUsed: string;
    fileSizeMb: number;
    csvDelimiterUsed: string | null;
  };
}

// Réponse de POST /orchestrator/schema-detect
export interface SchemaDetection {
  fileId: string;
  isOrangeMoney: boolean;
  confidenceScore: number;
  matchedRequiredColumns: string[];
  missingRequiredColumns: string[];
  allDetectedColumns: string[];
  mappingStatus: 'auto_detected' | 'pending_user_input' | 'validated' | 'error';
  // Pré-rempli uniquement si Orange Money détecté
  selectedColumns: KYCColumnMapping;
  columnReasoning: Partial<Record<keyof KYCColumnMapping, string>>; // NOUVEAU
}

export interface KYCColumnMapping {
  nomColumn?: string;
  prenomColumn?: string;
  msisdnColumn?: string;
  idTypeColumn?: string;
  idNumberColumn?: string;
  dobColumn?: string;
  addressColumn?: string;
  cityColumn?: string;
  statusColumn?: string;
}

// Réponse de POST /orchestrator/country-detect
export interface CountryDetection {
  fileId: string;
  detectedCountry: string;
  confidence: number;
  reasoning: string;
  status: 'completed' | 'error';
}

// Réponse de POST /orchestrator/active-lines-detect
export interface ActiveLinesDetection {
  totalLines: number;
  activeLines: number;
  activePercentage: number;
  statusColumn: string | null;
  statusValues: string[];
}

// --- Résultat d'analyse : agrégé PAR CHAMP, pas par ligne ---

export type Severity = 'info' | 'warning' | 'error';
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface FieldAnomaly {
  type: string;
  count: number;
  percentage: number;
  severity: Severity;
}

export interface FieldAnalysisResult {
  status: 'completed' | 'skipped' | 'error' | 'warning';
  complianceRate?: number;
  riskScore?: number;
  rowCount?: number;
  nullCount?: number;
  validCount?: number;
  nonNullCount?: number;
  anomalies?: FieldAnomaly[];
  columnAnalyzed?: string;
  warning?: string;
  reason?: string;
  error?: string;
  // Champs spécifiques par type d'analyse (présents selon le champ KYC)
  formatDetails?: {
    expectedLength?: number | null;
    expectedFormat?: string | null;
    pattern?: string | null;
    matchingLengthCount?: number;
    matchingLengthPercentage?: number;
    numericCount?: number;
    numericPercentage?: number;
  };
  idTypeDistribution?: Record<string, number>;
  dominantIdType?: string;
  dominantPercentage?: number;
  distinctIdTypesCount?: number;
  validationMode?: 'single_type' | 'any_type';
  matchedTypeDistribution?: Record<string, number> | null;
  duplicates?: {
    uniqueValidIds: number;
    duplicateIdsCount: number;
    duplicateRecordsCount: number;
    duplicatePercentage: number;
    topDuplicates: Record<string, number>;
  };
  suspiciousPatterns?: {
    sequential: number;
    repeated: number;
    allZeros: number;
    allNines: number;
  };
  detectedFormats?: Record<string, number>;
  ageStatistics?: {
    minAge: number | null;
    maxAge: number | null;
    avgAge: number | null;
  };
  ageAnomalies?: {
    underMinimumAge: number;
    overMaximumAge: number;
    futureDates: number;
  };
  topCities?: Record<string, number>;
  uniqueCitiesCount?: number;
  lengthStatistics?: {
    minLength: number;
    maxLength: number;
    avgLength: number;
  };
  [key: string]: unknown;
}
// Réponse de POST /orchestrator/analyze
export interface KYCAnalysisResult {
  fileId: string;
  analysisStatus: 'completed' | 'error';
  overallRiskScore: number;
  overallRiskLevel: RiskLevel;
  overallComplianceRate: number;
  activeRowsCount: number;
  totalAnomalies: number;
  anomaliesByField: Record<string, FieldAnomaly[]>;
  criticalFields: Array<{ field: string; anomaly: string; count: number; percentage: number }>;
  executiveSummary: {
    overallDataQuality: 'EXCELLENT' | 'GOOD' | 'FAIR' | 'POOR';
    riskAssessment: RiskLevel;
    fieldsWithIssues: number;
    criticalIssues: number;
    recommendation: string;
  };
  detailedResults: Record<string, FieldAnalysisResult>;
}

// Anomalie "aplatie" telle que renvoyée par GET /orchestrator/report/{file_id}
export interface ReportAnomaly {
  field: string;
  type: string;
  count: number;
  percentage: number;
  severity: Severity;
}

// Réponse de GET /orchestrator/report/{file_id}
export interface AnalysisReport {
  fileId: string;
  fileName: string | null;
  detectedCountry: string | null;
  isOrangeMoney: boolean | null;
  analysisStatus: string;
  overallRiskScore: number;
  overallRiskLevel: RiskLevel;
  overallComplianceRate: number;
  executiveSummary: KYCAnalysisResult['executiveSummary'];
  anomalies: ReportAnomaly[];
  summary: {
    totalAnomalies: number;
    criticalAnomalies: number;
    warningAnomalies: number;
    infoAnomalies: number;
    totalAnomalyOccurrences: number;
    affectedRows: number;
    complianceScore: number;
  };
  fieldResults: Record<string, FieldAnalysisResult>;
  analyzedAt: string | null;
}

// Élément de GET /orchestrator/analyses
export interface AnalysisHistoryItem {
  id: string;
  fileId: string;
  fileName: string | null;
  fileType: string | null;
  country: string | null;
  riskScore: number | null;
  riskLevel: RiskLevel | null;
  complianceRate: number | null;
  rowsAnalyzed: number | null;
  createdAt: string | null;
}

export interface AnalysisHistory {
  analyses: AnalysisHistoryItem[];
  total: number;
  page: number;
  pageSize: number;
}