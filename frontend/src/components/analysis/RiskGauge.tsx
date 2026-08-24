'use client';

import { useEffect, useRef } from 'react';

interface RiskGaugeProps {
  riskScore: number; // 0-100
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
}

export function RiskGauge({ riskScore, riskLevel }: RiskGaugeProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = 80;

    // Couleur selon le niveau de risque
    const colors = {
      LOW: '#10b981',
      MEDIUM: '#f59e0b',
      HIGH: '#ef4444',
      CRITICAL: '#7c2d12',
    };

    const color = colors[riskLevel];
    const angle = (riskScore / 100) * Math.PI;

    // Fond gris
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, 0, Math.PI, true);
    ctx.strokeStyle = '#e5e7eb';
    ctx.lineWidth = 12;
    ctx.stroke();

    // Arc de risque
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, 0, angle, false);
    ctx.strokeStyle = color;
    ctx.lineWidth = 12;
    ctx.lineCap = 'round';
    ctx.stroke();

    // Texte du score
    ctx.font = 'bold 32px Inter';
    ctx.fillStyle = '#1f2937';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(`${riskScore}%`, centerX, centerY + 20);

    // Texte du niveau
    ctx.font = '14px Inter';
    ctx.fillStyle = color;
    ctx.fillText(riskLevel, centerX, centerY + 50);
  }, [riskScore, riskLevel]);

  return (
    <div className="flex flex-col items-center">
      <canvas
        ref={canvasRef}
        width={200}
        height={120}
        className="mb-4"
      />
      <p className="text-sm text-gray-600">Score de risque</p>
    </div>
  );
}