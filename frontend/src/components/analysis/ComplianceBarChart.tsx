'use client';

import { fieldLabel, complianceScaleColor } from '@/src/lib/kycFields';

interface ComplianceBarChartProps {
  data: Array<{ field: string; rate: number }>;
}

export function ComplianceBarChart({ data }: ComplianceBarChartProps) {
  return (
    <div>
      <div className="flex items-end gap-3 h-56 px-2">
        {data.map(({ field, rate }) => {
          const color = complianceScaleColor(rate);
          return (
            <div key={field} className="flex-1 flex flex-col items-center h-full justify-end">
              <span className="text-xs font-bold text-gray-700 mb-1">{rate}%</span>
              <div
                className="w-full rounded-t-md transition-all"
                style={{
                  height: `${Math.max(rate, 2)}%`,
                  backgroundColor: color,
                }}
              />
            </div>
          );
        })}
      </div>
      <div className="flex gap-3 px-2 mt-2">
        {data.map(({ field }) => (
          <div key={field} className="flex-1 text-center">
            <span className="text-xs font-bold text-gray-700 block truncate">
              {fieldLabel(field)}
            </span>
          </div>
        ))}
      </div>

      {/* Légende de l'échelle de couleur */}
      <div className="flex items-center gap-2 mt-8 justify-end">
        <span className="text-xs text-gray-500">0</span>
        <div
          className="w-24 h-2 rounded-full"
          style={{
            background: 'linear-gradient(to right, #E24B4A, #FFDC00, #50BE87)',
          }}
        />
        <span className="text-xs text-gray-500">100</span>
      </div>
    </div>
  );
}