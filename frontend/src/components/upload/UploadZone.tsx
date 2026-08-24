'use client';

import { useCallback, useState } from 'react';
import { Upload, FileText } from 'lucide-react';
import { Card, CardContent } from '@/src/components/ui/card';

interface UploadZoneProps {
  onFileSelect: (file: File) => void;
  isLoading?: boolean;
}

export function UploadZone({ onFileSelect, isLoading = false }: UploadZoneProps) {
  const [isDragActive, setIsDragActive] = useState(false);

  const handleDrag = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      e.stopPropagation();
      if (e.type === 'dragenter' || e.type === 'dragover') {
        setIsDragActive(true);
      } else if (e.type === 'dragleave') {
        setIsDragActive(false);
      }
    },
    []
  );

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragActive(false);

      const files = e.dataTransfer.files;
      if (files && files[0]) {
        onFileSelect(files[0]);
      }
    },
    [onFileSelect]
  );

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files[0]) {
      onFileSelect(files[0]);
    }
  };

  return (
    <Card
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
      className={`border-2 border-dashed transition-colors cursor-pointer ${
        isDragActive
          ? 'border-orange-500 bg-orange-50'
          : 'border-gray-300 bg-gray-50 hover:border-orange-400'
      } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
    >
      <CardContent className="pt-12 pb-12">
        <label className="flex flex-col items-center justify-center cursor-pointer">
          <div className="mb-4">
            <Upload className="w-12 h-12 text-orange-500" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Téléchargez votre fichier de données
          </h3>
          <p className="text-sm text-gray-600 mb-4">
            Glissez-déposez votre fichier ou cliquez pour sélectionner
          </p>
          <div className="flex gap-4 text-xs text-gray-500 mb-6">
            <div className="flex items-center gap-1">
              <FileText className="w-4 h-4" />
              <span>CSV</span>
            </div>
            <div className="flex items-center gap-1">
              <FileText className="w-4 h-4" />
              <span>Excel (XLSX, XLS)</span>
            </div>
          </div>
          <p className="text-xs text-gray-500 mb-6">
            Taille maximale : 50 MB
          </p>
          <input
            type="file"
            onChange={handleChange}
            accept=".csv,.xlsx,.xls"
            className="hidden"
            disabled={isLoading}
          />
          <button
            type="button"
            className="px-6 py-2 bg-orange-500 text-white rounded-lg font-medium hover:bg-orange-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={isLoading}
          >
            {isLoading ? 'Analyse en cours...' : 'Sélectionner un fichier'}
          </button>
        </label>
      </CardContent>
    </Card>
  );
}