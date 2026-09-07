'use client';

import { useState } from 'react';
import { Upload, AlertCircle, Check } from 'lucide-react';
import { Card, CardContent } from '@/src/components/ui/card';

interface UploadStepProps {
  onUpload: (file: File) => void;
  isLoading: boolean;
  progress: number | null;
}

export function UploadStep({ onUpload, isLoading, progress }: UploadStepProps) {
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
    if (files && files[0]) validateAndUpload(files[0]);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) validateAndUpload(e.target.files[0]);
  };

  const validateAndUpload = (file: File) => {
    setError(null);

    const validExtensions = ['.csv', '.xlsx', '.xls'];
    const hasValidExtension = validExtensions.some((ext) => file.name.toLowerCase().endsWith(ext));
    if (!hasValidExtension) {
      setError('Format non supporté. Utilisez CSV ou Excel (XLSX, XLS).');
      return;
    }

    const maxSize = 20 * 1024 * 1024 * 1024; // 20 GB
    if (file.size > maxSize) {
      setError('Fichier trop volumineux. Limite : 20 GB');
      return;
    }

    onUpload(file);
  };

  const isUploading = progress !== null;

  return (
    <div className="space-y-6">
      <Card
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`border-2 border-dashed transition-colors ${
          isDragActive ? 'border-orange bg-orange-50' : 'border-gray-300 bg-gray-50 hover:border-orange'
        } ${isUploading ? '' : 'cursor-pointer'}`}
      >
        <CardContent className="pt-12 pb-12">
          {isUploading ? (
            <div className="flex flex-col items-center justify-center">
              <div className="w-16 h-16 rounded-full bg-orange-50 flex items-center justify-center mb-4">
                <Upload className="w-7 h-7 text-orange animate-pulse" />
              </div>
              <h3 className="text-lg font-semibold text-black mb-2">Envoi en cours...</h3>
              <p className="text-sm text-gray-600 mb-6">Ne fermez pas cette page</p>
              <div className="w-full max-w-sm">
                <div className="h-2.5 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-orange transition-all duration-300"
                    style={{ width: `${progress}%` }}
                  />
                </div>
                <p className="text-sm font-bold text-black text-center mt-2">{progress}%</p>
              </div>
            </div>
          ) : (
            <label className="flex flex-col items-center justify-center cursor-pointer">
              <div className="w-16 h-16 rounded-full bg-orange-50 flex items-center justify-center mb-4">
                <Upload className="w-7 h-7 text-orange" />
              </div>
              <h3 className="text-lg font-semibold text-black mb-2">Téléchargez votre fichier</h3>
              <p className="text-sm text-gray-600 mb-6">Glissez-déposez ou cliquez pour sélectionner</p>

              <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6 w-full max-w-sm">
                <div className="flex items-center gap-2 text-sm text-gray-700 mb-2">
                  <Check className="w-4 h-4 text-orange flex-shrink-0" />
                  <span>CSV, Excel (XLSX, XLS)</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-700">
                  <Check className="w-4 h-4 text-orange flex-shrink-0" />
                  <span>Jusqu'à 20 GB</span>
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
                className="px-6 py-2.5 bg-orange text-black rounded-md font-semibold hover:bg-orange-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={isLoading}
              >
                Sélectionner un fichier
              </button>
            </label>
          )}
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