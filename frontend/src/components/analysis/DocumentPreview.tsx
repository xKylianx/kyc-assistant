'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/src/components/ui/card';
import { FileText } from 'lucide-react';

interface DocumentPreviewProps {
  fileName: string;
  fileType: 'csv' | 'xlsx' | 'xls';
  rowsAnalyzed: number;
}

export function DocumentPreview({
  fileName,
  fileType,
  rowsAnalyzed,
}: DocumentPreviewProps) {
  const getFileIcon = () => {
    if (fileType === 'csv') {
      return '📄';
    }
    return '📊';
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <FileText className="w-5 h-5 text-blue-500" />
          {fileName}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center justify-center mb-4">
              <span className="text-4xl">{getFileIcon()}</span>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600 mb-2">Type de fichier</p>
              <p className="font-semibold text-gray-900 uppercase">{fileType}</p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="bg-blue-50 rounded-lg p-3 text-center">
              <p className="text-xs text-gray-600 mb-1">Lignes analysées</p>
              <p className="text-2xl font-bold text-blue-600">{rowsAnalyzed}</p>
            </div>
            <div className="bg-orange-50 rounded-lg p-3 text-center">
              <p className="text-xs text-gray-600 mb-1">Format</p>
              <p className="text-lg font-semibold text-orange-600">
                {fileType === 'csv' ? 'Texte' : 'Binaire'}
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}