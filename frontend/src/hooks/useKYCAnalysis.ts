'use client';

import { useState } from 'react';
import { ApiService } from '../services/api';
import { FileInfo, SchemaDetection, KYCAnalysisResult, AnalysisReport, PrepState } from '../types/analysis';

export type AnalysisStep = 'upload' | 'schema' | 'analysis' | 'report';

export function useKYCAnalysis() {
  const [currentStep, setCurrentStep] = useState<AnalysisStep>('upload');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fileId, setFileId] = useState<string | null>(null);
  const [fileInfo, setFileInfo] = useState<FileInfo | null>(null);
  const [prepState, setPrepState] = useState<PrepState | null>(null);
  const [schemaDetection, setSchemaDetection] = useState<SchemaDetection | null>(null);
  const [analysisResult, setAnalysisResult] = useState<KYCAnalysisResult | null>(null);
  const [report, setReport] = useState<AnalysisReport | null>(null);

  const uploadFile = async (file: File) => {
    setIsLoading(true);
    setError(null);
    try {
      const info = await ApiService.uploadFile(file);
      setFileId(info.fileId);
      setFileInfo(info);
      setPrepState(info.prepState);
      return info;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erreur lors de l’upload';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const runPrep = async () => {
    if (!prepState) throw new Error('Aucun état de préparation disponible');
    setIsLoading(true);
    setError(null);
    try {
      const prepared = await ApiService.runPrep(prepState);
      if (prepared.prep_status === 'error') {
        throw new Error(prepared.prep_error || 'La préparation du fichier a échoué');
      }
      setPrepState(prepared);
      const profile = prepared.dataset_profile;
      if (profile && fileInfo) {
        const columns = profile.columns;
        const preview = profile.sample_rows.map((row) => columns.map((column) => String(row[column] ?? '')));
        setFileInfo({ ...fileInfo, rowCount: profile.row_count, preview });
      }
      return prepared;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erreur lors de la préparation';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const detectSchema = async (detectedFileId?: string) => {
    const id = detectedFileId || fileId;
    if (!id) throw new Error('Aucun file ID disponible');
    setIsLoading(true);
    setError(null);
    try {
      const schema = await ApiService.detectSchema(id);
      const profile = prepState?.dataset_profile;
      if (profile) {
        schema.fileInfo = {
          ...schema.fileInfo,
          fileName: prepState.file_name,
          rowCount: profile.row_count,
          delimiter: String(prepState.prep_meta?.csv_delimiter_used || schema.fileInfo.delimiter || ','),
          preview: profile.sample_rows.map((row) => profile.columns.map((column) => String(row[column] ?? ''))),
        };
        schema.availableColumns = profile.columns;
      }
      setSchemaDetection(schema);
      setCurrentStep('schema');
      return schema;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erreur lors de la détection du schéma';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const validateSchema = async (selectedColumns: Record<string, string>) => {
    if (!fileId) throw new Error('Aucun file ID disponible');
    setIsLoading(true);
    setError(null);
    try {
      await ApiService.validateSchema(fileId, selectedColumns);
      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erreur lors de la validation du schéma';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const detectCountry = async () => {
    if (!fileId) throw new Error('Aucun file ID disponible');
    setIsLoading(true);
    setError(null);
    try {
      const result = await ApiService.detectCountry(fileId);
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erreur lors de la détection du pays';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const validateCountry = async (country: string) => {
    if (!fileId) throw new Error('Aucun file ID disponible');
    setIsLoading(true);
    setError(null);
    try {
      await ApiService.validateCountry(fileId, country);
      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erreur lors de la validation du pays';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const detectActiveLines = async () => {
    if (!fileId) throw new Error('Aucun file ID disponible');
    setIsLoading(true);
    setError(null);
    try {
      return await ApiService.detectActiveLines(fileId);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erreur lors de la détection des lignes actives';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const analyzeKYC = async () => {
    if (!fileId) throw new Error('Aucun file ID disponible');
    setIsLoading(true);
    setError(null);
    try {
      const result = await ApiService.analyzeKYC(fileId);
      setAnalysisResult(result);
      setCurrentStep('analysis');
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erreur lors de l’analyse KYC';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const generateReport = async () => {
    if (!fileId) throw new Error('Aucun file ID disponible');
    setIsLoading(true);
    setError(null);
    try {
      const result = await ApiService.generateReport(fileId);
      setReport(result);
      setCurrentStep('report');
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erreur lors de la génération du rapport';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const reset = () => {
    setCurrentStep('upload');
    setFileId(null);
    setFileInfo(null);
    setPrepState(null);
    setSchemaDetection(null);
    setAnalysisResult(null);
    setReport(null);
    setError(null);
  };

  return {
    currentStep, isLoading, error, fileId, fileInfo, prepState, schemaDetection,
    analysisResult, report, uploadFile, runPrep, detectSchema, validateSchema,
    detectCountry, validateCountry, detectActiveLines, analyzeKYC, generateReport, reset,
  };
}
