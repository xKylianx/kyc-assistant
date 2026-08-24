'use client';

import { useState } from 'react';
import { ApiService } from '../services/api';
import { FileInfo, SchemaDetection, KYCAnalysisResult, AnalysisReport } from '../types/analysis';

export type AnalysisStep = 'upload' | 'schema' | 'analysis' | 'report';

export function useKYCAnalysis() {
  const [currentStep, setCurrentStep] = useState<AnalysisStep>('upload');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Données du flux
  const [fileId, setFileId] = useState<string | null>(null);
  const [fileInfo, setFileInfo] = useState<FileInfo | null>(null);
  const [schemaDetection, setSchemaDetection] = useState<SchemaDetection | null>(null);
  const [analysisResult, setAnalysisResult] = useState<KYCAnalysisResult | null>(null);
  const [report, setReport] = useState<AnalysisReport | null>(null);

  // Étape 1 : Upload
  const uploadFile = async (file: File) => {
    setIsLoading(true);
    setError(null);

    try {
      console.log('📤 Uploading file:', file.name);
      const info = await ApiService.uploadFile(file);
      console.log('✅ Upload successful, fileId:', info.fileId);
      
      setFileId(info.fileId);
      setFileInfo(info);
      setCurrentStep('schema');
      
      return info;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erreur inconnue';
      console.error('❌ Upload error:', message);
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  // Étape 2 : Détecter le schéma
  const detectSchema = async (detectedFileId?: string) => {
    setIsLoading(true);
    setError(null);

    const idToUse = detectedFileId || fileId;
    if (!idToUse) {
      const message = 'No file ID available';
      setError(message);
      throw new Error(message);
    }

    try {
      console.log('🔍 Detecting schema for file:', idToUse);
      const schema = await ApiService.detectSchema(idToUse);
      console.log('✅ Schema detected:', schema);
      
      setSchemaDetection(schema);
      setCurrentStep('schema');
      
      return schema;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erreur inconnue';
      console.error('❌ Schema detection error:', message);
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  // Étape 2b : Valider le schéma
  const validateSchema = async (selectedColumns: Record<string, string>) => {
    setIsLoading(true);
    setError(null);

    if (!fileId) {
      const message = 'No file ID available';
      setError(message);
      throw new Error(message);
    }

    try {
      console.log('✅ Validating schema for file:', fileId);
      await ApiService.validateSchema(fileId, selectedColumns);
      console.log('✅ Schema validated');
      
      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erreur inconnue';
      console.error('❌ Schema validation error:', message);
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  // Étape 2c : Détecter le pays
  const detectCountry = async () => {
    setIsLoading(true);
    setError(null);

    if (!fileId) {
      const message = 'No file ID available';
      setError(message);
      throw new Error(message);
    }

    try {
      console.log('🌍 Detecting country for file:', fileId);
      const country = await ApiService.detectCountry(fileId);
      console.log('✅ Country detected:', country);
      
      return country;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erreur inconnue';
      console.error('❌ Country detection error:', message);
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  // Étape 2d : Détecter les lignes actives
  const detectActiveLines = async () => {
    setIsLoading(true);
    setError(null);

    if (!fileId) {
      const message = 'No file ID available';
      setError(message);
      throw new Error(message);
    }

    try {
      console.log('📊 Detecting active lines for file:', fileId);
      const activeLines = await ApiService.detectActiveLines(fileId);
      console.log('✅ Active lines detected:', activeLines);
      
      return activeLines;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erreur inconnue';
      console.error('❌ Active lines detection error:', message);
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  // Étape 3 : Analyser KYC
  const analyzeKYC = async (selectedColumns: Record<string, string>) => {
    setIsLoading(true);
    setError(null);

    if (!fileId) {
      const message = 'No file ID available';
      setError(message);
      throw new Error(message);
    }

    try {
      console.log('📊 Analyzing KYC for file:', fileId);
      const result = await ApiService.analyzeKYC(fileId, selectedColumns);
      console.log('✅ KYC analysis complete:', result);
      
      setAnalysisResult(result);
      setCurrentStep('analysis');
      
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erreur inconnue';
      console.error('❌ KYC analysis error:', message);
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  // Étape 4 : Générer le rapport
  const generateReport = async () => {
    setIsLoading(true);
    setError(null);

    if (!fileId) {
      const message = 'No file ID available';
      setError(message);
      throw new Error(message);
    }

    try {
      console.log('📋 Generating report for file:', fileId);
      const rep = await ApiService.generateReport(fileId);
      console.log('✅ Report generated:', rep);
      
      setReport(rep);
      setCurrentStep('report');
      
      return rep;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erreur inconnue';
      console.error('❌ Report generation error:', message);
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  // Réinitialiser
  const reset = () => {
    setCurrentStep('upload');
    setFileId(null);
    setFileInfo(null);
    setSchemaDetection(null);
    setAnalysisResult(null);
    setReport(null);
    setError(null);
  };

  return {
    currentStep,
    isLoading,
    error,
    fileId,
    fileInfo,
    schemaDetection,
    analysisResult,
    report,
    uploadFile,
    detectSchema,
    validateSchema,
    detectCountry,
    detectActiveLines,
    analyzeKYC,
    generateReport,
    reset,
  };
}