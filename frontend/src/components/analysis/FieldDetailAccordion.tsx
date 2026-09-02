'use client';

import { useState } from 'react';
import { FieldAnalysisResult } from '@/src/types/analysis';
import { fieldLabel, complianceColor, statusLabel } from '@/src/lib/kycFields';
import { ChevronDown, ChevronUp, AlertCircle } from 'lucide-react';

interface FieldDetailAccordionProps {
  field: string;
  data: FieldAnalysisResult;
}

export function FieldDetailAccordion({ field, data }: FieldDetailAccordionProps) {
  const [isOpen, setIsOpen] = useState(false);
  const isAnalyzed = data.status === 'completed';
  const colors = isAnalyzed && data.complianceRate != null ? complianceColor(data.complianceRate) : null;

  return (
    <div className="border rounded-lg overflow-hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-4 py-3 bg-white hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className="font-medium text-gray-900">{fieldLabel(field)}</span>
          {!isAnalyzed && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">
              {statusLabel(data.status)}
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          {isAnalyzed && data.complianceRate != null && colors && (
            <span className={`text-sm font-semibold ${colors.text}`}>
              {data.complianceRate}%
            </span>
          )}
          {isOpen ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
        </div>
      </button>

      {isOpen && (
        <div className="px-4 py-4 border-t bg-gray-50 space-y-4">
          {!isAnalyzed ? (
            <div className="flex items-start gap-2 text-sm text-gray-600">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <p>{data.warning || data.reason || data.error || 'Aucune information disponible'}</p>
            </div>
          ) : (
            <>
              {/* Métriques générales */}
              <div className="grid grid-cols-3 gap-3 text-sm">
                <div>
                  <p className="text-gray-500">Enregistrements</p>
                  <p className="font-medium text-gray-900">{data.rowCount?.toLocaleString('fr-FR') ?? '—'}</p>
                </div>
                <div>
                  <p className="text-gray-500">Valeurs manquantes</p>
                  <p className="font-medium text-gray-900">{data.nullCount?.toLocaleString('fr-FR') ?? '—'}</p>
                </div>
                <div>
                  <p className="text-gray-500">Valeurs valides</p>
                  <p className="font-medium text-gray-900">{data.validCount?.toLocaleString('fr-FR') ?? '—'}</p>
                </div>
              </div>

              {/* Format attendu (MSISDN, id_number) */}
              {data.formatDetails && (
                <div className="text-sm">
                  <p className="text-gray-500 mb-1">Format</p>
                  <div className="flex flex-wrap gap-x-6 gap-y-1 text-gray-700">
                    {data.formatDetails.expectedLength != null && (
                      <span>Longueur attendue : {data.formatDetails.expectedLength}</span>
                    )}
                    {data.formatDetails.expectedFormat && (
                      <span>Format : {data.formatDetails.expectedFormat}</span>
                    )}
                    {data.formatDetails.numericPercentage != null && (
                      <span>Numérique : {data.formatDetails.numericPercentage}%</span>
                    )}
                  </div>
                </div>
              )}

              {/* Distribution type d'ID */}
              {data.idTypeDistribution && (
                <div className="text-sm">
                  <p className="text-gray-500 mb-1">
                    Type dominant : <span className="text-gray-900 font-medium">{data.dominantIdType || 'N/A'}</span>
                    {data.dominantPercentage != null && ` (${data.dominantPercentage}%)`}
                  </p>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {Object.entries(data.idTypeDistribution).map(([type, count]) => (
                      <span key={type} className="px-2 py-1 bg-white border rounded text-xs text-gray-700">
                        {type}: {count.toLocaleString('fr-FR')}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Mode de validation ID number */}
              {data.validationMode === 'any_type' && (
                <div className="text-xs text-gray-500 bg-blue-50 rounded p-2">
                  Type d'ID non détecté — validation effectuée contre tous les formats connus du pays.
                </div>
              )}

              {/* Doublons */}
              {data.duplicates && (
                <div className="text-sm">
                  <p className="text-gray-500 mb-1">Doublons</p>
                  <div className="flex flex-wrap gap-x-6 gap-y-1 text-gray-700">
                    <span>IDs uniques : {data.duplicates.uniqueValidIds.toLocaleString('fr-FR')}</span>
                    <span>Enregistrements dupliqués : {data.duplicates.duplicateRecordsCount.toLocaleString('fr-FR')} ({data.duplicates.duplicatePercentage}%)</span>
                  </div>
                </div>
              )}

              {/* Formats de date détectés */}
              {data.detectedFormats && Object.keys(data.detectedFormats).length > 0 && (
                <div className="text-sm">
                  <p className="text-gray-500 mb-1">Formats détectés</p>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(data.detectedFormats).map(([fmt, count]) => (
                      <span key={fmt} className="px-2 py-1 bg-white border rounded text-xs text-gray-700">
                        {fmt}: {count.toLocaleString('fr-FR')}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Statistiques d'âge */}
              {data.ageStatistics && data.ageStatistics.avgAge != null && (
                <div className="text-sm">
                  <p className="text-gray-500 mb-1">Âges</p>
                  <div className="flex flex-wrap gap-x-6 gap-y-1 text-gray-700">
                    <span>Min : {data.ageStatistics.minAge} ans</span>
                    <span>Max : {data.ageStatistics.maxAge} ans</span>
                    <span>Moyenne : {data.ageStatistics.avgAge} ans</span>
                  </div>
                </div>
              )}

              {/* Top villes */}
              {data.topCities && (
                <div className="text-sm">
                  <p className="text-gray-500 mb-1">
                    Villes les plus fréquentes {data.uniqueCitiesCount != null && `(${data.uniqueCitiesCount} distinctes)`}
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(data.topCities).slice(0, 6).map(([city, count]) => (
                      <span key={city} className="px-2 py-1 bg-white border rounded text-xs text-gray-700">
                        {city}: {count.toLocaleString('fr-FR')}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Statistiques de longueur (adresse) */}
              {data.lengthStatistics && (
                <div className="text-sm">
                  <p className="text-gray-500 mb-1">Longueur des valeurs</p>
                  <div className="flex flex-wrap gap-x-6 gap-y-1 text-gray-700">
                    <span>Min : {data.lengthStatistics.minLength}</span>
                    <span>Max : {data.lengthStatistics.maxLength}</span>
                    <span>Moyenne : {data.lengthStatistics.avgLength}</span>
                  </div>
                </div>
              )}

              {/* Anomalies du champ */}
              {data.anomalies && data.anomalies.length > 0 && (
                <div className="text-sm">
                  <p className="text-gray-500 mb-1">Anomalies</p>
                  <ul className="space-y-1">
                    {data.anomalies.map((a, idx) => (
                      <li key={idx} className="text-gray-700">
                        • {a.type.replace(/_/g, ' ')} — {a.count.toLocaleString('fr-FR')} ({a.percentage}%)
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}