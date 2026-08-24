'use client';

import { AlertCircle, CheckCircle, AlertTriangle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/src/components/ui/card';

interface AnomalyCardProps {
  title: string;
  description: string;
  severity: 'info' | 'warning' | 'error';
  confidence: number; // 0-100
}

export function AnomalyCard({
  title,
  description,
  severity,
  confidence,
}: AnomalyCardProps) {
  const icons = {
    info: <CheckCircle className="w-5 h-5 text-blue-500" />,
    warning: <AlertTriangle className="w-5 h-5 text-yellow-500" />,
    error: <AlertCircle className="w-5 h-5 text-red-500" />,
  };

  const borderColors = {
    info: 'border-l-4 border-l-blue-500',
    warning: 'border-l-4 border-l-yellow-500',
    error: 'border-l-4 border-l-red-500',
  };

  const bgColors = {
    info: 'bg-blue-50',
    warning: 'bg-yellow-50',
    error: 'bg-red-50',
  };

  return (
    <Card className={`${borderColors[severity]} ${bgColors[severity]}`}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            {icons[severity]}
            <div>
              <CardTitle className="text-base">{title}</CardTitle>
              <p className="text-sm text-gray-600 mt-1">{description}</p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-sm font-semibold text-gray-900">
              {confidence}%
            </p>
            <p className="text-xs text-gray-500">confiance</p>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all ${
              severity === 'error'
                ? 'bg-red-500'
                : severity === 'warning'
                  ? 'bg-yellow-500'
                  : 'bg-blue-500'
            }`}
            style={{ width: `${confidence}%` }}
          />
        </div>
      </CardContent>
    </Card>
  );
}
