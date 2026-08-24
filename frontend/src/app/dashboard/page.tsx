'use client';

import { useEffect, useState } from 'react';
import { Layout } from '@/src/components/common';
import { ApiService } from '@/src/services/api';
import { AnalysisResponse, AnalysisHistory } from '@/src/types/analysis';
import { Card, CardContent, CardHeader, CardTitle } from '@/src/components/ui/card';
import { Button } from '@/src/components/ui/button';
import { Trash2, Eye, Download } from 'lucide-react';
import Link from 'next/link';

export default function DashboardPage() {
  const [analyses, setAnalyses] = useState<AnalysisResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  const pageSize = 10;

  useEffect(() => {
    loadAnalyses();
  }, [page]);

  const loadAnalyses = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await ApiService.getAnalysisHistory(page, pageSize);
      setAnalyses(data.analyses);
      setTotal(data.total);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erreur inconnue';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (analysisId: string) => {
    if (!confirm('Êtes-vous sûr de vouloir supprimer cette analyse ?')) {
      return;
    }

    try {
      await ApiService.deleteAnalysis(analysisId);
      setAnalyses(analyses.filter((a) => a.id !== analysisId));
    } catch (err) {
      alert('Erreur lors de la suppression');
    }
  };

  const handleExport = async (analysisId: string, fileName: string) => {
    try {
      const blob = await ApiService.exportAnalysisPdf(analysisId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${fileName}-report.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      alert('Erreur lors de l\'export');
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
    <Layout>
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Dashboard</h1>
          <p className="text-lg text-gray-600">
            Historique de vos analyses de fichiers
          </p>
        </div>

        {error && (
          <Card className="border-red-200 bg-red-50 mb-6">
            <CardContent className="pt-6">
              <p className="text-red-700">{error}</p>
            </CardContent>
          </Card>
        )}

        {isLoading ? (
          <Card>
            <CardContent className="pt-12 pb-12 text-center">
              <div className="inline-block animate-spin mb-4">
                <div className="w-8 h-8 border-4 border-gray-200 border-t-orange-500 rounded-full" />
              </div>
              <p className="text-gray-600">Chargement des analyses...</p>
            </CardContent>
          </Card>
        ) : analyses.length === 0 ? (
          <Card>
            <CardContent className="pt-12 pb-12 text-center">
              <p className="text-gray-600 mb-6">Aucune analyse trouvée</p>
              <Link href="/upload">
                <Button className="bg-orange-500 hover:bg-orange-600 text-white">
                  Analyser un fichier
                </Button>
              </Link>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {analyses.map((analysis) => (
              <Card key={analysis.id} className="hover:shadow-lg transition-shadow">
                <CardContent className="pt-6">
                  <div className="grid grid-cols-1 md:grid-cols-6 gap-4 items-center">
                    <div>
                      <p className="text-sm text-gray-600">Fichier</p>
                      <p className="font-semibold text-gray-900 truncate">
                        {analysis.fileName}
                      </p>
                    </div>

                    <div>
                      <p className="text-sm text-gray-600">Type</p>
                      <p className="font-semibold text-gray-900 uppercase">
                        {analysis.fileType}
                      </p>
                    </div>

                    <div>
                      <p className="text-sm text-gray-600">Score de risque</p>
                      <p className="text-2xl font-bold text-orange-600">
                        {analysis.riskScore}%
                      </p>
                    </div>

                    <div>
                      <p className="text-sm text-gray-600">Niveau</p>
                      <span
                        className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${getRiskColor(
                          analysis.riskLevel
                        )}`}
                      >
                        {analysis.riskLevel}
                      </span>
                    </div>

                    <div>
                      <p className="text-sm text-gray-600">Lignes</p>
                      <p className="text-lg font-semibold text-gray-900">
                        {analysis.rowsAnalyzed}
                      </p>
                    </div>

                    <div>
                      <p className="text-sm text-gray-600">Date</p>
                      <p className="text-sm text-gray-900">
                        {new Date(analysis.createdAt).toLocaleDateString('fr-FR')}
                      </p>
                    </div>
                  </div>

                  <div className="mt-4 flex gap-2 justify-end">
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex items-center gap-2"
                    >
                      <Eye className="w-4 h-4" />
                      Détails
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex items-center gap-2"
                      onClick={() => handleExport(analysis.id, analysis.fileName)}
                    >
                      <Download className="w-4 h-4" />
                      Export
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex items-center gap-2 text-red-600 hover:text-red-700"
                      onClick={() => handleDelete(analysis.id)}
                    >
                      <Trash2 className="w-4 h-4" />
                      Supprimer
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}

            {/* Pagination */}
            <div className="flex justify-center gap-2 mt-8">
              <Button
                variant="outline"
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page === 1}
              >
                Précédent
              </Button>
              <span className="px-4 py-2 text-gray-600">
                Page {page} sur {Math.ceil(total / pageSize)}
              </span>
              <Button
                variant="outline"
                onClick={() => setPage(page + 1)}
                disabled={page >= Math.ceil(total / pageSize)}
              >
                Suivant
              </Button>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}