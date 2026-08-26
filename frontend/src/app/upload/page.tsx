'use client';

import { Layout } from '../../components/common';
import { useKYCAnalysis } from '../../hooks/useKYCAnalysis';
import { UploadStep } from '../../components/upload/UploadStep';
import { SchemaStep } from '../../components/upload/SchemaStep';
import { CountryStep } from '../../components/upload/CountryStep';
import { AnalysisStep } from '../../components/upload/AnalysisStep';
import { ReportStep } from '../../components/upload/ReportStep';
import { Card, CardContent } from '../../components/ui/card';

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
    prepResult,
    schemaDetection,
    schemaAutoValidated,
    dismissSchemaBanner,
    countryDetection,
    analysisResult,
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
      await uploadFile(file);
      await runPrep();
    } catch (err) {
      console.error('Erreur upload:', err);
    }
  };

  const currentIndex = STEP_ORDER.indexOf(currentStep);

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Analyse KYC de données
          </h1>
          <p className="text-lg text-gray-600">
            Téléchargez votre fichier CSV ou Excel pour une analyse complète
          </p>
        </div>

        {/* Indicateur de progression */}
        <div className="mb-8">
          <div className="flex items-center mb-4">
            {STEP_ORDER.map((step, idx) => (
              <div
                key={step}
                className={`flex-1 h-2 rounded-full mx-1 first:ml-0 last:mr-0 ${
                  idx <= currentIndex ? 'bg-orange-500' : 'bg-gray-300'
                }`}
              />
            ))}
          </div>
          <div className="flex justify-between text-sm text-gray-600">
            {STEP_ORDER.map((step) => (
              <span key={step}>{STEP_LABELS[step]}</span>
            ))}
          </div>
        </div>

        {error && (
          <Card className="border-red-200 bg-red-50 mb-6">
            <CardContent className="pt-6">
              <p className="text-red-700">{error}</p>
            </CardContent>
          </Card>
        )}

        {(currentStep === 'upload' || currentStep === 'prep') && (
          <UploadStep onUpload={handleUpload} isLoading={isLoading} />
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
          <CountryStep
            countryDetection={countryDetection}
            schemaAutoValidated={schemaAutoValidated}
            onDismissBanner={dismissSchemaBanner}
            onConfirm={validateCountry}
            isLoading={isLoading}
          />
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