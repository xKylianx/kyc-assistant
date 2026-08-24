'use client';

import { KYCAnalysisResult } from '@/src/types/analysis';
import { Card, CardContent, CardHeader, CardTitle } from '@/src/components/ui/card';
import { Button } from '@/src/components/ui/button';
import { AlertCircle, CheckCircle, AlertTriangle, Info } from 'lucide-react';

interface AnalysisStepProps {
  result: KYCAnalysisResult;
  onComplete: () => void;
  isLoading: boolean;
}

export function AnalysisStep({ result, onComplete, isLoading }: AnalysisStepProps) {
  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      case 'info':
        return <Info className="w-5 h-5 text-blue-500" />;
      default:
        return null;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'error':
        return 'border-l-4 border-l-red-500 bg-red-50';
      case 'warning':
        return 'border-l-4 border-l-yellow-500 bg-yellow-50';
      case 'info':
        return 'border-l-4 border-l-blue-500 bg-blue-50';
      default:
        return 'border-l-4 border-l-gray-500 bg-gray-50';
    }
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'LOW':
        return 'bg-green-100 text-green-800';
      case 'MEDIUM':
        return 'bg-yellow-100 text-yellow-800';
      case 'HIGH':
        return 'bg-orange-100 text-orange-800';
      case 'CRITICAL':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      {/* Résumé de l'analyse */}
      <Card className="border-orange-500 bg-orange-50">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Analyse KYC complétée</span>
            <span className="text-sm text-gray-600">{result.analysisTime}s</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-gray-600 mb-1">Score de risque</p>
              <p className="text-2xl font-bold text-orange-600">{result.riskScore}%</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">Niveau</p>
              <span className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${getRiskColor(result.riskLevel)}`}>
                {result.riskLevel}
              </span>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">Lignes analysées</p>
              <p className="text-2xl font-bold text-orange-600">
                {result.analyzedRows.toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">Anomalies</p>
              <p className="text-2xl font-bold text-orange-600">
                {result.anomalies.length}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Infos détection */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-gray-600 mb-1">Pays détecté</p>
            <p className="text-xl font-bold text-gray-900">{result.detectedCountry}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-gray-600 mb-1">Schéma</p>
            <p className="text-xl font-bold text-gray-900">
              {result.detectedSchema === 'orange_money' ? 'Orange Money' : 'Autre'}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Anomalies */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            Anomalies détectées ({result.anomalies.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {result.anomalies.length === 0 ? (
            <div className="flex items-center gap-3 p-4 bg-green-50 rounded-lg">
              <CheckCircle className="w-6 h-6 text-green-500" />
              <div>
                <p className="font-semibold text-green-900">Aucune anomalie détectée</p>
                <p className="text-sm text-green-700">Les données semblent valides</p>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              {result.anomalies.map((anomaly) => (
                <div
                  key={anomaly.id}
                  className={`p-4 rounded-lg ${getSeverityColor(anomaly.severity)}`}
                >
                  <div className="flex items-start gap-3">
                    {getSeverityIcon(anomaly.severity)}
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <p className="font-semibold text-gray-900">
                          {anomaly.anomalyType}
                        </p>
                        <span className="text-xs font-medium text-gray-600">
                          Ligne {anomaly.row}
                        </span>
                      </div>
                      <p className="text-sm text-gray-700 mb-2">
                        {anomaly.description}
                      </p>
                      <div className="flex items-center justify-between">
                        <p className="text-xs text-gray-600">
                          Colonne: <span className="font-mono">{anomaly.column}</span>
                        </p>
                        <p className="text-xs text-gray-600">
                          Confiance: <span className="font-semibold">{anomaly.confidence}%</span>
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Boutons */}
      <div className="flex gap-4 justify-end">
        <Button variant="outline">
          Retour
        </Button>
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