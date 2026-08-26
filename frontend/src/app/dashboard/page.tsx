'use client';

import { useEffect, useState } from 'react';
import { Layout } from '@/src/components/common';
import { ApiService } from '@/src/services/api';
import { AnalysisHistoryItem } from '@/src/types/analysis';
import { Card, CardContent } from '@/src/components/ui/card';
import { Button } from '@/src/components/ui/button';
import { riskBadgeClasses } from '@/src/lib/kycFields';
import { Plus, TrendingUp, TrendingDown } from 'lucide-react';
import Link from 'next/link';

const PAGE_SIZE = 10;

export default function DashboardPage() {
  const [analyses, setAnalyses] = useState<AnalysisHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [countryFilter, setCountryFilter] = useState<string>('');
  const [sort, setSort] = useState<'asc' | 'desc'>('desc');

  useEffect(() => {
    loadAnalyses();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, countryFilter, sort]);

  const loadAnalyses = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await ApiService.getAnalysisHistory(
        page,
        PAGE_SIZE,
        countryFilter || undefined,
        sort
      );
      setAnalyses(data.analyses);
      setTotal(data.total);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erreur inconnue';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  // Tendance simple : compare la plus récente et la plus ancienne analyse
  // du pays filtré, sur la page actuellement chargée (approximation légère,
  // suffisante pour un indicateur visuel — pas une vraie série temporelle).
  const trend =
    countryFilter && analyses.length >= 2
      ? (analyses[0].complianceRate ?? 0) - (analyses[analyses.length - 1].complianceRate ?? 0)
      : null;

  const knownCountries = Array.from(
    new Set(analyses.map((a) => a.country).filter((c): c is string => !!c))
  );

  return (
    <Layout>
      <div className="max-w-5xl mx-auto">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 mb-2">Historique</h1>
            <p className="text-lg text-gray-600">
              Comparez l&apos;évolution du niveau de KYC entre vos analyses
            </p>
          </div>
          <Link href="/upload">
            <Button className="bg-orange-500 hover:bg-orange-600 text-white flex items-center gap-2">
              <Plus className="w-4 h-4" />
              Nouvelle analyse
            </Button>
          </Link>
        </div>

        <div className="flex items-center gap-3 mb-6">
          <select
            value={countryFilter}
            onChange={(e) => {
              setPage(1);
              setCountryFilter(e.target.value);
            }}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-orange-500"
          >
            <option value="">Tous les pays</option>
            {knownCountries.map((country) => (
              <option key={country} value={country}>
                {country}
              </option>
            ))}
          </select>
          <select
            value={sort}
            onChange={(e) => {
              setPage(1);
              setSort(e.target.value as 'asc' | 'desc');
            }}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-orange-500"
          >
            <option value="desc">Plus récent</option>
            <option value="asc">Plus ancien</option>
          </select>
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
              <p className="text-gray-600">Chargement de l&apos;historique...</p>
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
          <div className="space-y-2">
            <div className="grid grid-cols-[1fr_100px_100px_110px_100px] gap-2 px-3 text-xs text-gray-400">
              <span>Fichier</span>
              <span>Conformité</span>
              <span>Risque</span>
              <span>Lignes</span>
              <span>Date</span>
            </div>

            {analyses.map((a) => (
              <Card key={a.id}>
                <CardContent className="py-3 px-4">
                  <div className="grid grid-cols-[1fr_100px_100px_110px_100px] gap-2 items-center">
                    <span className="text-sm text-gray-900 truncate">
                      {a.fileName || a.fileId}
                    </span>
                    <span
                      className={`text-sm ${
                        a.complianceRate != null && a.complianceRate >= 90
                          ? 'text-green-600'
                          : a.complianceRate != null && a.complianceRate >= 80
                          ? 'text-yellow-600'
                          : 'text-red-600'
                      }`}
                    >
                      {a.complianceRate != null ? `${a.complianceRate}%` : '—'}
                    </span>
                    {a.riskLevel ? (
                      <span
                        className={`inline-block w-fit px-2 py-0.5 rounded text-xs font-semibold ${riskBadgeClasses(
                          a.riskLevel
                        )}`}
                      >
                        {a.riskLevel}
                      </span>
                    ) : (
                      <span className="text-sm text-gray-400">—</span>
                    )}
                    <span className="text-sm text-gray-900">
                      {a.rowsAnalyzed != null ? a.rowsAnalyzed.toLocaleString('fr-FR') : '—'}
                    </span>
                    <span className="text-xs text-gray-600">
                      {a.createdAt
                        ? new Date(a.createdAt).toLocaleDateString('fr-FR', {
                            day: '2-digit',
                            month: 'short',
                          })
                        : '—'}
                    </span>
                  </div>
                </CardContent>
              </Card>
            ))}

            {trend !== null && (
              <p className="text-sm text-gray-600 mt-4 flex items-center gap-1">
                {trend >= 0 ? (
                  <TrendingUp className="w-4 h-4 text-green-600" />
                ) : (
                  <TrendingDown className="w-4 h-4 text-red-600" />
                )}
                Conformité {trend >= 0 ? 'en hausse' : 'en baisse'} de{' '}
                {Math.abs(Math.round(trend * 10) / 10)} points sur les analyses affichées pour{' '}
                {countryFilter}.
              </p>
            )}

            {/* Pagination */}
            <div className="flex justify-center gap-2 mt-8">
              <Button variant="outline" onClick={() => setPage(Math.max(1, page - 1))} disabled={page === 1}>
                Précédent
              </Button>
              <span className="px-4 py-2 text-gray-600 text-sm">
                Page {page} sur {Math.max(1, Math.ceil(total / PAGE_SIZE))}
              </span>
              <Button
                variant="outline"
                onClick={() => setPage(page + 1)}
                disabled={page >= Math.ceil(total / PAGE_SIZE)}
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