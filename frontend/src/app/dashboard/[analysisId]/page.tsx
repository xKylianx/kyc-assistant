'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Layout } from '@/src/components/common';
import { ApiService } from '@/src/services/api';
import { AnalysisReport } from '@/src/types/analysis';
import { ReportStep } from '@/src/components/upload/ReportStep';
import { Card, CardContent } from '@/src/components/ui/card';

export default function AnalysisDetailPage() {
  const params = useParams<{ analysisId: string }>();
  const router = useRouter();
  const [report, setReport] = useState<AnalysisReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isExporting, setIsExporting] = useState(false);

  useEffect(() => {
    if (!params.analysisId) return;
    ApiService.generateReport(params.analysisId)
      .then(setReport)
      .catch((err) => setError(err instanceof Error ? err.message : 'Impossible de charger le rapport'));
  }, [params.analysisId]);

  const handleExportPdf = async () => {
    if (!params.analysisId) return;
    setIsExporting(true);
    try {
      const blob = await ApiService.exportReportPdf(params.analysisId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `kyc-report-${params.analysisId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur lors de l'export PDF");
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <Layout>
      <div className="max-w-6xl mx-auto">
        {error && (
          <Card className="border-red-200 bg-red-50">
            <CardContent className="pt-6 text-red-700">{error}</CardContent>
          </Card>
        )}
        {!error && !report && (
          <Card>
            <CardContent className="py-12 text-center text-gray-600">Chargement du rapport...</CardContent>
          </Card>
        )}
        {report && (
          <ReportStep
            report={report}
            onReset={() => router.push('/dashboard')}
            onExportPdf={handleExportPdf}
            isExporting={isExporting}
          />
        )}
      </div>
    </Layout>
  );
}