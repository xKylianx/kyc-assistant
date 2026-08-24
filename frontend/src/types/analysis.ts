export interface PrepDatasetProfile {
  row_count: number;
  column_count: number;
  columns: string[];
  dtypes: Record<string, string>;
  missing_ratio_by_column: Record<string, number>;
  sample_rows: Record<string, unknown>[];
}

export interface PrepState {
  thread_id?: string | null;
  user_id?: string | null;
  file_id: string;
  file_name: string;
  file_path: string;
  prep_status: 'uploaded' | 'success' | 'error';
  prep_error?: string | null;
  dataset_profile?: PrepDatasetProfile;
  prep_meta?: Record<string, unknown>;
  prepared_at?: string;
}

export interface FileInfo {
  fileName: string;
  fileSize: number;
  fileType: 'csv' | 'xlsx' | 'xls';
  delimiter?: string;
  rowCount: number;
  preview: string[][];
}

export interface SchemaDetection {
  fileId: string;
  fileInfo: FileInfo;
  detectedCountry: string;
  detectedSchema: 'orange_money' | 'other';
  availableColumns: string[];
  selectedColumns: {
    nomColumn?: string;
    prenomColumn?: string;
    msisdnColumn?: string;
    idTypeColumn?: string;
    idNumberColumn?: string;
    dobColumn?: string;
    addressColumn?: string;
    cityColumn?: string;
    statusColumn?: string;
    [key: string]: string | undefined;
  };
}

export interface KYCAnomaly {
  id: string;
  row: number;
  column: string;
  value: string;
  anomalyType: string;
  description: string;
  severity: 'info' | 'warning' | 'error';
  confidence: number;
}

export interface KYCAnalysisResult {
  fileId: string;
  fileName: string;
  totalRows: number;
  analyzedRows: number;
  anomalies: KYCAnomaly[];
  riskScore: number;
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  detectedCountry: string;
  detectedSchema: 'orange_money' | 'other';
  analysisTime: number;
  createdAt: string;
}

export interface AnalysisReport {
  analysis: KYCAnalysisResult;
  summary: {
    totalAnomalies: number;
    criticalAnomalies: number;
    warningAnomalies: number;
    infoAnomalies: number;
    affectedRows: number;
    complianceScore: number;
  };
}
