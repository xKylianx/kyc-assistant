import { FileInfo, SchemaDetection, KYCAnalysisResult, AnalysisReport } from '../types/analysis';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === 'true';

console.log('🔧 API Service initialized:', { API_BASE_URL, USE_MOCK });

export class ApiService {
  /**
   * Étape 1 : Uploader le fichier
   * POST /files/upload
   */
  static async uploadFile(file: File): Promise<FileInfo & { fileId: string }> {
    console.log('📤 uploadFile:', { fileName: file.name, fileSize: file.size, USE_MOCK });

    if (USE_MOCK) {
      console.log('✅ Using mock data');
      await new Promise((resolve) => setTimeout(resolve, 1500));
      
      return {
        fileId: 'mock-file-id-123',
        fileName: file.name,
        fileSize: file.size,
        fileType: (file.name.split('.').pop() || 'csv') as 'csv' | 'xlsx' | 'xls',
        delimiter: ',',
        rowCount: 1250,
        preview: [
          ['Nom', 'Prénom', 'MSISDN', 'ID Type', 'ID Number', 'DOB', 'Address', 'City', 'Status'],
          ['Doe', 'John', '+33612345678', 'Passport', 'AB123456', '1990-05-15', '123 Rue de Paris', 'Paris', 'Active'],
          ['Smith', 'Jane', '+33687654321', 'ID Card', 'CD789012', '1985-08-22', '456 Avenue Lyon', 'Lyon', 'Active'],
        ],
      };
    }

    console.log('🌐 Making real API call to:', `${API_BASE_URL}/files/upload`);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE_URL}/files/upload`, {
        method: 'POST',
        body: formData,
      });

      console.log('📨 Response status:', response.status);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ Error response:', errorText);
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      const data = await response.json();
      console.log('✅ Upload successful:', data);
      
      return {
        fileId: data.file.file_id,
        fileName: data.file.file_name,
        fileSize: data.file.size_bytes,
        fileType: data.file.extension.replace('.', '') as 'csv' | 'xlsx' | 'xls',
        delimiter: ',',
        rowCount: 0,
        preview: [],
      };
    } catch (error) {
      console.error('❌ Upload error:', error);
      throw error;
    }
  }

  /**
   * Étape 2 : Détecter le schéma
   * POST /orchestrator/schema-detect?file_id=...
   */
  static async detectSchema(fileId: string): Promise<SchemaDetection> {
    console.log('🔍 detectSchema:', { fileId, USE_MOCK });

    if (USE_MOCK) {
      console.log('✅ Using mock data');
      await new Promise((resolve) => setTimeout(resolve, 1000));
      
      return {
        fileId,
        fileInfo: {
          fileName: 'data.csv',
          fileSize: 1024000,
          fileType: 'csv',
          delimiter: ',',
          rowCount: 1250,
          preview: [
            ['Nom', 'Prénom', 'MSISDN', 'ID Type', 'ID Number', 'DOB', 'Address', 'City', 'Status'],
            ['Doe', 'John', '+33612345678', 'Passport', 'AB123456', '1990-05-15', '123 Rue de Paris', 'Paris', 'Active'],
            ['Smith', 'Jane', '+33687654321', 'ID Card', 'CD789012', '1985-08-22', '456 Avenue Lyon', 'Lyon', 'Active'],
          ],
        },
        detectedCountry: 'FR',
        detectedSchema: 'orange_money',
        availableColumns: ['Nom', 'Prénom', 'MSISDN', 'ID Type', 'ID Number', 'DOB', 'Address', 'City', 'Status'],
        selectedColumns: {
          nomColumn: 'Nom',
          prenomColumn: 'Prénom',
          msisdnColumn: 'MSISDN',
          idTypeColumn: 'ID Type',
          idNumberColumn: 'ID Number',
          dobColumn: 'DOB',
          addressColumn: 'Address',
          cityColumn: 'City',
          statusColumn: 'Status',
        },
      };
    }

    console.log('🌐 Making real API call to:', `${API_BASE_URL}/orchestrator/schema-detect?file_id=${fileId}`);
    const response = await fetch(`${API_BASE_URL}/orchestrator/schema-detect?file_id=${fileId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ Error response:', errorText);
      const error = JSON.parse(errorText);
      throw new Error(error.error?.message || 'Erreur lors de la détection du schéma');
    }

