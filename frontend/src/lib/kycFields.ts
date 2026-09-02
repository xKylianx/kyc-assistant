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