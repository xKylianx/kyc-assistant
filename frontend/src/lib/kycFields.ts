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