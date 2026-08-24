'use client';

import { useState } from 'react';
import { SchemaDetection } from '../../types/analysis';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Globe, Database } from 'lucide-react';

interface SchemaStepProps {
  schema: SchemaDetection;
  onConfirm: (selectedColumns: Record<string, string>) => void;
  isLoading: boolean;
}

export function SchemaStep({ schema, onConfirm, isLoading }: SchemaStepProps) {
  const [selectedColumns, setSelectedColumns] = useState<Record<string, string>>(
    schema.selectedColumns as Record<string, string>
  );

  const handleColumnChange = (key: string, value: string) => {
    setSelectedColumns((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  const handleConfirm = () => {
    const filteredColumns = Object.fromEntries(
      Object.entries(selectedColumns).filter(([, value]) => value && value.trim() !== '')
    );
    onConfirm(filteredColumns);
  };

  const requiredFields = [
    { key: 'nomColumn', label: '👤 Nom', icon: '👤' },
    { key: 'prenomColumn', label: '👤 Prénom', icon: '👤' },
    { key: 'msisdnColumn', label: '📱 MSISDN', icon: '📱' },
    { key: 'idTypeColumn', label: '🆔 Type d\'ID', icon: '🆔' },
    { key: 'idNumberColumn', label: '🆔 Numéro d\'ID', icon: '🆔' },
    { key: 'dobColumn', label: '📅 Date de naissance', icon: '📅' },
    { key: 'addressColumn', label: '🏠 Adresse', icon: '🏠' },
    { key: 'cityColumn', label: '🏙️ Ville', icon: '🏙️' },
    { key: 'statusColumn', label: '✅ Statut', icon: '✅' },
  ];

  return (
    <div className="space-y-6">
      {/* Infos fichier */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-gray-600 mb-1">Nom du fichier</p>
            <p className="font-semibold text-gray-900 truncate">
              {schema.fileInfo.fileName}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-gray-600 mb-1">Nombre de lignes</p>
            <p className="text-2xl font-bold text-orange-600">
              {schema.fileInfo.rowCount.toLocaleString()}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-gray-600 mb-1">Délimiteur</p>
            <p className="font-semibold text-gray-900">
              {schema.fileInfo.delimiter === ',' ? 'Virgule (,)' : schema.fileInfo.delimiter}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Détection pays et schéma */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <Globe className="w-8 h-8 text-blue-600" />
              <div>
                <p className="text-sm text-gray-600">Pays détecté</p>
                <p className="text-xl font-bold text-blue-600">
                  {schema.detectedCountry}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-green-200 bg-green-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <Database className="w-8 h-8 text-green-600" />
              <div>
                <p className="text-sm text-gray-600">Schéma détecté</p>
                <p className="text-xl font-bold text-green-600">
                  {schema.detectedSchema === 'orange_money' ? 'Orange Money' : 'Autre'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Aperçu des données */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Aperçu des données</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  {schema.fileInfo.preview[0]?.map((col) => (
                    <th key={col} className="px-4 py-2 text-left font-semibold text-gray-900">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {schema.fileInfo.preview.slice(1, 4).map((row, idx) => (
                  <tr key={idx} className="border-b hover:bg-gray-50">
                    {row.map((cell, cellIdx) => (
                      <td key={cellIdx} className="px-4 py-2 text-gray-700">
                        {cell}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Sélection des colonnes KYC */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Sélectionner les colonnes KYC</CardTitle>
          <p className="text-sm text-gray-600 mt-2">
            Mappez les colonnes de votre fichier aux champs KYC obligatoires
          </p>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {requiredFields.map(({ key, label }) => (
              <div key={key}>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {label}
                </label>
                <select
                  value={selectedColumns[key] || ''}
                  onChange={(e) => handleColumnChange(key, e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
                >
                  <option value="">-- Sélectionner --</option>
                  {schema.availableColumns.map((col) => (
                    <option key={col} value={col}>
                      {col}
                    </option>
                  ))}
                </select>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Boutons */}
      <div className="flex gap-4 justify-end">
        <Button variant="outline">
          Retour
        </Button>
        <Button
          onClick={handleConfirm}
          disabled={isLoading}
          className="bg-orange-500 hover:bg-orange-600 text-white"
        >
          {isLoading ? 'Chargement...' : 'Continuer vers l\'analyse'}
        </Button>
      </div>
    </div>
  );
}