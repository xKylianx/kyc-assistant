'use client';

import { useState } from 'react';
import { ApiService } from '../services/api';
import {
  UploadResult,
  PrepResult,
  SchemaDetection,
  CountryDetection,
  ActiveLinesDetection,
  KYCAnalysisResult,
  AnalysisReport,
  KYCColumnMapping,
} from '../types/analysis';

export type AnalysisStep =
  | 'upload'
  | 'prep'
  | 'schema'
  | 'country'
  | 'analysis'
  | 'report';

export function useKYCAnalysis() {
  const [currentStep, setCurrentStep] = useState<AnalysisStep>('upload');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Données du flux
  const [fileId, setFileId] = useState<string | null>(null);
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const [prepResult, setPrepResult] = useState<PrepResult | null>(null);
  const [schemaDetection, setSchemaDetection] = useState<SchemaDetection | null>(null);
  const [schemaAutoValidated, setSchemaAutoValidated] = useState<boolean>(false);
  const [countryDetection, setCountryDetection] = useState<CountryDetection | null>(null);
  const [activeLines, setActiveLines] = useState<ActiveLinesDetection | null>(null);
  const [analysisResult, setAnalysisResult] = useState<KYCAnalysisResult | null>(null);
  const [report, setReport] = useState<AnalysisReport | null>(null);

  const runStep = async <T,>(
    label: string,
    fn: () => Promise<T>
  ): Promise<T> => {
    setIsLoading(true);
    setError(null);
    try {
      return await fn();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erreur inconnue';
      console.error(`❌ ${label}:`, message);
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };
  // Étape 1 : Upload
  const uploadFile = async (file: File) => {
    return runStep('Upload', async () => {
      const result = await ApiService.uploadFile(file);
      setFileId(result.fileId);
      setUploadResult(result);
      setCurrentStep('prep');
      return result;
    });
  };

  // Étape 2 : Prep agent — accepte le résultat d'upload en paramètre pour éviter
  // toute dépendance à un state pas encore re-rendu (voir handleUpload dans page.tsx)
  const runPrep = async (upload?: UploadResult) => {
    const uploadData = upload ?? uploadResult;
    if (!uploadData) throw new Error('Aucun fichier uploadé');
    return runStep('Prep', async () => {
      const result = await ApiService.runPrep(uploadData.prepState);
      setPrepResult(result);
      if (result.prepStatus === 'error') {
        throw new Error(result.prepError || 'Échec de la préparation du fichier');
      }

      const schema = await ApiService.detectSchema(uploadData.fileId);
      setSchemaDetection(schema);

      if (schema.isOrangeMoney) {
        await ApiService.validateSchema(uploadData.fileId, schema.selectedColumns);
        setSchemaAutoValidated(true);
        const country = await ApiService.detectCountry(uploadData.fileId);
        setCountryDetection(country);
        setCurrentStep('country');
      } else {
        setSchemaAutoValidated(false);
        setCurrentStep('schema');
      }

      return result;
    });
  };

  // Permet à l'UI de fermer le bandeau sans affecter le flux d'analyse
  const dismissSchemaBanner = () => setSchemaAutoValidated(false);

  // Étape 3 : Valider le mapping de colonnes KYC (cas non-Orange Money uniquement)
  const validateSchema = async (columns: KYCColumnMapping) => {
    if (!fileId) throw new Error('Aucun fichier sélectionné');
    return runStep('Validation du schéma', async () => {
      await ApiService.validateSchema(fileId, columns);
      const country = await ApiService.detectCountry(fileId);
      setCountryDetection(country);
      setCurrentStep('country');
      return true;
    });
  };

  // Étape 4 : Confirmer (ou corriger) le pays détecté
  const validateCountry = async (country: string) => {
    if (!fileId) throw new Error('Aucun fichier sélectionné');
    return runStep('Validation du pays', async () => {
      await ApiService.validateCountry(fileId, country);
      setCountryDetection((prev) =>
        prev ? { ...prev, detectedCountry: country, status: 'completed' } : prev
      );
      // Enchaîne sur la détection des lignes actives puis l'analyse
      const lines = await ApiService.detectActiveLines(fileId);
      setActiveLines(lines);
      const result = await ApiService.analyzeKYC(fileId);
      setAnalysisResult(result);
      setCurrentStep('analysis');
      return result;
    });
  };

  // Étape 5 : Générer le rapport final (agent 3)
  const generateReport = async () => {
    if (!fileId) throw new Error('Aucun fichier sélectionné');
    return runStep('Génération du rapport', async () => {
      const rep = await ApiService.generateReport(fileId);
      setReport(rep);
      setCurrentStep('report');
      return rep;
    });
  };

  const exportReportPdf = async () => {
    if (!fileId) throw new Error('Aucun fichier sélectionné');
    return runStep('Export PDF', async () => {
      const blob = await ApiService.exportReportPdf(fileId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `kyc-report-${fileId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    });
  };

  // Réinitialiser
    // Réinitialiser
  const reset = () => {
    setCurrentStep('upload');
    setFileId(null);
    setUploadResult(null);
    setPrepResult(null);
    setSchemaDetection(null);
    setSchemaAutoValidated(false); // NOUVEAU
    setCountryDetection(null);
    setActiveLines(null);
    setAnalysisResult(null);
    setReport(null);
    setError(null);
  };

  return {
    currentStep,
    isLoading,
    error,
    fileId,
    uploadResult,
    prepResult,
    schemaDetection,
    schemaAutoValidated,   // NOUVEAU
    dismissSchemaBanner,   // NOUVEAU
    countryDetection,
    activeLines,
    analysisResult,
    report,
    uploadFile,
    runPrep,
    validateSchema,
    validateCountry,
    generateReport,
    exportReportPdf,
    reset,
  };
}