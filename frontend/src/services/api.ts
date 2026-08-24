import { FileInfo, SchemaDetection, KYCAnalysisResult, AnalysisReport, PrepState } from '../types/analysis';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === 'true';

async function parseError(response: Response, fallback: string): Promise<Error> {
  const text = await response.text();
  try {
    const body = JSON.parse(text);
    return new Error(body?.error?.message || body?.detail || fallback);
  } catch {
    return new Error(text || fallback);
  }
}

export class ApiService {
  static async uploadFile(file: File): Promise<FileInfo & { fileId: string; prepState: PrepState }> {
    if (USE_MOCK) {
      const prepState: PrepState = {
        thread_id: 'mock-thread', user_id: null, file_id: 'mock-file-id-123',
        file_name: file.name, file_path: '/mock/' + file.name, prep_status: 'uploaded', prep_error: null,
      };
      return { fileId: prepState.file_id, fileName: file.name, fileSize: file.size,
        fileType: (file.name.split('.').pop() || 'csv') as 'csv' | 'xlsx' | 'xls',
        delimiter: ',', rowCount: 0, preview: [], prepState };
    }
    const formData = new FormData();
    formData.append('file', file);
    const response = await fetch(API_BASE_URL + '/files/upload', { method: 'POST', body: formData });
    if (!response.ok) throw await parseError(response, "Erreur lors de l'upload");
    const data = await response.json();
    const saved = data.file;
    const prepState = data.prep_state as PrepState;
    return { fileId: saved.file_id, fileName: saved.file_name, fileSize: saved.size_bytes,
      fileType: saved.extension.replace('.', '') as 'csv' | 'xlsx' | 'xls',
      delimiter: saved.detected_delimiter || undefined, rowCount: 0, preview: [], prepState };
  }

