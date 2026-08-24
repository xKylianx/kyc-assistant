// Types pour l'upload et l'analyse

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