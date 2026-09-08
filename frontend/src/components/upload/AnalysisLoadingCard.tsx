'use client';

import { Loader2 } from 'lucide-react';
import { Card, CardContent } from '@/src/components/ui/card';

interface AnalysisLoadingCardProps {
  elapsedSeconds: number;
}

function formatElapsed(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return m > 0 ? `${m}m ${s.toString().padStart(2, '0')}s` : `${s}s`;
}

export function AnalysisLoadingCard({ elapsedSeconds }: AnalysisLoadingCardProps) {
  return (
    <Card>
      <CardContent className="pt-12 pb-12">
        <div className="flex flex-col items-center justify-center text-center">
          <div className="w-16 h-16 rounded-full bg-orange-50 flex items-center justify-center mb-4">
            <Loader2 className="w-7 h-7 text-orange animate-spin" />
          </div>
          <h3 className="text-lg font-semibold text-black mb-2">
            Analyse KYC en cours
          </h3>
          <p className="text-sm text-gray-600 mb-1">
            Temps écoulé : <span className="font-bold text-black">{formatElapsed(elapsedSeconds)}</span>
          </p>
          <p className="text-xs text-gray-500 max-w-sm mt-3">
            Sur les fichiers volumineux (plusieurs giga-octets), l'analyse
            peut prendre plusieurs minutes. Chaque champ KYC est contrôlé
            séquentiellement. Ne fermez pas cette page.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}