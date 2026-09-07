import {
  UploadResult,
  PrepState,
  PrepResult,
  SchemaDetection,
  CountryDetection,
  ActiveLinesDetection,
  KYCAnalysisResult,
  AnalysisReport,
  AnalysisHistory,
  KYCColumnMapping,
} from '../types/analysis';

import { normalizeSeverity } from '../lib/kycFields';



const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === 'true';

function normalizeAnomaliesByField(
  raw: Record<string, Array<{ type: string; count: number; percentage: number; severity: string }>>
): Record<string, import('../types/analysis').FieldAnomaly[]> {
  const result: Record<string, import('../types/analysis').FieldAnomaly[]> = {};
  for (const [field, anomalies] of Object.entries(raw)) {
    result[field] = anomalies.map((a) => ({
      type: a.type,
      count: a.count,
      percentage: a.percentage,
      severity: normalizeSeverity(a.severity),
    }));
  }
  return result;
}

function normalizeDetailedResults(
  raw: Record<string, any>
): Record<string, import('../types/analysis').FieldAnalysisResult> {
  const result: Record<string, import('../types/analysis').FieldAnalysisResult> = {};
  for (const [field, data] of Object.entries(raw || {})) {
    if (!data) continue;

    const normalized: import('../types/analysis').FieldAnalysisResult = {
      ...data,
      status: data.status,
      complianceRate: data.compliance_rate,
      riskScore: data.risk_score,
      rowCount: data.row_count,
      nullCount: data.null_count,
      nonNullCount: data.non_null_count,
      validCount: data.valid_count,
      columnAnalyzed: data.column_analyzed,
      warning: data.warning,
      reason: data.reason,
      error: data.error,
    };

    if (data.format_details) {
      normalized.formatDetails = {
        expectedLength: data.format_details.expected_length,
        expectedFormat: data.format_details.expected_format,
        pattern: data.format_details.pattern,
        matchingLengthCount: data.format_details.matching_length_count,
        matchingLengthPercentage: data.format_details.matching_length_percentage,
        numericCount: data.format_details.numeric_count,
        numericPercentage: data.format_details.numeric_percentage,
      };
    }

    if (data.id_type_distribution) {
      normalized.idTypeDistribution = data.id_type_distribution;
      normalized.dominantIdType = data.dominant_id_type;
      normalized.dominantPercentage = data.dominant_percentage;
      normalized.distinctIdTypesCount = data.distinct_id_types_count;
    }

    if (data.validation_mode) {
      normalized.validationMode = data.validation_mode;
      normalized.matchedTypeDistribution = data.matched_type_distribution;
    }

    if (data.duplicates) {
      normalized.duplicates = {
        uniqueValidIds: data.duplicates.unique_valid_ids,
        duplicateIdsCount: data.duplicates.duplicate_ids_count,
        duplicateRecordsCount: data.duplicates.duplicate_records_count,
        duplicatePercentage: data.duplicates.duplicate_percentage,
        topDuplicates: data.duplicates.top_duplicates,
      };
    }

    if (data.suspicious_patterns) {
      normalized.suspiciousPatterns = {
        sequential: data.suspicious_patterns.sequential,
        repeated: data.suspicious_patterns.repeated,
        allZeros: data.suspicious_patterns.all_zeros,
        allNines: data.suspicious_patterns.all_nines,
      };
    }

    if (data.detected_formats) {
      normalized.detectedFormats = data.detected_formats;
    }

    if (data.age_statistics) {
      normalized.ageStatistics = {
        minAge: data.age_statistics.min_age,
        maxAge: data.age_statistics.max_age,
        avgAge: data.age_statistics.avg_age,
      };
    }

    if (data.age_anomalies) {
      normalized.ageAnomalies = {
        underMinimumAge: data.age_anomalies.under_minimum_age,
        overMaximumAge: data.age_anomalies.over_maximum_age,
        futureDates: data.age_anomalies.future_dates,
      };
    }

    if (data.top_cities) {
      normalized.topCities = data.top_cities;
      normalized.uniqueCitiesCount = data.unique_cities_count;
    }

    if (data.length_statistics) {
      normalized.lengthStatistics = {
        minLength: data.length_statistics.min_length,
        maxLength: data.length_statistics.max_length,
        avgLength: data.length_statistics.avg_length,
      };
    }

    if (data.controls) {
      normalized.controls = data.controls;
    }

    if (data.length_distribution) {
      normalized.lengthDistribution = data.length_distribution;
    }

    if (data.age_distribution) {
      normalized.ageDistribution = data.age_distribution;
    }

    if (data.validation_errors) {
      normalized.validationErrors = data.validation_errors;
    }

    result[field] = normalized;
  }
  return result;
}

