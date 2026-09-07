'use client';

import { useState } from 'react';
import { FieldAnalysisResult } from '@/src/types/analysis';
import { fieldLabel, complianceColor, statusLabel } from '@/src/lib/kycFields';
import { ChevronDown, ChevronUp, AlertCircle } from 'lucide-react';
import { MiniDonut } from './MiniDonut';
import { AgePyramid } from './AgePyramid';

interface FieldDetailAccordionProps {
  field: string;
  data: FieldAnalysisResult;
}

// Petit histogramme CSS, sans dépendance externe. Affiche les N plus
// grandes barres d'une distribution (utile pour length_distribution à 30
// tranches ou age_distribution à 75 tranches — on ne montre pas tout).
function MiniHistogram({
  distribution,
  topN = 15,
  unit = '',
}: {
  distribution: Record<string, number>;
  topN?: number;
  unit?: string;
}) {
  const entries = Object.entries(distribution)
    .map(([k, v]) => [k, Number(v)] as [string, number])
    .sort((a, b) => Number(a[0]) - Number(b[0]))
    .slice(0, topN);
  const max = Math.max(...entries.map(([, v]) => v), 1);

  return (
    <div className="space-y-1">
      {entries.map(([key, value]) => (
        <div key={key} className="grid grid-cols-[50px_1fr_60px] items-center gap-2">
          <span className="text-xs text-gray-500 text-right">{key}{unit}</span>
          <div className="h-3 bg-white border rounded overflow-hidden">
            <div
              className="h-full bg-blue-400"
              style={{ width: `${(value / max) * 100}%` }}
            />
          </div>
          <span className="text-xs text-gray-600">{value.toLocaleString('fr-FR')}</span>
        </div>
      ))}
      {Object.keys(distribution).length > topN && (
        <p className="text-xs text-gray-400 italic">
          + {Object.keys(distribution).length - topN} autres tranches
        </p>
      )}
    </div>
  );
}

function ControlsList({ controls }: { controls: Record<string, number> }) {
  return (
    <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-sm">
      {Object.entries(controls).map(([label, value]) => (
        <div key={label} className="flex justify-between border-b border-gray-100 py-1">
          <span className="text-gray-600">{label}</span>
          <span className="font-medium text-gray-900">{value.toLocaleString('fr-FR')}</span>
        </div>
      ))}
    </div>
  );
}

