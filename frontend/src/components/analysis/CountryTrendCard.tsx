'use client';

import { useEffect, useState } from 'react';
import { ApiService } from '@/src/services/api';
import { Globe, TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface CountryTrendCardProps {
  country: string;
  currentFileId: string;
  currentComplianceRate: number;
  rowsAnalyzed: number;
}

export function CountryTrendCard({
  country,
  currentFileId,
  currentComplianceRate,
  rowsAnalyzed,
}: CountryTrendCardProps) {
  const [previousRate, setPreviousRate] = useState<number | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let cancelled = false;
    ApiService.getAnalysisHistory(1, 5, country, 'desc')
      .then((data) => {
        if (cancelled) return;
        const previous = data.analyses.find(
          (a) => a.fileId !== currentFileId && a.complianceRate != null
        );
        setPreviousRate(previous?.complianceRate ?? null);
      })
      .catch(() => setPreviousRate(null))
      .finally(() => !cancelled && setLoaded(true));
    return () => {
      cancelled = true;
    };
  }, [country, currentFileId]);

  const delta = previousRate != null ? currentComplianceRate - previousRate : null;

  return (
    <div className="flex items-center gap-4 border border-gray-200 rounded-lg p-4">
      <div className="w-11 h-11 rounded-full bg-orange-50 flex items-center justify-center flex-shrink-0">
        <Globe className="w-5 h-5 text-orange" />
      </div>
      <div className="flex-1">
        <p className="text-sm font-bold text-black">{country}</p>
        <p className="text-xs text-gray-500 mt-0.5">
          {rowsAnalyzed.toLocaleString('fr-FR')} lignes actives analysées
        </p>
      </div>
      {loaded && delta != null && (
        <div className="text-right">
          <p
            className={`text-sm font-bold flex items-center gap-1 justify-end ${
              delta > 0 ? 'text-green-600' : delta < 0 ? 'text-red-600' : 'text-gray-500'
            }`}
          >
            {delta > 0 ? (
              <TrendingUp className="w-4 h-4" />
            ) : delta < 0 ? (
              <TrendingDown className="w-4 h-4" />
            ) : (
              <Minus className="w-4 h-4" />
            )}
            {delta > 0 ? '+' : ''}
            {delta.toFixed(1)} pts
          </p>
          <p className="text-xs text-gray-400 mt-0.5">vs analyse précédente</p>
        </div>
      )}
    </div>
  );
}