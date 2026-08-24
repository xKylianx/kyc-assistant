'use client';

import { AnalysisReport } from '@/src/types/analysis';
import { Card, CardContent, CardHeader, CardTitle } from '@/src/components/ui/card';
import { Button } from '@/src/components/ui/button';
import { CheckCircle, AlertCircle, Download, RotateCcw } from 'lucide-react';

interface ReportStepProps {
  report: AnalysisReport;
  onReset: () => void;
}

export function ReportStep({ report, onReset }: ReportStepProps) {
  const { analysis, summary } = report;

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'LOW': return 'bg-green-100 text-green-800';
      case 'MEDIUM': return 'bg-yellow-100 text-yellow-800';
      case 'HIGH': return 'bg-orange-100 text-orange-800';
      case 'CRITICAL': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const handleExportPdf = () => {
    alert('Export PDF : endpoint backend à implémenter.');
  };

  return (
    <div className="space-y-6">
      <Card className="border-green-500 bg-green-50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CheckCircle className="w-6 h-6 text-green-600" />
            Analyse complétée avec succès
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-700">
            Votre fichier <span className="font-semibold">{analysis.fileName}</span> a été analysé avec succès.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle className="text-base">Résumé exécutif</CardTitle></CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-orange-50 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-1">Score de risque</p>
              <p className="text-3xl font-bold text-orange-600">{analysis.riskScore}%</p>
              <span className={'inline-block mt-2 px-3 py-1 rounded-full text-sm font-semibold ' + getRiskColor(analysis.riskLevel)}>
                {analysis.riskLevel}
              </span>
            </div>
            <div className="bg-blue-50 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-1">Score de conformité</p>
              <p className="text-3xl font-bold text-blue-600">{summary.complianceScore}%</p>
              <p className="text-xs text-gray-600 mt-2">Données conformes</p>
            </div>
            <div className="bg-purple-50 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-1">Lignes analysées</p>
              <p className="text-3xl font-bold text-purple-600">{analysis.analyzedRows.toLocaleString()}</p>
              <p className="text-xs text-gray-600 mt-2">sur {analysis.totalRows.toLocaleString()}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle className="text-base">Statistiques des anomalies</CardTitle></CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-red-50 rounded-lg"><p className="text-2xl font-bold text-red-600">{summary.criticalAnomalies}</p><p className="text-xs text-gray-600 mt-1">Critiques</p></div>
            <div className="text-center p-4 bg-orange-50 rounded-lg"><p className="text-2xl font-bold text-orange-600">{summary.warningAnomalies}</p><p className="text-xs text-gray-600 mt-1">Avertissements</p></div>
            <div className="text-center p-4 bg-blue-50 rounded-lg"><p className="text-2xl font-bold text-blue-600">{summary.infoAnomalies}</p><p className="text-xs text-gray-600 mt-1">Infos</p></div>
            <div className="text-center p-4 bg-gray-50 rounded-lg"><p className="text-2xl font-bold text-gray-600">{summary.affectedRows}</p><p className="text-xs text-gray-600 mt-1">Lignes affectées</p></div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle className="text-base">Détails de l'analyse</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex justify-between items-center py-2 border-b"><span className="text-gray-600">Fichier analysé</span><span className="font-semibold text-gray-900">{analysis.fileName}</span></div>
            <div className="flex justify-between items-center py-2 border-b"><span className="text-gray-600">Pays détecté</span><span className="font-semibold text-gray-900">{analysis.detectedCountry}</span></div>
            <div className="flex justify-between items-center py-2 border-b"><span className="text-gray-600">Schéma détecté</span><span className="font-semibold text-gray-900">{analysis.detectedSchema === 'orange_money' ? 'Orange Money' : 'Autre'}</span></div>
            <div className="flex justify-between items-center py-2"><span className="text-gray-600">Date d'analyse</span><span className="font-semibold text-gray-900">{new Date(analysis.createdAt).toLocaleDateString('fr-FR')}</span></div>
          </div>
        </CardContent>
      </Card>

      {analysis.riskScore > 50 && (
        <Card className="border-orange-200 bg-orange-50">
          <CardHeader><CardTitle className="text-base flex items-center gap-2"><AlertCircle className="w-5 h-5 text-orange-600" />Recommandations</CardTitle></CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm text-gray-700">
              <li>• Vérifier les anomalies détectées avant de traiter les données</li>
              <li>• Corriger les formats invalides</li>
              <li>• Valider les statuts non reconnus</li>
            </ul>
          </CardContent>
        </Card>
      )}

      <div className="flex gap-4 justify-end">
        <Button variant="outline" onClick={onReset} className="flex items-center gap-2">
          <RotateCcw className="w-4 h-4" /> Analyser un autre fichier
        </Button>
        <Button onClick={handleExportPdf} className="bg-orange-500 hover:bg-orange-600 text-white flex items-center gap-2">
          <Download className="w-4 h-4" /> Télécharger le rapport PDF
        </Button>
      </div>
    </div>
  );
}
