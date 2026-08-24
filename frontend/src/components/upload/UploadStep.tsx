'use client';

import { useState } from 'react';
import { Upload, AlertCircle } from 'lucide-react';
import { Card, CardContent } from '@/src/components/ui/card';

interface UploadStepProps {
  onUpload: (file: File) => void;
  isLoading: boolean;
}

export function UploadStep({ onUpload, isLoading }: UploadStepProps) {
  const [isDragActive, setIsDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDrag = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(e.type === 'dragenter' || e.type === 'dragover');
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);

    const files = e.dataTransfer.files;
    if (files && files[0]) {
      validateAndUpload(files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndUpload(e.target.files[0]);
    }
  };

  const validateAndUpload = (file: File) => {
    setError(null);

    const validExtensions = ['.csv', '.xlsx', '.xls'];
    const hasValidExtension = validExtensions.some((ext) =>
      file.name.toLowerCase().endsWith(ext)
    );

    if (!hasValidExtension) {
      setError('Format non supporté. Utilisez CSV ou Excel (XLSX, XLS).');
      return;
    }

    const maxSize = 1024 * 1024 * 1024; // 1 GB
    if (file.size > maxSize) {
      setError('Fichier trop volumineux. Limite : 1 GB');
      return;
    }

    onUpload(file);
  };

  return (
    <div className="space-y-6">
      <Card
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`border-2 border-dashed transition-colors cursor-pointer ${
          isDragActive
            ? 'border-orange-500 bg-orange-50'
            : 'border-gray-300 bg-gray-50 hover:border-orange-400'
        }`}
      >
        <CardContent className="pt-12 pb-12">
          <label className="flex flex-col items-center justify-center cursor-pointer">
            <Upload className="w-12 h-12 text-orange-500 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Téléchargez votre fichier
            </h3>
            <p className="text-sm text-gray-600 mb-6">
              Glissez-déposez ou cliquez pour sélectionner
            </p>

            <div className="bg-white rounded-lg p-4 mb-6 w-full max-w-sm">
              <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
                <span>✓ CSV</span>
                <span>✓ Excel (XLSX, XLS)</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <span>✓ Jusqu'à 1 GB</span>
              </div>
            </div>

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
              {isLoading ? 'Chargement...' : 'Sélectionner un fichier'}
            </button>
          </label>
        </CardContent>
      </Card>

      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-6 h-6 text-red-500 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-semibold text-red-900">Erreur</h3>
                <p className="text-sm text-red-700 mt-1">{error}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}