async function handleResponse<T>(response: Response, context: string): Promise<T> {
  if (!response.ok) {
    const errorText = await response.text();
    let message = `Erreur lors de ${context}`;
    try {
      const parsed = JSON.parse(errorText);
      message = parsed.error?.message || parsed.detail || message;
    } catch {
      // corps non-JSON, on garde le message par défaut
    }
    throw new Error(message);
  }
  return response.json();
}

export class ApiService {
  /**
   * Étape 1 : Uploader le fichier
   * POST /files/upload
   */
    static async uploadFile(
    file: File,
    onProgress?: (percent: number) => void
  ): Promise<UploadResult> {
    if (USE_MOCK) {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      onProgress?.(100);
      const fileId = 'mock-file-id-123';
      return {
        fileId,
        fileName: file.name,
        storedFileName: file.name,
        filePath: `/mock/${file.name}`,
        sizeBytes: file.size,
        extension: file.name.split('.').pop() || 'csv',
        status: 'active',
        createdAt: new Date().toISOString(),
        prepState: {
          thread_id: 'mock-thread',
          user_id: 'mock-user',
          file_id: fileId,
          file_name: file.name,
          file_path: `/mock/${file.name}`,
          prep_status: 'uploaded',
          prep_error: null,
        },
      };
    }

    const formData = new FormData();
    formData.append('file', file);

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable && onProgress) {
          onProgress(Math.round((event.loaded / event.total) * 100));
        }
      };

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const data = JSON.parse(xhr.responseText);
            resolve({
              fileId: data.file.file_id,
              fileName: data.file.file_name,
              storedFileName: data.file.stored_file_name,
              filePath: data.file.file_path,
              sizeBytes: data.file.size_bytes,
              extension: data.file.extension.replace('.', ''),
              status: data.file.status,
              createdAt: data.file.created_at,
              prepState: data.prep_state,
            });
          } catch {
            reject(new Error('Réponse invalide du serveur lors de l\'upload'));
          }
        } else {
          let message = 'Erreur lors de l\'upload du fichier';
          try {
            const parsed = JSON.parse(xhr.responseText);
            message = parsed.error?.message || parsed.detail || message;
          } catch {
            // corps non-JSON, on garde le message par défaut
          }
          reject(new Error(message));
        }
      };

      xhr.onerror = () => reject(new Error('Erreur réseau lors de l\'upload'));
      xhr.open('POST', `${API_BASE_URL}/files/upload`);
      xhr.send(formData);
    });
  }

  /**
   * Étape 2 : Lancer le prep agent (profiling du fichier)
   * POST /orchestrator/prep
   */
  static async runPrep(prepState: PrepState): Promise<PrepResult> {
    if (USE_MOCK) {
      await new Promise((resolve) => setTimeout(resolve, 800));
      return {
        fileId: prepState.file_id,
        prepStatus: 'success',
        prepError: null,
        prepMeta: { engineUsed: 'pandas', fileSizeMb: 0.02, csvDelimiterUsed: ',' },
      };
    }

    const response = await fetch(`${API_BASE_URL}/orchestrator/prep`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prep_state: prepState }),
    });

    const data = await handleResponse<{
      data: { prep_state: Record<string, any> };
    }>(response, 'la préparation du fichier');

    const ps = data.data.prep_state;
    return {
      fileId: ps.file_id,
      prepStatus: ps.prep_status,
      prepError: ps.prep_error,
      datasetProfile: ps.dataset_profile
        ? {
            rowCount: ps.dataset_profile.row_count,
            columnCount: ps.dataset_profile.column_count,
            columns: ps.dataset_profile.columns,
            dtypes: ps.dataset_profile.dtypes,
            missingRatioByColumn: ps.dataset_profile.missing_ratio_by_column,
            sampleRows: ps.dataset_profile.sample_rows,
          }
        : undefined,
      prepMeta: ps.prep_meta
        ? {
            engineUsed: ps.prep_meta.engine_used,
            fileSizeMb: ps.prep_meta.file_size_mb,
            csvDelimiterUsed: ps.prep_meta.csv_delimiter_used,
          }
        : undefined,
    };
  }

  /**
   * Étape 3 : Détecter le schéma (Orange Money ou mapping manuel)
   * POST /orchestrator/schema-detect?file_id=...
   */
  static async detectSchema(fileId: string): Promise<SchemaDetection> {
    if (USE_MOCK) {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      return {
        fileId,
        isOrangeMoney: false,
        confidenceScore: 62,
        matchedRequiredColumns: [],
        missingRequiredColumns: ['USER_ID', 'ACCOUNT_STATUS'],
        allDetectedColumns: ['Nom', 'Prénom', 'MSISDN', 'ID Type', 'ID Number', 'DOB', 'Address', 'City', 'Status'],
        mappingStatus: 'pending_user_input',
        selectedColumns: {},
        columnReasoning: {},
      };
    }

    const response = await fetch(
      `${API_BASE_URL}/orchestrator/schema-detect?file_id=${fileId}`,
      { method: 'POST', headers: { 'Content-Type': 'application/json' } }
    );

    const data = await handleResponse<Record<string, any>>(response, 'la détection du schéma');

        const selectedColumns: KYCColumnMapping = {
          nomColumn: data.nom_column,
          prenomColumn: data.prenom_column,
          msisdnColumn: data.msisdn_column,
          idTypeColumn: data.id_type_column,
          idNumberColumn: data.id_number_column,
          dobColumn: data.dob_column,
          addressColumn: data.address_column,
          cityColumn: data.city_column,
          statusColumn: data.status_column,
    };

        const rawReasoning = data.column_suggestion_reasoning || {};
        const columnReasoning: SchemaDetection['columnReasoning'] = {
            nomColumn: rawReasoning.nom_column,
            prenomColumn: rawReasoning.prenom_column,
            msisdnColumn: rawReasoning.msisdn_column,
            idTypeColumn: rawReasoning.id_type_column,
            idNumberColumn: rawReasoning.id_number_column,
            dobColumn: rawReasoning.dob_column,
            addressColumn: rawReasoning.address_column,
            cityColumn: rawReasoning.city_column,
            statusColumn: rawReasoning.status_column,
    };

    return {
      fileId,
      isOrangeMoney: data.is_orange_money,
      confidenceScore: data.confidence_score ?? 0,
      matchedRequiredColumns: data.matched_required_columns || [],
      missingRequiredColumns: data.missing_required_columns || [],
      allDetectedColumns: data.all_detected_columns || [],
      mappingStatus: data.mapping_status || 'error',
      selectedColumns,
      columnReasoning,
    };
  }

  /**
   * Étape 3b : Valider le mapping de colonnes
   * POST /orchestrator/validate-schema?file_id=...&nom_column=...
   */
  static async validateSchema(
    fileId: string,
    columns: KYCColumnMapping
  ): Promise<void> {
    if (USE_MOCK) {
      await new Promise((resolve) => setTimeout(resolve, 500));
      return;
    }

    const params = new URLSearchParams({
      file_id: fileId,
      nom_column: columns.nomColumn || '',
      prenom_column: columns.prenomColumn || '',
      msisdn_column: columns.msisdnColumn || '',
      dob_column: columns.dobColumn || '',
      id_type_column: columns.idTypeColumn || '',
      id_number_column: columns.idNumberColumn || '',
      status_column: columns.statusColumn || '',
      address_column: columns.addressColumn || '',
      city_column: columns.cityColumn || '',
    });

    const response = await fetch(
      `${API_BASE_URL}/orchestrator/validate-schema?${params}`,
      { method: 'POST', headers: { 'Content-Type': 'application/json' } }
    );

    await handleResponse(response, 'la validation du schéma');
  }

  /**
   * Étape 4 : Détecter le pays
   * POST /orchestrator/country-detect?file_id=...
   */
  static async detectCountry(fileId: string): Promise<CountryDetection> {
    if (USE_MOCK) {
      await new Promise((resolve) => setTimeout(resolve, 800));
      return {
        fileId,
        detectedCountry: 'Madagascar',
        confidence: 0.87,
        reasoning: 'Formats de numéros et de villes cohérents avec Madagascar.',
        status: 'completed',
      };
    }

    const response = await fetch(
      `${API_BASE_URL}/orchestrator/country-detect?file_id=${fileId}`,
      { method: 'POST', headers: { 'Content-Type': 'application/json' } }
    );

    const data = await handleResponse<Record<string, any>>(response, 'la détection du pays');

    return {
      fileId,
      detectedCountry: data.detected_country,
      confidence: data.country_detection_confidence ?? 0,
      reasoning: data.country_detection_reasoning || '',
      status: data.country_detection_status,
    };
  }

  /**
   * Étape 4b : Valider (ou corriger) le pays détecté
   * POST /orchestrator/validate-country?file_id=...&country=...
   */
  static async validateCountry(fileId: string, country: string): Promise<void> {
    if (USE_MOCK) {
      await new Promise((resolve) => setTimeout(resolve, 400));
      return;
    }

    const params = new URLSearchParams({ file_id: fileId, country });
    const response = await fetch(
      `${API_BASE_URL}/orchestrator/validate-country?${params}`,
      { method: 'POST', headers: { 'Content-Type': 'application/json' } }
    );

    await handleResponse(response, 'la validation du pays');
  }

  /**
   * Étape 5 : Détecter les lignes actives
   * POST /orchestrator/active-lines-detect?file_id=...
   */
  static async detectActiveLines(fileId: string): Promise<ActiveLinesDetection> {
    if (USE_MOCK) {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      return {
        totalLines: 10,
        activeLines: 8,
        activePercentage: 80,
        statusColumn: 'Status',
        statusValues: ['Active'],
      };
    }

    const response = await fetch(
      `${API_BASE_URL}/orchestrator/active-lines-detect?file_id=${fileId}`,
      { method: 'POST', headers: { 'Content-Type': 'application/json' } }
    );

    const data = await handleResponse<Record<string, any>>(response, 'la détection des lignes actives');

    return {
      totalLines: data.total_lines_count,
      activeLines: data.active_lines_count,
      activePercentage: data.active_lines_percentage,
      statusColumn: data.active_status_column,
      statusValues: data.active_status_values || [],
    };
  }

  /**
   * Étape 6 : Analyser les données KYC (agent 2)
   * POST /orchestrator/analyze?file_id=...
   */
  static async analyzeKYC(fileId: string): Promise<KYCAnalysisResult> {
    if (USE_MOCK) {
      await new Promise((resolve) => setTimeout(resolve, 2000));
      return {
        fileId,
        analysisStatus: 'completed',
        overallRiskScore: 0.22,
        overallRiskLevel: 'MEDIUM',
        overallComplianceRate: 91.4,
        activeRowsCount: 8,
        totalAnomalies: 2,
        anomaliesByField: {
          msisdn: [{ type: 'non_numeric_values', count: 1, percentage: 12.5, severity: 'error' }],
        },
        criticalFields: [
          { field: 'msisdn', anomaly: 'non_numeric_values', count: 1, percentage: 12.5 },
        ],
        executiveSummary: {
          overallDataQuality: 'GOOD',
          riskAssessment: 'MEDIUM',
          fieldsWithIssues: 1,
          criticalIssues: 1,
          recommendation: '⚡ MEDIUM RISK: Proceed with caution. Monitor identified issues.',
        },
        detailedResults: {},
      };
    }

    const response = await fetch(
      `${API_BASE_URL}/orchestrator/analyze?file_id=${fileId}`,
      { method: 'POST', headers: { 'Content-Type': 'application/json' } }
    );

    const data = await handleResponse<Record<string, any>>(response, "l'analyse KYC");

    return {
      fileId,
      analysisStatus: data.analysis_status,
      overallRiskScore: data.overall_risk_score ?? 0,
      overallRiskLevel: data.overall_risk_level ?? 'LOW',
      overallComplianceRate: data.overall_compliance_rate ?? 0,
      activeRowsCount: data.active_rows_count ?? 0,
      totalAnomalies: data.total_anomalies ?? 0,
      anomaliesByField: normalizeAnomaliesByField(data.anomalies_by_field ?? {}),
      criticalFields: data.critical_fields ?? [],
      executiveSummary: {
        overallDataQuality: data.executive_summary?.overall_data_quality ?? 'FAIR',
        riskAssessment: data.executive_summary?.risk_assessment ?? 'LOW',
        fieldsWithIssues: data.executive_summary?.fields_with_issues ?? 0,
        criticalIssues: data.executive_summary?.critical_issues ?? 0,
        recommendation: data.executive_summary?.recommendation ?? '',
      },
      detailedResults: normalizeDetailedResults(data.detailed_results ?? {}),
    };
  }

  /**
   * Étape 7 : Récupérer le rapport final (agent 3)
   * GET /orchestrator/report/{fileId}
   */
  static async generateReport(fileId: string): Promise<AnalysisReport> {
    if (USE_MOCK) {
      await new Promise((resolve) => setTimeout(resolve, 500));
      return {
        fileId,
        fileName: 'data.csv',
        detectedCountry: 'Madagascar',
        isOrangeMoney: false,
        analysisStatus: 'completed',
        overallRiskScore: 0.22,
        overallRiskLevel: 'MEDIUM',
        overallComplianceRate: 91.4,
        executiveSummary: {
          overallDataQuality: 'GOOD',
          riskAssessment: 'MEDIUM',
          fieldsWithIssues: 1,
          criticalIssues: 1,
          recommendation: '⚡ MEDIUM RISK: Proceed with caution.',
        },
        anomalies: [
          { field: 'msisdn', type: 'non_numeric_values', count: 1, percentage: 12.5, severity: 'error' },
        ],
        summary: {
          totalAnomalies: 1,
          criticalAnomalies: 1,
          warningAnomalies: 0,
          infoAnomalies: 0,
          totalAnomalyOccurrences: 1,
          affectedRows: 1,
          complianceScore: 91.4,
        },
        fieldResults: {},
        analyzedAt: new Date().toISOString(),
      };
    }

    const response = await fetch(`${API_BASE_URL}/orchestrator/report/${fileId}`);
    const data = await handleResponse<Record<string, any>>(response, 'la génération du rapport');

    return {
      fileId: data.file_id,
      fileName: data.file_name,
      detectedCountry: data.detected_country,
      isOrangeMoney: data.is_orange_money,
      analysisStatus: data.analysis_status,
      overallRiskScore: data.overall_risk_score ?? 0,
      overallRiskLevel: data.overall_risk_level ?? 'LOW',
      overallComplianceRate: data.overall_compliance_rate ?? 0,
      executiveSummary: {
        overallDataQuality: data.executive_summary?.overall_data_quality ?? 'FAIR',
        riskAssessment: data.executive_summary?.risk_assessment ?? 'LOW',
        fieldsWithIssues: data.executive_summary?.fields_with_issues ?? 0,
        criticalIssues: data.executive_summary?.critical_issues ?? 0,
        recommendation: data.executive_summary?.recommendation ?? '',
      },
      anomalies: (data.anomalies || []).map((a: any) => ({
        field: a.field,
        type: a.type,
        count: a.count,
        percentage: a.percentage,
        severity: a.severity,
      })),
      summary: {
        totalAnomalies: data.summary?.total_anomalies ?? 0,
        criticalAnomalies: data.summary?.critical_anomalies ?? 0,
        warningAnomalies: data.summary?.warning_anomalies ?? 0,
        infoAnomalies: data.summary?.info_anomalies ?? 0,
        totalAnomalyOccurrences: data.summary?.total_anomaly_occurrences ?? 0,
        affectedRows: data.summary?.affected_rows ?? 0,
        complianceScore: data.summary?.compliance_score ?? 0,
      },
      fieldResults: normalizeDetailedResults(data.field_results ?? {}),
      analyzedAt: data.analyzed_at,
    };
  }

  /**
   * Exporter le rapport en PDF
   * GET /orchestrator/report/{fileId}/export/pdf
   */
  static async exportReportPdf(fileId: string): Promise<Blob> {
    if (USE_MOCK) {
      return new Blob(['Mock PDF Report'], { type: 'application/pdf' });
    }

    const response = await fetch(`${API_BASE_URL}/orchestrator/report/${fileId}/export/pdf`);
    if (!response.ok) {
      throw new Error("Erreur lors de l'export PDF");
    }
    return response.blob();
  }

  /**
   * Historique des analyses (dashboard)
   * GET /orchestrator/analyses?page=&page_size=&country=&sort=
   */
  static async getAnalysisHistory(
    page: number = 1,
    pageSize: number = 10,
    country?: string,
    sort: 'asc' | 'desc' = 'desc'
  ): Promise<AnalysisHistory> {
    if (USE_MOCK) {
      await new Promise((resolve) => setTimeout(resolve, 500));
      return {
        analyses: [
          {
            id: 'mock-1',
            fileId: 'mock-1',
            fileName: 'kyc_mada_2026_01.csv',
            fileType: 'csv',
            country: 'Madagascar',
            riskScore: 0.22,
            riskLevel: 'MEDIUM',
            complianceRate: 91.4,
            rowsAnalyzed: 8420,
            createdAt: new Date().toISOString(),
          },
        ],
        total: 1,
        page: 1,
        pageSize,
      };
    }

    const params = new URLSearchParams({
      page: String(page),
      page_size: String(pageSize),
      sort,
    });
    if (country) params.set('country', country);

    const response = await fetch(`${API_BASE_URL}/orchestrator/analyses?${params}`);
    const data = await handleResponse<Record<string, any>>(response, "le chargement de l'historique");

    return {
      analyses: (data.analyses || []).map((a: any) => ({
        id: a.id,
        fileId: a.fileId,
        fileName: a.fileName,
        fileType: a.fileType,
        country: a.country,
        riskScore: a.riskScore,
        riskLevel: a.riskLevel,
        complianceRate: a.complianceRate,
        rowsAnalyzed: a.rowsAnalyzed,
        createdAt: a.createdAt,
      })),
      total: data.total ?? 0,
      page: data.page ?? page,
      pageSize: data.pageSize ?? pageSize,
    };
  }
}