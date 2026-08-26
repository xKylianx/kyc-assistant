'use client';

import { useState } from 'react';
import { Card, CardContent } from '@/src/components/ui/card';
import { Button } from '@/src/components/ui/button';
import { Alert, AlertDescription } from '@/src/components/ui/alert';
import { CountryDetection } from '@/src/types/analysis';
import { CheckCircle, Globe, X } from 'lucide-react';

interface CountryStepProps {
  countryDetection: CountryDetection;
  schemaAutoValidated: boolean;
  onDismissBanner: () => void;
  onConfirm: (country: string) => void;
  isLoading: boolean;
}

export function CountryStep({
  countryDetection,
  schemaAutoValidated,
  onDismissBanner,
  onConfirm,
  isLoading,
}: CountryStepProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [correctedCountry, setCorrectedCountry] = useState(countryDetection.detectedCountry);

  return (
    <div className="space-y-4">
      {schemaAutoValidated && (
        <Alert className="border-green-200 bg-green-50">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-start gap-2">
              <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
              <AlertDescription className="text-green-800">
                Schéma Orange Money détecté — colonnes KYC mappées automatiquement.
              </AlertDescription>
            </div>
            <button
              onClick={onDismissBanner}
              aria-label="Fermer"
              className="text-green-700 hover:text-green-900 flex-shrink-0"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </Alert>
      )}

      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-2 mb-1">
            <Globe className="w-5 h-5 text-orange-500" />
            <h3 className="font-semibold text-gray-900">Pays détecté</h3>
          </div>
          <p className="text-sm text-gray-600 mb-5">
            Confirmez le pays avant de lancer les contrôles KYC. Les règles de
            validation (âge, format ID) en dépendent.
          </p>

          {!isEditing ? (
            <>
              <div className="bg-gray-50 rounded-lg p-4 flex items-center justify-between mb-4">
                <div>
                  <p className="text-2xl font-semibold text-gray-900">
                    {countryDetection.detectedCountry}
                  </p>
                  <p className="text-sm text-gray-600 mt-1">
                    Confiance de détection : {Math.round(countryDetection.confidence * 100)}%
                  </p>
                </div>
                <div className="w-11 h-11 rounded-full bg-green-100 flex items-center justify-center">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                </div>
              </div>

              {countryDetection.reasoning && (
                <div className="border-t pt-3 mb-5">
                  <p className="text-sm text-gray-600 mb-1">Raisonnement du modèle</p>
                  <p className="text-sm text-gray-900">{countryDetection.reasoning}</p>
                </div>
              )}

              <div className="flex gap-3">
                <Button
                  className="flex-1 bg-orange-500 hover:bg-orange-600 text-white"
                  onClick={() => onConfirm(countryDetection.detectedCountry)}
                  disabled={isLoading}
                >
                  {isLoading ? 'Validation...' : `Confirmer ${countryDetection.detectedCountry}`}
                </Button>
                <Button variant="outline" className="flex-1" onClick={() => setIsEditing(true)}>
                  Modifier
                </Button>
              </div>
            </>
          ) : (
            <>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Corriger le pays
              </label>
              <input
                type="text"
                value={correctedCountry}
                onChange={(e) => setCorrectedCountry(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 mb-4"
                placeholder="Ex : Madagascar"
              />
              <div className="flex gap-3">
                <Button
                  className="flex-1 bg-orange-500 hover:bg-orange-600 text-white"
                  onClick={() => onConfirm(correctedCountry)}
                  disabled={isLoading || !correctedCountry.trim()}
                >
                  {isLoading ? 'Validation...' : 'Valider ce pays'}
                </Button>
                <Button variant="outline" className="flex-1" onClick={() => setIsEditing(false)}>
                  Annuler
                </Button>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}