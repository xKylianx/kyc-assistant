'use client';

import { complianceScaleColor, qualityLabel } from '@/src/lib/kycFields';

interface ComplianceGaugeProps {
  rate: number;
  quality: string;
  size?: number;
}

export function ComplianceGauge({ rate, quality, size = 140 }: ComplianceGaugeProps) {
  const strokeWidth = 12;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const clamped = Math.max(0, Math.min(100, rate));
  const offset = circumference - (clamped / 100) * circumference;
  const color = complianceScaleColor(clamped);
  const { label, emoji } = qualityLabel(quality);

  return (
    <div className="flex flex-col items-center">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="#F1EFE8"
            strokeWidth={strokeWidth}
            fill="none"
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={color}
            strokeWidth={strokeWidth}
            fill="none"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 0.6s ease' }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-bold text-black">{clamped.toFixed(1)}%</span>
        </div>
      </div>
      <span
        className="mt-2 text-xs font-semibold px-2.5 py-1 rounded-full"
        style={{ backgroundColor: `${color}22`, color }}
      >
        {emoji} {label}
      </span>
    </div>
  );
}