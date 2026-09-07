'use client';

import { fieldLabel } from '@/src/lib/kycFields';

interface ComplianceRadarProps {
  data: Array<{ field: string; rate: number }>;
  size?: number;
}

export function ComplianceRadar({ data, size = 240 }: ComplianceRadarProps) {
  const center = size / 2;
  const maxRadius = size / 2 - 34;
  const n = data.length;

  if (n < 3) return null;

  const pointFor = (i: number, r: number): [number, number] => {
    const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
    return [center + r * Math.cos(angle), center + r * Math.sin(angle)];
  };

  const gridLevels = [0.33, 0.66, 1];
  const dataPath = data
    .map((d, i) => pointFor(i, (Math.max(d.rate, 0) / 100) * maxRadius).join(','))
    .join(' ');

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="mx-auto block">
      {gridLevels.map((lvl) => (
        <polygon
          key={lvl}
          points={data.map((_, i) => pointFor(i, lvl * maxRadius).join(',')).join(' ')}
          fill="none"
          stroke="#D6D6D6"
          strokeWidth={1}
        />
      ))}
      <polygon points={dataPath} fill="#FF7900" fillOpacity={0.25} stroke="#FF7900" strokeWidth={2} />
      {data.map((d, i) => {
        const [lx, ly] = pointFor(i, maxRadius + 18);
        return (
          <text
            key={d.field}
            x={lx}
            y={ly}
            textAnchor="middle"
            dominantBaseline="middle"
            fontSize={11}
            fontWeight="bold"
            fill="#000000"
          >
            {fieldLabel(d.field)}
          </text>
        );
      })}
    </svg>
  );
}