  static async runPrep(prepState: PrepState): Promise<PrepState> {
    if (USE_MOCK) {
      return { ...prepState, prep_status: 'success',
        dataset_profile: { row_count: 1250, column_count: 9,
          columns: ['Nom', 'Prénom', 'MSISDN', 'ID Type', 'ID Number', 'DOB', 'Address', 'City', 'Status'],
          dtypes: {}, missing_ratio_by_column: {},
          sample_rows: [
            { Nom: 'Doe', Prénom: 'John', MSISDN: '+33612345678', 'ID Type': 'Passport', 'ID Number': 'AB123456', DOB: '1990-05-15', Address: '123 Rue de Paris', City: 'Paris', Status: 'Active' },
            { Nom: 'Smith', Prénom: 'Jane', MSISDN: '+33687654321', 'ID Type': 'ID Card', 'ID Number': 'CD789012', DOB: '1985-08-22', Address: '456 Avenue Lyon', City: 'Lyon', Status: 'Active' },
          ] } };
    }
    const response = await fetch(API_BASE_URL + '/orchestrator/prep', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prep_state: prepState }),
    });
    if (!response.ok) throw await parseError(response, 'Erreur lors de la préparation du fichier');
    const data = await response.json();
    return data.data.prep_state as PrepState;
  }

  static async detectSchema(fileId: string): Promise<SchemaDetection> {
    if (USE_MOCK) {
      const columns = ['Nom', 'Prénom', 'MSISDN', 'ID Type', 'ID Number', 'DOB', 'Address', 'City', 'Status'];
      return { fileId, fileInfo: { fileName: 'data.csv', fileSize: 1024000, fileType: 'csv', delimiter: ',', rowCount: 1250, preview: [] },
        detectedCountry: 'Unknown', detectedSchema: 'orange_money', availableColumns: columns,
        selectedColumns: { nomColumn: 'Nom', prenomColumn: 'Prénom', msisdnColumn: 'MSISDN', idTypeColumn: 'ID Type', idNumberColumn: 'ID Number', dobColumn: 'DOB', addressColumn: 'Address', cityColumn: 'City', statusColumn: 'Status' } };
    }
    const response = await fetch(API_BASE_URL + '/orchestrator/schema-detect?file_id=' + encodeURIComponent(fileId), { method: 'POST' });
    if (!response.ok) throw await parseError(response, 'Erreur lors de la détection du schéma');
    const data = await response.json();
    return { fileId,
      fileInfo: { fileName: data.file_name || 'data.csv', fileSize: data.file_size_bytes || 0,
        fileType: (data.extension || 'csv').replace('.', '') as 'csv' | 'xlsx' | 'xls',
        delimiter: data.detected_delimiter || ',', rowCount: data.row_count || 0, preview: [] },
      detectedCountry: data.detected_country || 'Unknown',
      detectedSchema: data.is_orange_money ? 'orange_money' : 'other',
      availableColumns: data.all_detected_columns || [],
      selectedColumns: { nomColumn: data.nom_column, prenomColumn: data.prenom_column, msisdnColumn: data.msisdn_column,
        idTypeColumn: data.id_type_column, idNumberColumn: data.id_number_column, dobColumn: data.dob_column,
        addressColumn: data.address_column, cityColumn: data.city_column, statusColumn: data.status_column } };
  }

  static async validateSchema(fileId: string, selectedColumns: Record<string, string>): Promise<void> {
    const params = new URLSearchParams({ file_id: fileId });
    const mapping: Record<string, string | undefined> = {
      nom_column: selectedColumns.nomColumn, prenom_column: selectedColumns.prenomColumn, msisdn_column: selectedColumns.msisdnColumn,
      dob_column: selectedColumns.dobColumn, id_type_column: selectedColumns.idTypeColumn, id_number_column: selectedColumns.idNumberColumn,
      status_column: selectedColumns.statusColumn, address_column: selectedColumns.addressColumn, city_column: selectedColumns.cityColumn,
    };
    Object.entries(mapping).forEach(([key, value]) => params.set(key, value || ''));
    if (USE_MOCK) return;
    const response = await fetch(API_BASE_URL + '/orchestrator/validate-schema?' + params.toString(), { method: 'POST' });
    if (!response.ok) throw await parseError(response, 'Erreur lors de la validation du schéma');
  }

  static async detectCountry(fileId: string): Promise<{ country: string; confidence?: number }> {
    if (USE_MOCK) return { country: 'FR', confidence: 0.99 };
    const response = await fetch(API_BASE_URL + '/orchestrator/country-detect?file_id=' + encodeURIComponent(fileId), { method: 'POST' });
    if (!response.ok) throw await parseError(response, 'Erreur lors de la détection du pays');
    const data = await response.json();
    return { country: data.detected_country || 'Unknown', confidence: data.country_detection_confidence };
  }

  static async validateCountry(fileId: string, country: string): Promise<void> {
    if (USE_MOCK) return;
    const params = new URLSearchParams({ file_id: fileId, country });
    const response = await fetch(API_BASE_URL + '/orchestrator/validate-country?' + params.toString(), { method: 'POST' });
    if (!response.ok) throw await parseError(response, 'Erreur lors de la validation du pays');
  }

  static async detectActiveLines(fileId: string) {
    if (USE_MOCK) return { totalLines: 1250, activeLines: 1000, activePercentage: 80, statusColumn: 'Status', statusValues: ['Active'] };
    const response = await fetch(API_BASE_URL + '/orchestrator/active-lines-detect?file_id=' + encodeURIComponent(fileId), { method: 'POST' });
    if (!response.ok) throw await parseError(response, 'Erreur lors de la détection des lignes actives');
    const data = await response.json();
    return { totalLines: data.total_lines_count || 0, activeLines: data.active_lines_count || 0,
      activePercentage: data.active_lines_percentage || 0, statusColumn: data.active_status_column || '',
      statusValues: data.active_status_values || [] };
  }

  static async analyzeKYC(fileId: string): Promise<KYCAnalysisResult> {
    if (USE_MOCK) return { fileId, fileName: 'data.csv', totalRows: 1250, analyzedRows: 1000, anomalies: [],
      riskScore: 35, riskLevel: 'MEDIUM', detectedCountry: 'FR', detectedSchema: 'orange_money',
      analysisTime: 1, createdAt: new Date().toISOString() };
    const startedAt = performance.now();
    const response = await fetch(API_BASE_URL + '/orchestrator/analyze?file_id=' + encodeURIComponent(fileId), { method: 'POST' });
    if (!response.ok) throw await parseError(response, "Erreur lors de l'analyse KYC");
    const data = await response.json();
    return { fileId, fileName: data.file_name || 'data.csv', totalRows: data.total_lines_count || data.active_rows_count || 0,
      analyzedRows: data.active_rows_count || 0, anomalies: flattenAnomalies(data.anomalies_by_field || {}),
      riskScore: Number(data.overall_risk_score || 0), riskLevel: data.overall_risk_level || 'LOW',
      detectedCountry: data.country || 'Unknown', detectedSchema: data.is_orange_money ? 'orange_money' : 'other',
      analysisTime: Math.round((performance.now() - startedAt) / 100) / 10, createdAt: new Date().toISOString() };
  }

  static async generateReport(fileId: string): Promise<AnalysisReport> {
    if (USE_MOCK) return { analysis: { fileId, fileName: 'data.csv', totalRows: 1250, analyzedRows: 1000, anomalies: [],
      riskScore: 35, riskLevel: 'MEDIUM', detectedCountry: 'FR', detectedSchema: 'orange_money', analysisTime: 0, createdAt: new Date().toISOString() },
      summary: { totalAnomalies: 1, criticalAnomalies: 0, warningAnomalies: 1, infoAnomalies: 0, affectedRows: 1, complianceScore: 85 } };
    const response = await fetch(API_BASE_URL + '/orchestrator/report/' + encodeURIComponent(fileId));
    if (!response.ok) throw await parseError(response, 'Erreur lors de la génération du rapport');
    const data = await response.json();
    const anomalies = flattenAnomalies(data.anomalies || {});
    const riskLevel = data.summary?.overall_risk_level || 'LOW';
    const affectedRows = new Set(anomalies.map((item) => item.row).filter((row) => row > 0)).size;
    return { analysis: { fileId, fileName: data.file_name || 'data.csv', totalRows: Number(data.row_count || 0),
      analyzedRows: Number(data.active_lines?.active_lines_count || 0), anomalies,
      riskScore: Number(data.summary?.overall_risk_score || 0), riskLevel: riskLevel === 'UNKNOWN' ? 'LOW' : riskLevel,
      detectedCountry: data.country?.country || 'Unknown', detectedSchema: data.schema?.is_orange_money ? 'orange_money' : 'other',
      analysisTime: 0, createdAt: new Date().toISOString() },
      summary: { totalAnomalies: Number(data.summary?.total_anomalies || anomalies.length),
        criticalAnomalies: anomalies.filter((item) => item.severity === 'error').length,
        warningAnomalies: anomalies.filter((item) => item.severity === 'warning').length,
        infoAnomalies: anomalies.filter((item) => item.severity === 'info').length,
        affectedRows, complianceScore: Number(data.summary?.overall_compliance_rate || 0) } };
  }

  static async exportReportPdf(fileId: string): Promise<Blob> {
    if (USE_MOCK) return new Blob(['Mock PDF Report'], { type: 'application/pdf' });
    const response = await fetch(API_BASE_URL + '/orchestrator/report/' + encodeURIComponent(fileId) + '/export/pdf');
    if (!response.ok) throw await parseError(response, "Erreur lors de l'export PDF");
    return response.blob();
  }
}

function flattenAnomalies(raw: Record<string, unknown>): KYCAnalysisResult['anomalies'] {
  const result: KYCAnalysisResult['anomalies'] = [];
  Object.entries(raw || {}).forEach(([field, value]) => {
    if (!Array.isArray(value)) return;
    value.forEach((item, index) => {
      if (!item || typeof item !== 'object') return;
      const anomaly = item as Record<string, unknown>;
      result.push({ id: String(anomaly.id ?? (field + '-' + index)), row: Number(anomaly.row ?? anomaly.row_number ?? 0),
        column: String(anomaly.column ?? field), value: String(anomaly.value ?? ''),
        anomalyType: String(anomaly.anomaly_type ?? anomaly.type ?? 'anomaly'),
        description: String(anomaly.description ?? anomaly.message ?? 'Anomalie détectée'),
        severity: anomaly.severity === 'error' || anomaly.severity === 'warning' ? anomaly.severity : 'info',
        confidence: Number(anomaly.confidence ?? 0) });
    });
  });
  return result;
}
