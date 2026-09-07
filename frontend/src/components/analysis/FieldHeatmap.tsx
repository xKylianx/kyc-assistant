'use client';

import { FieldAnalysisResult } from '@/src/types/analysis';
import { fieldLabel, complianceScaleColor, heatmapTextColor, KYC_FIELD_ORDER } from '@/src/lib/kycFields';

interface FieldHeatmapProps {
  fieldResults: Record<string, FieldAnalysisResult>;
}

export function FieldHeatmap({ fieldResults }: FieldHeatmapProps) {
  const entries = KYC_FIELD_ORDER.filter(
    (f) => fieldResults[f]?.status === 'completed' && typeof fieldResults[f].complianceRate === 'number'
  ).map((f) => ({ field: f, rate: fieldResults[f].complianceRate as number }));

  if (entries.length === 0) return null;

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
      {entries.map(({ field, rate }) => {
        const bg = complianceScaleColor(rate);
        const text = heatmapTextColor(rate);
        return (
          <div key={field} className="rounded-lg p-3 text-center" style={{ backgroundColor: bg }}>
            <p className="text-xs font-bold mb-1" style={{ color: text }}>
              {fieldLabel(field)}
            </p>
            <p className="text-lg font-bold" style={{ color: text }}>
              {rate}%
            </p>
          </div>
        );
      })}
    </div>
  );
}