'use client';

import { Layout } from '../../components/common';
import { useKYCAnalysis } from '../../hooks/useKYCAnalysis';
import { UploadStep } from '../../components/upload/UploadStep';
import { SchemaStep } from '../../components/upload/SchemaStep';
import { AnalysisStep } from '../../components/upload/AnalysisStep';
import { ReportStep } from '../../components/upload/ReportStep';
import { Card, CardContent } from '../../components/ui/card';

export default function UploadPage() {
  const {
    currentStep, isLoading, error, fileId, fileInfo, schemaDetection, analysisResult, report,
    uploadFile, runPrep, detectSchema, validateSchema, detectCountry, validateCountry,
    detectActiveLines, analyzeKYC, generateReport, reset,
  } = useKYCAnalysis();

  const handleUpload = async (file: File) => {
    try {
      const info = await uploadFile(file);
      await runPrep();
      await detectSchema(info.fileId);
    } catch (err) {
      console.error('Erreur upload/prep:', err);
    }
  };

  const handleSchemaConfirm = async (selectedColumns: Record<string, string>) => {
    try {
      await validateSchema(selectedColumns);

      const country = await detectCountry();
      if (!country.country || country.country === 'Unknown') {
        throw new Error('Le pays n’a pas pu être déterminé automatiquement.');
      }
      await validateCountry(country.country);

      await detectActiveLines();
      await analyzeKYC();
    } catch (err) {
      console.error('Erreur analyse:', err);
    }
  };

  const handleAnalysisComplete = async () => {
    try {
      await generateReport();
    } catch (err) {
      console.error('Erreur rapport:', err);
    }
  };

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Analyse KYC de données</h1>
          <p className="text-lg text-gray-600">
            Téléchargez votre fichier CSV ou Excel pour une analyse complète
          </p>
        </div>

        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div className={'flex-1 h-2 rounded-full ' + (currentStep === 'upload' ? 'bg-orange-500' : 'bg-green-500')} />
            <div className={'flex-1 h-2 rounded-full mx-2 ' + (['schema', 'analysis', 'report'].includes(currentStep) ? 'bg-orange-500' : 'bg-gray-300')} />
            <div className={'flex-1 h-2 rounded-full mx-2 ' + (['analysis', 'report'].includes(currentStep) ? 'bg-orange-500' : 'bg-gray-300')} />
            <div className={'flex-1 h-2 rounded-full ' + (currentStep === 'report' ? 'bg-orange-500' : 'bg-gray-300')} />
          </div>
          <div className="flex justify-between text-sm text-gray-600">
            <span>Upload</span><span>Schéma</span><span>Analyse</span><span>Rapport</span>
          </div>
        </div>

        {error && (
          <Card className="border-red-200 bg-red-50 mb-6">
            <CardContent className="pt-6">
              <p className="text-red-700">{error}</p>
            </CardContent>
          </Card>
        )}

        {currentStep === 'upload' && <UploadStep onUpload={handleUpload} isLoading={isLoading} />}

        {currentStep === 'schema' && schemaDetection && (
          <SchemaStep schema={schemaDetection} onConfirm={handleSchemaConfirm} isLoading={isLoading} />
        )}

        {currentStep === 'analysis' && analysisResult && (
          <AnalysisStep result={analysisResult} onComplete={handleAnalysisComplete} isLoading={isLoading} />
        )}

        {currentStep === 'report' && report && <ReportStep report={report} onReset={reset} />}
      </div>
    </Layout>
  );
}
