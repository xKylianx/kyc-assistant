'use client';

import { RiskGauge } from './RiskGauge';
import { AnomalyCard } from './AnomalyCard';
import { DocumentPreview } from './DocumentPreview';
import { Card, CardContent, CardHeader, CardTitle } from '@/src/components/ui/card';
import { CheckCircle, Clock } from 'lucide-react';

interface Anomaly {
  id: string;
  title: string;
  description: string;
  severity: 'info' | 'warning' | 'error';
  confidence: number;
}

interface AnalysisResultsProps {
  riskScore: number;
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  anomalies: Anomaly[];
  fileName: string;
  fileType: 'csv' | 'xlsx' | 'xls';
  rowsAnalyzed: number;
  analysisTime: number;
}

export function AnalysisResults({
  riskScore,
  riskLevel,
  anomalies,
  fileName,
  fileType,
  rowsAnalyzed,
  analysisTime,
}: AnalysisResultsProps) {
  return (
    <div className="space-y-6">
      {/* En-tête avec résumé */}
      <Card className="border-orange-500 bg-orange-50">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Analyse complétée</span>
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <Clock className="w-4 h-4" />
              {analysisTime}s
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-gray-600 mb-1">Score de risque</p>
              <p className="text-2xl font-bold text-orange-600">{riskScore}%</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">Niveau</p>
              <p className="text-2xl font-bold text-orange-600">{riskLevel}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">Lignes analysées</p>
              <p className="text-2xl font-bold text-orange-600">{rowsAnalyzed}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">Anomalies détectées</p>
              <p className="text-2xl font-bold text-orange-600">
                {anomalies.length}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Grille principale */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Colonne gauche : Aperçu et jauge */}
        <div className="lg:col-span-1 space-y-6">
          <DocumentPreview
            fileName={fileName}
            fileType={fileType}
            rowsAnalyzed={rowsAnalyzed}
          />
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Évaluation du risque</CardTitle>
            </CardHeader>
            <CardContent className="flex justify-center">
              <RiskGauge riskScore={riskScore} riskLevel={riskLevel} />
            </CardContent>
          </Card>
        </div>

        {/* Colonne droite : Anomalies */}
        <div className="lg:col-span-2">
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">
              Détails des anomalies
            </h3>
            {anomalies.length > 0 ? (
              anomalies.map((anomaly) => (
                <AnomalyCard
                  key={anomaly.id}
                  title={anomaly.title}
                  description={anomaly.description}
                  severity={anomaly.severity}
                  confidence={anomaly.confidence}
                />
              ))
            ) : (
              <Card className="border-green-200 bg-green-50">
                <CardContent className="pt-6">
                  <div className="flex items-center gap-3">
                    <CheckCircle className="w-6 h-6 text-green-500" />
                    <div>
                      <p className="font-semibold text-green-900">
                        Aucune anomalie détectée
                      </p>
                      <p className="text-sm text-green-700">
                        Les données semblent valides
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}