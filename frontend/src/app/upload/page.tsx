'use client';

import { Layout } from '../../components/common';
import { useKYCAnalysis } from '../../hooks/useKYCAnalysis';
import { UploadStep } from '../../components/upload/UploadStep';
import { SchemaStep } from '../../components/upload/SchemaStep';
import { CountryStep } from '../../components/upload/CountryStep';
import { AnalysisStep } from '../../components/upload/AnalysisStep';
import { ReportStep } from '../../components/upload/ReportStep';
import { AnalysisLoadingCard } from '../../components/upload/AnalysisLoadingCard';
import { Card, CardContent } from '../../components/ui/card';
import { AlertCircle } from 'lucide-react';

const STEP_LABELS: Record<string, string> = {
  upload: 'Upload',
  prep: 'Préparation',
  schema: 'Schéma',
  country: 'Pays',
  analysis: 'Analyse',
  report: 'Rapport',
};

const STEP_ORDER = ['upload', 'prep', 'schema', 'country', 'analysis', 'report'];

export default function UploadPage() {
  const {
    currentStep,
    isLoading,
    error,
    uploadProgress,
    prepResult,
    schemaDetection,
    schemaAutoValidated,
    dismissSchemaBanner,
    countryDetection,
    analysisResult,
    analysisElapsedSeconds,
    report,
    uploadFile,
    runPrep,
    validateSchema,
    validateCountry,
    generateReport,
    exportReportPdf,
    reset,
  } = useKYCAnalysis();

  const handleUpload = async (file: File) => {
    try {
      const upload = await uploadFile(file);
      await runPrep(upload);
    } catch (err) {
      console.error('Erreur upload:', err);
    }
  };

  const currentIndex = STEP_ORDER.indexOf(currentStep);
  const isAnalyzing = currentStep === 'country' && isLoading && !!countryDetection;

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-black mb-2">
            Analyse KYC de données
          </h1>
          <p className="text-lg text-gray-600">
            Téléchargez votre fichier CSV ou Excel pour une analyse complète
          </p>
        </div>

        <div className="mb-8">
          <div className="flex items-center mb-4">
            {STEP_ORDER.map((step, idx) => (
              <div
                key={step}
                className={`flex-1 h-2 rounded-full mx-1 first:ml-0 last:mr-0 transition-colors ${
                  idx <= currentIndex ? 'bg-orange' : 'bg-gray-200'
                }`}
              />
            ))}
          </div>
          <div className="flex justify-between text-sm">
            {STEP_ORDER.map((step, idx) => (
              <span
                key={step}
                className={idx <= currentIndex ? 'text-black font-medium' : 'text-gray-400'}
              >
                {STEP_LABELS[step]}
              </span>
            ))}
          </div>
        </div>

        {error && (
          <Card className="border-red-200 bg-red-50 mb-6">
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                <p className="text-red-700">{error}</p>
              </div>
            </CardContent>
          </Card>
        )}

        {(currentStep === 'upload' || currentStep === 'prep') && (
          <UploadStep onUpload={handleUpload} isLoading={isLoading} progress={uploadProgress} />
        )}

        {currentStep === 'schema' && schemaDetection && (
          <SchemaStep
            schema={schemaDetection}
            prepResult={prepResult}
            onConfirm={validateSchema}
            isLoading={isLoading}
          />
        )}

        {currentStep === 'country' && countryDetection && (
          isAnalyzing ? (
            <AnalysisLoadingCard elapsedSeconds={analysisElapsedSeconds} />
          ) : (
            <CountryStep
              countryDetection={countryDetection}
              schemaAutoValidated={schemaAutoValidated}
              onDismissBanner={dismissSchemaBanner}
              onConfirm={validateCountry}
              isLoading={isLoading}
            />
          )
        )}

        {currentStep === 'analysis' && analysisResult && (
          <AnalysisStep
            result={analysisResult}
            onComplete={generateReport}
            isLoading={isLoading}
          />
        )}

        {currentStep === 'report' && report && (
          <ReportStep
            report={report}
            onReset={reset}
            onExportPdf={exportReportPdf}
            isExporting={isLoading}
          />
        )}
      </div>
    </Layout>
  );
}