'use client';

import { KYCAnalysisResult } from '@/src/types/analysis';
import { Card, CardContent, CardHeader, CardTitle } from '@/src/components/ui/card';
import { Button } from '@/src/components/ui/button';
import { AnomalyCard } from '@/src/components/analysis/AnomalyCard';
import { fieldLabel, complianceColor, riskBadgeClasses } from '@/src/lib/kycFields';

interface AnalysisStepProps {
  result: KYCAnalysisResult;
  onComplete: () => void;
  isLoading: boolean;
}

export function AnalysisStep({ result, onComplete, isLoading }: AnalysisStepProps) {
  const fieldEntries = Object.entries(result.detailedResults).filter(
    ([, data]) => data?.status === 'completed' && typeof data.complianceRate === 'number'
  );

  // Toutes les anomalies aplaties, triées par sévérité (error d'abord)
  const severityOrder = { error: 0, warning: 1, info: 2 };
  const allAnomalies = Object.entries(result.anomaliesByField)
    .flatMap(([field, anomalies]) => anomalies.map((a) => ({ field, ...a })))
    .sort((a, b) => severityOrder[a.severity] - severityOrder[b.severity]);

  return (
    <div className="space-y-6">
      {/* Cartes de synthèse */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-gray-600 mb-1">Conformité globale</p>
            <p className="text-2xl font-semibold text-gray-900">
              {result.overallComplianceRate}%
            </p>
          </CardContent>
        </Card>

        <Card className={result.overallRiskLevel !== 'LOW' ? 'border-yellow-200 bg-yellow-50' : ''}>
          <CardContent className="pt-6">
            <p className="text-sm text-gray-600 mb-1">Niveau de risque</p>
            <span
              className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${riskBadgeClasses(
                result.overallRiskLevel
              )}`}
            >
              {result.overallRiskLevel}
            </span>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-gray-600 mb-1">Lignes actives analysées</p>
            <p className="text-2xl font-semibold text-gray-900">
              {result.activeRowsCount.toLocaleString('fr-FR')}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Conformité par champ */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Conformité par champ KYC</CardTitle>
        </CardHeader>
        <CardContent>
          {fieldEntries.length === 0 ? (
            <p className="text-sm text-gray-500">Aucun champ analysé.</p>
          ) : (
            <div className="space-y-1">
              {fieldEntries.map(([field, data]) => {
                const rate = data.complianceRate as number;
                const colors = complianceColor(rate);
                return (
                  <div
                    key={field}
                    className="grid grid-cols-[130px_1fr_60px] items-center gap-3 py-2 border-b last:border-b-0"
                  >
                    <span className="text-sm text-gray-900">{fieldLabel(field)}</span>
                    <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${colors.bar}`}
                        style={{ width: `${Math.min(rate, 100)}%` }}
                      />
                    </div>
                    <span className={`text-sm text-right ${colors.text}`}>{rate}%</span>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Anomalies */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            Anomalies détectées ({result.totalAnomalies})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {allAnomalies.length === 0 ? (
            <div className="flex items-center gap-3 p-4 bg-green-50 rounded-lg">
              <div>
                <p className="font-semibold text-green-900">Aucune anomalie détectée</p>
                <p className="text-sm text-green-700">Les données semblent conformes</p>
              </div>
            </div>
          ) : (
            <div className="space-y-2">
              {allAnomalies.map((a, idx) => (
                <AnomalyCard
                  key={`${a.field}-${a.type}-${idx}`}
                  field={a.field}
                  type={a.type}
                  count={a.count}
                  percentage={a.percentage}
                  severity={a.severity}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <div className="flex justify-end">
        <Button
          onClick={onComplete}
          disabled={isLoading}
          className="bg-orange-500 hover:bg-orange-600 text-white"
        >
          {isLoading ? 'Génération du rapport...' : 'Générer le rapport'}
        </Button>
      </div>
    </div>
  );
}