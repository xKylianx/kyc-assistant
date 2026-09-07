'use client';

import { KYCAnalysisResult } from '@/src/types/analysis';
import { Card, CardContent, CardHeader, CardTitle } from '@/src/components/ui/card';
import { Button } from '@/src/components/ui/button';
import { AnomalyCard } from '@/src/components/analysis/AnomalyCard';
import { ComplianceGauge } from '@/src/components/analysis/ComplianceGauge';
import { ComplianceBarChart } from '@/src/components/analysis/ComplianceBarChart';
import { fieldLabel, riskBadgeClasses } from '@/src/lib/kycFields';
import { CheckCircle } from 'lucide-react';

interface AnalysisStepProps {
  result: KYCAnalysisResult;
  onComplete: () => void;
  isLoading: boolean;
}

export function AnalysisStep({ result, onComplete, isLoading }: AnalysisStepProps) {
  const fieldEntries = Object.entries(result.detailedResults).filter(
    ([, data]) => data?.status === 'completed' && typeof data.complianceRate === 'number'
  );

  const chartData = fieldEntries.map(([field, data]) => ({
    field,
    rate: data.complianceRate as number,
  }));

  const severityOrder = { error: 0, warning: 1, info: 2 };
  const allAnomalies = Object.entries(result.anomaliesByField)
    .flatMap(([field, anomalies]) => anomalies.map((a) => ({ field, ...a })))
    .sort((a, b) => severityOrder[a.severity] - severityOrder[b.severity]);

  return (
    <div className="space-y-6">
      {/* Synthèse : jauge + stats */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row items-center gap-8">
            <ComplianceGauge
              rate={result.overallComplianceRate}
              quality={result.executiveSummary.overallDataQuality}
            />
            <div className="flex-1 grid grid-cols-1 sm:grid-cols-2 gap-4 w-full">
              <div>
                <p className="text-sm text-gray-600 mb-1">Niveau de risque</p>
                <span
                  className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${riskBadgeClasses(
                    result.overallRiskLevel
                  )}`}
                >
                  {result.overallRiskLevel}
                </span>
              </div>
              <div>
                <p className="text-sm text-gray-600 mb-1">Lignes actives analysées</p>
                <p className="text-2xl font-semibold text-black">
                  {result.activeRowsCount.toLocaleString('fr-FR')}
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Histogramme vertical par champ */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Conformité par champ KYC</CardTitle>
        </CardHeader>
        <CardContent>
          {chartData.length === 0 ? (
            <p className="text-sm text-gray-500">Aucun champ analysé.</p>
          ) : (
            <ComplianceBarChart data={chartData} />
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
              <CheckCircle className="w-6 h-6 text-green-600 flex-shrink-0" />
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
          className="bg-orange hover:bg-orange-600 text-black font-semibold"
        >
          {isLoading ? 'Génération du rapport...' : 'Générer le rapport'}
        </Button>
      </div>
    </div>
  );
}