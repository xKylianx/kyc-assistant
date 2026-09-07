'use client';

import { useState } from 'react';
import { SchemaDetection, PrepResult, KYCColumnMapping } from '@/src/types/analysis';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Database, AlertTriangle } from 'lucide-react';

interface SchemaStepProps {
  schema: SchemaDetection;
  prepResult: PrepResult | null;
  onConfirm: (columns: KYCColumnMapping) => void;
  isLoading: boolean;
}

const REQUIRED_FIELDS: Array<{ key: keyof KYCColumnMapping; label: string }> = [
  { key: 'nomColumn', label: 'Nom' },
  { key: 'prenomColumn', label: 'Prénom' },
  { key: 'msisdnColumn', label: 'MSISDN' },
  { key: 'idTypeColumn', label: "Type d'ID" },
  { key: 'idNumberColumn', label: "Numéro d'ID" },
  { key: 'dobColumn', label: 'Date de naissance' },
  { key: 'addressColumn', label: 'Adresse' },
  { key: 'cityColumn', label: 'Ville' },
  { key: 'statusColumn', label: 'Statut' },
];

export function SchemaStep({ schema, prepResult, onConfirm, isLoading }: SchemaStepProps) {
  const [selectedColumns, setSelectedColumns] = useState<KYCColumnMapping>(
    schema.selectedColumns
  );

  const handleColumnChange = (key: keyof KYCColumnMapping, value: string) => {
    setSelectedColumns((prev) => ({ ...prev, [key]: value }));
  };

  const handleConfirm = () => {
    const filtered = Object.fromEntries(
      Object.entries(selectedColumns).filter(([, value]) => value && value.trim() !== '')
    ) as KYCColumnMapping;
    onConfirm(filtered);
  };

  const profile = prepResult?.datasetProfile;
  const previewRows = profile?.sampleRows ?? [];
  const previewColumns = profile?.columns ?? schema.allDetectedColumns;

  // Un champ obligatoire n'a pas de sélection valide : on bloque la confirmation
  const hasEmptyRequiredField = REQUIRED_FIELDS.some(
    ({ key }) => !selectedColumns[key] || selectedColumns[key]?.trim() === ''
  );

  return (
    <div className="space-y-6">
      {/* Infos fichier */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-gray-600 mb-1">Nombre de lignes</p>
            <p className="text-2xl font-bold text-orange">
              {profile?.rowCount != null ? profile.rowCount.toLocaleString('fr-FR') : '—'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-gray-600 mb-1">Colonnes détectées</p>
            <p className="text-2xl font-bold text-black">
              {schema.allDetectedColumns.length}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-gray-600 mb-1">Délimiteur</p>
            <p className="font-semibold text-black">
              {prepResult?.prepMeta?.csvDelimiterUsed === ','
                ? 'Virgule (,)'
                : prepResult?.prepMeta?.csvDelimiterUsed || '—'}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Détection du schéma */}
      <Card className={schema.isOrangeMoney ? 'border-brand-green/30 bg-brand-green/5' : 'border-orange-100 bg-orange-50'}>
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${
              schema.isOrangeMoney ? 'bg-brand-green/15' : 'bg-orange-100'
            }`}>
              <Database className={`w-5 h-5 ${schema.isOrangeMoney ? 'text-brand-green' : 'text-orange'}`} />
            </div>
            <div>
              <p className="text-sm text-gray-600">Schéma détecté</p>
              <p className={`text-xl font-bold ${schema.isOrangeMoney ? 'text-brand-green' : 'text-orange'}`}>
                {schema.isOrangeMoney ? 'Orange Money' : 'Schéma personnalisé'}
              </p>
              <p className="text-sm text-gray-600 mt-1">
                Confiance : {schema.confidenceScore}%
              </p>
            </div>
          </div>

          {!schema.isOrangeMoney && schema.missingRequiredColumns.length > 0 && (
            <div className="flex items-start gap-2 mt-4 pt-4 border-t border-orange-100">
              <AlertTriangle className="w-4 h-4 text-orange flex-shrink-0 mt-0.5" />
              <p className="text-sm font-semibold text-gray-900">
                Colonnes Orange Money non identifiées. Identification automatique
                des colonnes pour l'analyse KYC. Veuillez les valider ou les modifier.
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Aperçu des données */}
      {previewRows.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Aperçu des données</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    {previewColumns.map((col) => (
                      <th key={col} className="px-4 py-2 text-left font-semibold text-black whitespace-nowrap">
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {previewRows.slice(0, 5).map((row, idx) => (
                    <tr key={idx} className="border-b hover:bg-gray-50">
                      {previewColumns.map((col) => (
                        <td key={col} className="px-4 py-2 text-gray-700 whitespace-nowrap">
                          {String(row[col] ?? '')}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

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
            {REQUIRED_FIELDS.map(({ key, label }) => (
              <div key={key}>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {label}
                </label>
                <select
                  value={selectedColumns[key] || ''}
                  onChange={(e) => handleColumnChange(key, e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange focus:border-orange"
                >
                  <option value="">-- Sélectionner --</option>
                  {schema.allDetectedColumns.map((col) => (
                    <option key={col} value={col}>
                      {col}
                    </option>
                  ))}
                </select>
                {schema.columnReasoning?.[key] && (
                  <p className="text-xs font-semibold text-gray-700 mt-1">
                    {schema.columnReasoning[key]}
                  </p>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Boutons */}
      <div className="flex gap-4 justify-end items-center">
        {hasEmptyRequiredField && (
          <p className="text-sm text-gray-500">Mappez tous les champs avant de continuer</p>
        )}
        <Button
          onClick={handleConfirm}
          disabled={isLoading || hasEmptyRequiredField}
          className="bg-orange hover:bg-orange-600 text-black font-semibold"
        >
          {isLoading ? 'Chargement...' : "Continuer vers l'analyse"}
        </Button>
      </div>
    </div>
  );
}