'use client';

import { complianceScaleColor } from '@/src/lib/kycFields';

interface MiniDonutProps {
  rate: number;
  size?: number;
  strokeWidth?: number;
}

export function MiniDonut({ rate, size = 32, strokeWidth = 5 }: MiniDonutProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const clamped = Math.max(0, Math.min(100, rate));
  const offset = circumference - (clamped / 100) * circumference;
  const color = complianceScaleColor(clamped);

  return (
    <svg width={size} height={size} className="-rotate-90 flex-shrink-0">
      <circle cx={size / 2} cy={size / 2} r={radius} stroke="#F1EFE8" strokeWidth={strokeWidth} fill="none" />
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
      />
    </svg>
  );
}