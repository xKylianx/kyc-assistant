import { Severity } from '@/src/types/analysis';

// Le backend renvoie des sévérités "low"/"medium"/"high" (voir
// data_analysis_nodes.py). Le frontend affiche "info"/"warning"/"error".
// Ce mapping doit rester identique à SEVERITY_MAP dans
// backend/src/services/report_service.py pour que /analyze et /report
// affichent la même chose.
const BACKEND_SEVERITY_MAP: Record<string, Severity> = {
  low: 'info',
  medium: 'warning',
  high: 'error',
};

export function normalizeSeverity(raw: string): Severity {
  return BACKEND_SEVERITY_MAP[raw] ?? 'info';
}

export const KYC_FIELD_LABELS: Record<string, string> = {
  msisdn: 'MSISDN',
  first_name: 'Prénom',
  last_name: 'Nom',
  id_type: "Type d'ID",
  id_number: "Numéro d'ID",
  dob: 'Date de naissance',
  address: 'Adresse',
  city: 'Ville',
};

export function fieldLabel(field: string): string {
  return KYC_FIELD_LABELS[field] || field;
}

export function complianceColor(rate: number): { bar: string; text: string } {
  if (rate >= 95) return { bar: 'bg-green-500', text: 'text-green-700' };
  if (rate >= 85) return { bar: 'bg-yellow-500', text: 'text-yellow-700' };
  return { bar: 'bg-red-500', text: 'text-red-700' };
}

export function riskBadgeClasses(level: string): string {
  switch (level) {
    case 'LOW':
      return 'bg-green-100 text-green-800';
    case 'MEDIUM':
      return 'bg-yellow-100 text-yellow-800';
    case 'HIGH':
      return 'bg-orange-100 text-orange-800';
    case 'CRITICAL':
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}

export const KYC_FIELD_ICONS: Record<string, string> = {
  msisdn: '📱',
  first_name: '👤',
  last_name: '👤',
  id_type: '🆔',
  id_number: '🆔',
  dob: '📅',
  address: '📍',
  city: '🏙️',
};

export const KYC_FIELD_ORDER = [
  'msisdn',
  'first_name',
  'last_name',
  'id_type',
  'id_number',
  'dob',
  'address',
  'city',
];

export function statusLabel(status: string): string {
  switch (status) {
    case 'completed':
      return 'Analysé';
    case 'warning':
      return 'Non concluant';
    case 'skipped':
      return 'Ignoré';
    case 'error':
      return 'Erreur';
    default:
      return status;
  }
}

export function dobValidationRulesLabel(data: import('../types/analysis').FieldAnalysisResult): string {
  const under = data.ageAnomalies?.underMinimumAge ?? 0;
  const over = data.ageAnomalies?.overMaximumAge ?? 0;
  return `Âge min : 18 ans · Âge max : 95 ans`;
}

// Interpolation hex linéaire entre deux couleurs
function interpolateHex(colorA: string, colorB: string, t: number): string {
  const a = colorA.match(/\w\w/g)!.map((h) => parseInt(h, 16));
  const b = colorB.match(/\w\w/g)!.map((h) => parseInt(h, 16));
  const rgb = a.map((v, i) => Math.round(v + (b[i] - v) * t));
  return `#${rgb.map((v) => v.toString(16).padStart(2, '0')).join('')}`;
}

// Échelle continue rouge → jaune → vert, calquée sur le principe du POC
// Streamlit (colormap continu par valeur plutôt que seuils fixes).
export function complianceScaleColor(rate: number): string {
  const r = Math.max(0, Math.min(100, rate));
  if (r <= 50) {
    return interpolateHex('#E24B4A', '#FFDC00', r / 50);
  }
  return interpolateHex('#FFDC00', '#50BE87', (r - 50) / 50);
}

export function qualityLabel(quality: string): { label: string; emoji: string } {
  switch (quality) {
    case 'EXCELLENT':
      return { label: 'Excellent', emoji: '↑' };
    case 'GOOD':
      return { label: 'Good', emoji: '↑' };
    case 'FAIR':
      return { label: 'Fair', emoji: '→' };
    case 'POOR':
      return { label: 'Poor', emoji: '↓' };
    default:
      return { label: quality, emoji: '' };
  }
}

// Couleur de texte lisible sur un fond coloré par l'échelle continue
// (mêmes teintes que les cartes de la maquette validée)
export function heatmapTextColor(rate: number): string {
  if (rate < 40) return '#4A1B0C';
  if (rate < 75) return '#412402';
  return '#173404';
}