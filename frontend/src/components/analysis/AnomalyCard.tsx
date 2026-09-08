'use client';

import { AlertCircle, AlertTriangle, Info } from 'lucide-react';
import { fieldLabel } from '@/src/lib/kycFields';
import { Severity } from '@/src/types/analysis';

interface AnomalyCardProps {
  field: string;
  type: string;
  count: number;
  percentage: number;
  severity: Severity;
}

const SEVERITY_CONFIG: Record<Severity, { icon: typeof AlertCircle; bg: string; text: string }> = {
  error: { icon: AlertCircle, bg: 'bg-red-50', text: 'text-red-800' },
  warning: { icon: AlertTriangle, bg: 'bg-yellow-50', text: 'text-yellow-800' },
  info: { icon: Info, bg: 'bg-blue-50', text: 'text-blue-800' },
};

// Rend un type d'anomalie technique (ex. "non_numeric_values") lisible
function humanizeAnomalyType(type: string): string {
  return type.replace(/_/g, ' ').replace(/^\w/, (c) => c.toUpperCase());
}

export function AnomalyCard({ field, type, count, percentage, severity }: AnomalyCardProps) {
  const config = SEVERITY_CONFIG[severity] ?? SEVERITY_CONFIG.info;
  const Icon = config.icon;

  return (
    <div className={`flex items-start gap-3 rounded-lg p-3 ${config.bg}`}>
      <Icon className={`w-4 h-4 flex-shrink-0 mt-0.5 ${config.text}`} />
      <div className="flex-1 min-w-0">
        <p className={`text-sm font-semibold ${config.text}`}>
          {fieldLabel(field)} — {humanizeAnomalyType(type)}
        </p>
        <p className="text-xs text-gray-600 mt-0.5">
          {count.toLocaleString('fr-FR')} enregistrement{count > 1 ? 's' : ''} ({percentage}%)
        </p>
      </div>
    </div>
  );
}