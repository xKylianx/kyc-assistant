'use client';

import { AnalysisReport } from '@/src/types/analysis';
import { Card, CardContent, CardHeader, CardTitle } from '@/src/components/ui/card';
import { Button } from '@/src/components/ui/button';
import { CheckCircle, Download, RotateCcw, AlertTriangle } from 'lucide-react';
import { riskBadgeClasses } from '@/src/lib/kycFields';
import { FieldDetailAccordion } from '@/src/components/analysis/FieldDetailAccordion';
import { KYC_FIELD_ORDER } from '@/src/lib/kycFields';

interface ReportStepProps {
  report: AnalysisReport;
  onReset: () => void;
  onExportPdf: () => void;
  isExporting: boolean;
}

const RECOMMENDATION_STYLES: Record<string, string> = {
  LOW: 'bg-green-50 text-green-800',
  MEDIUM: 'bg-yellow-50 text-yellow-800',
  HIGH: 'bg-orange-50 text-orange-800',
  CRITICAL: 'bg-red-50 text-red-800',
};

export function ReportStep({ report, onReset, onExportPdf, isExporting }: ReportStepProps) {
  console.log('DEBUG fieldResults:', report.fieldResults);
  console.log('DEBUG fieldResults keys:', Object.keys(report.fieldResults || {}));
  const recommendationStyle =
    RECOMMENDATION_STYLES[report.overallRiskLevel] || 'bg-gray-50 text-gray-800';

  return (
    <div className="space-y-6">
      {/* En-tête */}
      <Card className="border-green-500 bg-green-50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CheckCircle className="w-6 h-6 text-green-600" />
            Analyse terminée
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-700">
            <span className="font-semibold">{report.fileName || report.fileId}</span>
            {report.detectedCountry && <> · {report.detectedCountry}</>}
          </p>
        </CardContent>
      </Card>

      {/* Recommandation */}
      {report.executiveSummary.recommendation && (
        <div className={`rounded-lg p-4 flex items-start gap-3 ${recommendationStyle}`}>
          <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <p className="text-sm">{report.executiveSummary.recommendation}</p>
        </div>
      )}

      {/* Stats clés */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-gray-600 mb-1">Score de risque</p>
            <p className="text-2xl font-semibold text-gray-900">{report.overallRiskScore}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-gray-600 mb-1">Anomalies</p>
            <p className="text-2xl font-semibold text-gray-900">{report.summary.totalAnomalies}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-gray-600 mb-1">Enregistrements affectés (estimation)</p>
            <p className="text-2xl font-semibold text-gray-900">
              {report.summary.affectedRows.toLocaleString('fr-FR')}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Résumé exécutif */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Résumé exécutif</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex justify-between items-center py-2 border-b">
              <span className="text-gray-600">Qualité globale</span>
              <span className="font-semibold text-gray-900">
                {report.executiveSummary.overallDataQuality}
              </span>
            </div>
            <div className="flex justify-between items-center py-2 border-b">
              <span className="text-gray-600">Niveau de risque</span>
              <span
                className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${riskBadgeClasses(
                  report.overallRiskLevel
                )}`}
              >
                {report.overallRiskLevel}
              </span>
            </div>
            <div className="flex justify-between items-center py-2 border-b">
              <span className="text-gray-600">Taux de conformité</span>
              <span className="font-semibold text-gray-900">
                {report.overallComplianceRate}%
              </span>
            </div>
            <div className="flex justify-between items-center py-2 border-b">
              <span className="text-gray-600">Champs avec problèmes</span>
              <span className="font-semibold text-gray-900">
                {report.executiveSummary.fieldsWithIssues}
              </span>
            </div>
            <div className="flex justify-between items-center py-2">
              <span className="text-gray-600">Problèmes critiques</span>
              <span className="font-semibold text-gray-900">
                {report.executiveSummary.criticalIssues}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Détail par champ KYC */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Détail de l'analyse par champ</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {KYC_FIELD_ORDER
              .filter((field) => report.fieldResults[field])
              .map((field) => (
                <FieldDetailAccordion
                  key={field}
                  field={field}
                  data={report.fieldResults[field]}
                />
              ))}
          </div>
        </CardContent>
      </Card>

      {/* Boutons */}
      <div className="flex gap-4 justify-end">
        <Button variant="outline" onClick={onReset} className="flex items-center gap-2">
          <RotateCcw className="w-4 h-4" />
          Analyser un autre fichier
        </Button>
        <Button
          onClick={onExportPdf}
          disabled={isExporting}
          className="bg-orange-500 hover:bg-orange-600 text-white flex items-center gap-2"
        >
          <Download className="w-4 h-4" />
          {isExporting ? 'Export en cours...' : 'Exporter en PDF'}
        </Button>
      </div>
    </div>
  );
}