function KeyValueRow({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex justify-between border-b border-gray-100 py-1.5 text-sm">
      <span className="text-gray-600">{label}</span>
      <span className="font-medium text-gray-900">
        {typeof value === 'number' ? value.toLocaleString('fr-FR') : value}
      </span>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <p className="text-xs uppercase tracking-wide text-gray-400 mb-2">{title}</p>
      {children}
    </div>
  );
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
        <div className="flex items-center gap-2">
          {isAnalyzed && data.complianceRate != null && colors && (
            <>
              <MiniDonut rate={data.complianceRate} />
              <span className={`text-sm font-semibold ${colors.text}`}>{data.complianceRate}%</span>
            </>
          )}
          {isOpen ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
        </div>
      </button>

      {isOpen && (
        <div className="px-4 py-4 border-t bg-gray-50 space-y-5">
          {!isAnalyzed ? (
            <div className="flex items-start gap-2 text-sm text-gray-600">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <p>{data.warning || data.reason || data.error || 'Aucune information disponible'}</p>
            </div>
          ) : (
            <>
              {/* Métriques générales — communes à tous les champs */}
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

              {/* ===== MSISDN ===== */}
              {field === 'msisdn' && (
                <>
                  {data.formatDetails && (
                    <Section title="Format">
                      <KeyValueRow label="Longueur la plus fréquente" value={`${data.formatDetails.expectedLength ?? '—'} chiffres`} />
                      <KeyValueRow label="Valeurs numériques" value={`${data.formatDetails.numericPercentage ?? '—'}%`} />
                      <KeyValueRow label="Longueur correcte" value={`${data.formatDetails.matchingLengthPercentage ?? '—'}%`} />
                    </Section>
                  )}
                  {data.lengthDistribution && (
                    <Section title="Distribution des longueurs">
                      <MiniHistogram distribution={data.lengthDistribution} unit=" car." />
                    </Section>
                  )}
                </>
              )}

              {/* ===== FIRST NAME / LAST NAME ===== */}
              {(field === 'first_name' || field === 'last_name') && data.controls && (
                <Section title="Contrôles">
                  <ControlsList controls={data.controls} />
                </Section>
              )}

              {/* ===== ID TYPE ===== */}
              {field === 'id_type' && data.idTypeDistribution && (
                <Section title="Répartition des types d'ID">
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(data.idTypeDistribution).map(([type, count]) => (
                      <span key={type} className="px-2 py-1 bg-white border rounded text-xs text-gray-700">
                        {type}: {count.toLocaleString('fr-FR')}
                      </span>
                    ))}
                  </div>
                </Section>
              )}

              {/* ===== ID NUMBER ===== */}
              {field === 'id_number' && (
                <>
                  {data.validationMode === 'any_type' && (
                    <div className="text-xs text-gray-500 bg-blue-50 rounded p-2">
                      Type d'ID non détecté — validation effectuée contre tous les formats connus du pays.
                    </div>
                  )}
                  {data.matchedTypeDistribution && (
                    <Section title="Répartition des formats détectés parmi les valides">
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(data.matchedTypeDistribution).map(([type, count]) => (
                          <span key={type} className="px-2 py-1 bg-white border rounded text-xs text-gray-700">
                            {type}: {count.toLocaleString('fr-FR')}
                          </span>
                        ))}
                      </div>
                    </Section>
                  )}
                  {data.duplicates && (
                    <Section title="Doublons">
                      <KeyValueRow label="IDs uniques valides" value={data.duplicates.uniqueValidIds} />
                      <KeyValueRow label="IDs dupliqués" value={data.duplicates.duplicateIdsCount} />
                      <KeyValueRow label="Enregistrements dupliqués" value={data.duplicates.duplicateRecordsCount} />
                      {Object.keys(data.duplicates.topDuplicates || {}).length > 0 && (
                        <div className="mt-2">
                          <p className="text-xs text-gray-500 mb-1">Top doublons</p>
                          <div className="space-y-1">
                            {Object.entries(data.duplicates.topDuplicates).map(([id, count]) => (
                              <div key={id} className="flex justify-between text-xs">
                                <span className="font-mono text-gray-700">{id}</span>
                                <span className="text-gray-500">{count} occurrences</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </Section>
                  )}
                  {data.lengthDistribution && (
                    <Section title="Distribution des longueurs">
                      <MiniHistogram distribution={data.lengthDistribution} unit=" car." />
                    </Section>
                  )}
                  {data.suspiciousPatterns && (
                    <Section title="Patterns suspects">
                      <KeyValueRow label="Séquences (123456...)" value={data.suspiciousPatterns.sequential} />
                      <KeyValueRow label="Chiffres répétés" value={data.suspiciousPatterns.repeated} />
                      <KeyValueRow label="Tout à zéro" value={data.suspiciousPatterns.allZeros} />
                      <KeyValueRow label="Tout à neuf" value={data.suspiciousPatterns.allNines} />
                    </Section>
                  )}
                </>
              )}

              {/* ===== DOB ===== */}
              {field === 'dob' && (
                <>
                  <Section title="Règles de validation">
                    <KeyValueRow label="Âge minimum" value="18 ans" />
                    <KeyValueRow label="Âge maximum" value="95 ans" />
                  </Section>
                  {data.detectedFormats && Object.keys(data.detectedFormats).length > 0 && (
                    <Section title="Formats détectés">
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(data.detectedFormats).map(([fmt, count]) => (
                          <span key={fmt} className="px-2 py-1 bg-white border rounded text-xs text-gray-700">
                            {fmt}: {count.toLocaleString('fr-FR')}
                          </span>
                        ))}
                      </div>
                    </Section>
                  )}
                  {data.validationErrors && Object.keys(data.validationErrors).length > 0 && (
                    <Section title="Erreurs de validation (top 5)">
                      <div className="space-y-1">
                        {Object.entries(data.validationErrors).slice(0, 5).map(([err, count]) => (
                          <div key={err} className="flex justify-between text-xs">
                            <span className="text-gray-700">{err}</span>
                            <span className="text-gray-500">{count.toLocaleString('fr-FR')}</span>
                          </div>
                        ))}
                      </div>
                    </Section>
                  )}
                  {data.ageDistribution && (
                    <Section title="Distribution des âges">
                      <AgePyramid distribution={data.ageDistribution} />
                    </Section>
                  )}
                  {data.ageAnomalies && (
                    <Section title="Anomalies d'âge">
                      <KeyValueRow label="Sous l'âge minimum" value={data.ageAnomalies.underMinimumAge} />
                      <KeyValueRow label="Au-dessus de l'âge maximum" value={data.ageAnomalies.overMaximumAge} />
                      <KeyValueRow label="Dates futures" value={data.ageAnomalies.futureDates} />
                    </Section>
                  )}
                </>
              )}

              {/* ===== CITY ===== */}
              {field === 'city' && (
                <>
                  {data.controls && (
                    <Section title="Contrôles">
                      <ControlsList controls={data.controls} />
                    </Section>
                  )}
                  {data.topCities && (
                    <Section title={`Top 10 villes${data.uniqueCitiesCount != null ? ` (${data.uniqueCitiesCount} distinctes)` : ''}`}>
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(data.topCities).slice(0, 10).map(([city, count]) => (
                          <span key={city} className="px-2 py-1 bg-white border rounded text-xs text-gray-700">
                            {city}: {count.toLocaleString('fr-FR')}
                          </span>
                        ))}
                      </div>
                    </Section>
                  )}
                </>
              )}

              {/* ===== ADDRESS ===== */}
              {field === 'address' && data.controls && (
                <Section title="Contrôles">
                  <ControlsList controls={data.controls} />
                </Section>
              )}

              {/* Anomalies détectées — commun à tous les champs */}
              {data.anomalies && data.anomalies.length > 0 && (
                <Section title="Anomalies">
                  <ul className="space-y-1">
                    {data.anomalies.map((a, idx) => (
                      <li key={idx} className="text-sm text-gray-700">
                        • {a.type.replace(/_/g, ' ')} — {a.count.toLocaleString('fr-FR')} ({a.percentage}%)
                      </li>
                    ))}
                  </ul>
                </Section>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}