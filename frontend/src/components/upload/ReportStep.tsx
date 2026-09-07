'use client';

import { AnalysisReport } from '@/src/types/analysis';
import { Card, CardContent, CardHeader, CardTitle } from '@/src/components/ui/card';
import { Button } from '@/src/components/ui/button';
import { CheckCircle, Download, RotateCcw, AlertTriangle, FileWarning, Users, ShieldAlert } from 'lucide-react';
import { riskBadgeClasses, complianceScaleColor, qualityLabel, KYC_FIELD_ORDER } from '@/src/lib/kycFields';
import { ComplianceGauge } from '@/src/components/analysis/ComplianceGauge';
import { FieldDetailAccordion } from '@/src/components/analysis/FieldDetailAccordion';
import { FieldHeatmap } from '@/src/components/analysis/FieldHeatmap';
import { ComplianceRadar } from '@/src/components/analysis/ComplianceRadar';
import { CountryTrendCard } from '@/src/components/analysis/CountryTrendCard';
import { fieldLabel } from '@/src/lib/kycFields';

interface ReportStepProps {
  report: AnalysisReport;
  onReset: () => void;
  onExportPdf: () => void;
  isExporting: boolean;
}

const RECOMMENDATION_STYLES: Record<string, string> = {
  LOW: 'bg-green-50 text-green-800 border-green-200',
  MEDIUM: 'bg-orange-50 text-orange-800 border-orange-200',
  HIGH: 'bg-orange-50 text-orange-900 border-orange-300',
  CRITICAL: 'bg-red-50 text-red-800 border-red-200',
};

export function ReportStep({ report, onReset, onExportPdf, isExporting }: ReportStepProps) {
  const recommendationStyle =
    RECOMMENDATION_STYLES[report.overallRiskLevel] || 'bg-gray-50 text-gray-800 border-gray-200';
  const { label: qualityText, emoji: qualityEmoji } = qualityLabel(report.executiveSummary.overallDataQuality);
  const riskScoreColor = complianceScaleColor(100 - report.overallRiskScore * 100);

  const radarData = KYC_FIELD_ORDER.filter(
    (f) => report.fieldResults[f]?.status === 'completed' && typeof report.fieldResults[f].complianceRate === 'number'
  ).map((f) => ({ field: f, rate: report.fieldResults[f].complianceRate as number }));

  return (
    <div className="space-y-6">
      {/* En-tête */}
      <Card className="border-green-200 bg-green-50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CheckCircle className="w-6 h-6 text-green-600" />
            Analyse terminée
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-700">
            <span className="font-semibold text-black">{report.fileName || report.fileId}</span>
            {report.detectedCountry && <> · {report.detectedCountry}</>}
          </p>
        </CardContent>
      </Card>

      {/* Recommandation */}
      {report.executiveSummary.recommendation && (
        <div className={`rounded-lg p-4 border flex items-start gap-3 ${recommendationStyle}`}>
          <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <p className="text-sm font-semibold">{report.executiveSummary.recommendation}</p>
        </div>
      )}

      {/* Tendance pays */}
      {report.detectedCountry && (
        <CountryTrendCard
          country={report.detectedCountry}
          currentFileId={report.fileId}
          currentComplianceRate={report.overallComplianceRate}
          rowsAnalyzed={report.summary.affectedRows}
        />
      )}

      {/* Heatmap champs */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Vue d'ensemble par champ</CardTitle>
        </CardHeader>
        <CardContent>
          <FieldHeatmap fieldResults={report.fieldResults} />
        </CardContent>
      </Card>

      {/* Synthèse visuelle : jauge + stats clés */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row items-center gap-8">
            <ComplianceGauge
              rate={report.overallComplianceRate}
              quality={report.executiveSummary.overallDataQuality}
            />

            <div className="flex-1 grid grid-cols-1 sm:grid-cols-3 gap-4 w-full">
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <ShieldAlert className="w-4 h-4 text-gray-500" />
                  <p className="text-sm text-gray-600">Score de risque</p>
                </div>
                <p className="text-2xl font-bold" style={{ color: riskScoreColor }}>
                  {report.overallRiskScore}
                </p>
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <FileWarning className="w-4 h-4 text-gray-500" />
                  <p className="text-sm text-gray-600">Anomalies</p>
                </div>
                <p className="text-2xl font-bold text-black">{report.summary.totalAnomalies}</p>
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Users className="w-4 h-4 text-gray-500" />
                  <p className="text-sm text-gray-600">Enreg. affectés (estim.)</p>
                </div>
                <p className="text-2xl font-bold text-black">
                  {report.summary.affectedRows.toLocaleString('fr-FR')}
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Radar de conformité */}
      {radarData.length >= 3 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Profil de conformité</CardTitle>
          </CardHeader>
          <CardContent>
            <ComplianceRadar data={radarData} />
          </CardContent>
        </Card>
      )}

      {/* Résumé exécutif */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Résumé exécutif</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="border rounded-lg p-4">
              <p className="text-xs text-gray-500 mb-1">Qualité globale des données</p>
              <p className="text-lg font-bold text-black flex items-center gap-1.5">
                {qualityEmoji} {qualityText}
              </p>
            </div>

            <div className="border rounded-lg p-4">
              <p className="text-xs text-gray-500 mb-1">Niveau de risque</p>
              <span
                className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${riskBadgeClasses(
                  report.overallRiskLevel
                )}`}
              >
                {report.overallRiskLevel}
              </span>
            </div>

            <div className="border rounded-lg p-4">
              <p className="text-xs text-gray-500 mb-1">Champs avec problèmes</p>
              <p className="text-lg font-bold text-black">
                {report.executiveSummary.fieldsWithIssues}
              </p>
            </div>

            <div className="border rounded-lg p-4">
              <p className="text-xs text-gray-500 mb-1">Problèmes critiques</p>
              <p className="text-lg font-bold text-black">
                {report.executiveSummary.criticalIssues}
              </p>
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
          className="bg-orange hover:bg-orange-600 text-black font-semibold flex items-center gap-2"
        >
          <Download className="w-4 h-4" />
          {isExporting ? 'Export en cours...' : 'Exporter en PDF'}
        </Button>
      </div>
    </div>
  );
}