    const data = await response.json();
    console.log('✅ Schema detected:', data);

    return {
      fileId,
      fileInfo: {
        fileName: 'data.csv',
        fileSize: 0,
        fileType: 'csv',
        delimiter: ',',
        rowCount: data.total_columns_found || 0,
        preview: [],
      },
      detectedCountry: 'FR',
      detectedSchema: data.is_orange_money ? 'orange_money' : 'other',
      availableColumns: data.all_detected_columns || [],
      selectedColumns: {
        nomColumn: data.nom_column,
        prenomColumn: data.prenom_column,
        msisdnColumn: data.msisdn_column,
        idTypeColumn: data.id_type_column,
        idNumberColumn: data.id_number_column,
        dobColumn: data.dob_column,
        addressColumn: data.address_column,
        cityColumn: data.city_column,
        statusColumn: data.status_column,
      },
    };
  }

  /**
   * Étape 2b : Valider le schéma
   * POST /orchestrator/validate-schema?file_id=...&nom_column=...&...
   */
  static async validateSchema(
    fileId: string,
    selectedColumns: Record<string, string>
  ): Promise<void> {
    console.log('✅ validateSchema:', { fileId, selectedColumns, USE_MOCK });

    if (USE_MOCK) {
      await new Promise((resolve) => setTimeout(resolve, 500));
      return;
    }

    // Construire les query parameters
    const params = new URLSearchParams({
      file_id: fileId,
      nom_column: selectedColumns.nomColumn || '',
      prenom_column: selectedColumns.prenomColumn || '',
      msisdn_column: selectedColumns.msisdnColumn || '',
      id_type_column: selectedColumns.idTypeColumn || '',
      id_number_column: selectedColumns.idNumberColumn || '',
      dob_column: selectedColumns.dobColumn || '',
      address_column: selectedColumns.addressColumn || '',
      city_column: selectedColumns.cityColumn || '',
      status_column: selectedColumns.statusColumn || '',
    });

    console.log('🌐 Making real API call to:', `${API_BASE_URL}/orchestrator/validate-schema?${params}`);
    const response = await fetch(`${API_BASE_URL}/orchestrator/validate-schema?${params}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ Error response:', errorText);
      throw new Error('Erreur lors de la validation du schéma');
    }
  }

  /**
   * Étape 2c : Détecter le pays
   * POST /orchestrator/country-detect?file_id=...
   */
  static async detectCountry(fileId: string): Promise<string> {
    console.log('🌍 detectCountry:', { fileId, USE_MOCK });

    if (USE_MOCK) {
      await new Promise((resolve) => setTimeout(resolve, 800));
      return 'FR';
    }

    console.log('🌐 Making real API call to:', `${API_BASE_URL}/orchestrator/country-detect?file_id=${fileId}`);
    const response = await fetch(`${API_BASE_URL}/orchestrator/country-detect?file_id=${fileId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ Error response:', errorText);
      throw new Error('Erreur lors de la détection du pays');
    }

    const data = await response.json();
    return data.detected_country;
  }

  /**
   * Étape 2d : Détecter les lignes actives
   * POST /orchestrator/active-lines-detect?file_id=...
   */
  static async detectActiveLines(fileId: string): Promise<{
    totalLines: number;
    activeLines: number;
    activePercentage: number;
    statusColumn: string;
    statusValues: string[];
  }> {
    console.log('📊 detectActiveLines:', { fileId, USE_MOCK });

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

    console.log('🌐 Making real API call to:', `${API_BASE_URL}/orchestrator/active-lines-detect?file_id=${fileId}`);
    const response = await fetch(`${API_BASE_URL}/orchestrator/active-lines-detect?file_id=${fileId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ Error response:', errorText);
      throw new Error('Erreur lors de la détection des lignes actives');
    }

    const data = await response.json();
    return {
      totalLines: data.total_lines_count,
      activeLines: data.active_lines_count,
      activePercentage: data.active_lines_percentage,
      statusColumn: data.active_status_column,
      statusValues: data.active_status_values,
    };
  }

  /**
   * Étape 3 : Analyser les données KYC
   * POST /orchestrator/analyze?file_id=...
   */
  static async analyzeKYC(
    fileId: string,
    selectedColumns: Record<string, string>
  ): Promise<KYCAnalysisResult> {
    console.log('📊 analyzeKYC:', { fileId, USE_MOCK });

    if (USE_MOCK) {
      console.log('✅ Using mock data');
      await new Promise((resolve) => setTimeout(resolve, 2000));
      
      return {
        fileId,
        fileName: 'data.csv',
        totalRows: 10,
        analyzedRows: 8,
        anomalies: [
          {
            id: 'a1',
            row: 4,
            column: 'MSISDN',
            value: 'invalid_phone',
            anomalyType: 'invalid_format',
            description: 'Format de numéro de téléphone invalide',
            severity: 'error',
            confidence: 98,
          },
        ],
        riskScore: 35,
        riskLevel: 'MEDIUM',
        detectedCountry: 'FR',
        detectedSchema: 'orange_money',
        analysisTime: 5,
        createdAt: new Date().toISOString(),
      };
    }

    console.log('🌐 Making real API call to:', `${API_BASE_URL}/orchestrator/analyze?file_id=${fileId}`);
    const response = await fetch(`${API_BASE_URL}/orchestrator/analyze?file_id=${fileId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ Error response:', errorText);
      throw new Error('Erreur lors de l\'analyse KYC');
    }

    const data = await response.json();
    
    return {
      fileId,
      fileName: 'data.csv',
      totalRows: data.total_lines_count || 0,
      analyzedRows: data.active_rows_count || 0,
      anomalies: data.anomalies || [],
      riskScore: data.overall_risk_score || 0,
      riskLevel: data.overall_risk_level || 'LOW',
      detectedCountry: data.detected_country || 'FR',
      detectedSchema: 'orange_money',
      analysisTime: 0,
      createdAt: new Date().toISOString(),
    };
  }

  /**
   * Étape 4 : Générer le rapport
   * GET /orchestrator/report/{fileId}
   */
  static async generateReport(fileId: string): Promise<AnalysisReport> {
    console.log('📋 generateReport:', { fileId, USE_MOCK });

    if (USE_MOCK) {
      console.log('✅ Using mock data');
      await new Promise((resolve) => setTimeout(resolve, 500));
      
      return {
        analysis: {
          fileId,
          fileName: 'data.csv',
          totalRows: 10,
          analyzedRows: 8,
          anomalies: [],
          riskScore: 35,
          riskLevel: 'MEDIUM',
          detectedCountry: 'FR',
          detectedSchema: 'orange_money',
          analysisTime: 5,
          createdAt: new Date().toISOString(),
        },
        summary: {
          totalAnomalies: 1,
          criticalAnomalies: 0,
          warningAnomalies: 0,
          infoAnomalies: 1,
          affectedRows: 1,
          complianceScore: 85,
        },
      };
    }

    console.log('🌐 Making real API call to:', `${API_BASE_URL}/orchestrator/report/${fileId}`);
    const response = await fetch(`${API_BASE_URL}/orchestrator/report/${fileId}`);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ Error response:', errorText);
      throw new Error('Erreur lors de la génération du rapport');
    }

    const data = await response.json();
    
    return {
      analysis: {
        fileId,
        fileName: data.file_name || 'data.csv',
        totalRows: data.total_lines_count || 0,
        analyzedRows: data.active_rows_count || 0,
        anomalies: data.anomalies || [],
        riskScore: data.overall_risk_score || 0,
        riskLevel: data.overall_risk_level || 'LOW',
        detectedCountry: data.detected_country || 'FR',
        detectedSchema: 'orange_money',
        analysisTime: 0,
        createdAt: new Date().toISOString(),
      },
      summary: {
        totalAnomalies: data.total_anomalies || 0,
        criticalAnomalies: data.critical_anomalies || 0,
        warningAnomalies: data.warning_anomalies || 0,
        infoAnomalies: data.info_anomalies || 0,
        affectedRows: data.affected_rows || 0,
        complianceScore: data.compliance_score || 0,
      },
    };
  }

  /**
   * Exporter le rapport en PDF
   */
  static async exportReportPdf(fileId: string): Promise<Blob> {
    console.log('📥 exportReportPdf:', { fileId, USE_MOCK });

    if (USE_MOCK) {
      const pdfContent = 'Mock PDF Report';
      return new Blob([pdfContent], { type: 'application/pdf' });
    }

    const response = await fetch(`${API_BASE_URL}/orchestrator/report/${fileId}/export/pdf`);

    if (!response.ok) {
      throw new Error('Erreur lors de l\'export PDF');
    }

    return response.blob();
  }
}