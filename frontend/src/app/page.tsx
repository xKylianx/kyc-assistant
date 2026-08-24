
/**
 * Page d'accueil
 */

import Link from "next/link";
import { Layout } from "@/src/components/common";
import { Button } from "@/src/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/src/components/ui/card";
import { Upload, BarChart3, Shield, Zap } from "lucide-react";

export default function Home() {
  return (
    <Layout>
      {/* Hero Section */}
      <section className="py-20 text-center">
        <h1 className="text-5xl font-bold text-gray-900 mb-4">
          Analyse de documents <span className="text-orange-primary">KYC</span>
        </h1>
        <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
          Détectez les anomalies et les risques dans vos documents d'identité avec notre solution IA avancée.
        </p>
        <div className="flex gap-4 justify-center">
          <Link href="/upload">
            <Button className="bg-orange-primary hover:bg-orange-600 text-white px-8 py-6 text-lg flex items-center gap-2">
              <Upload className="w-5 h-5" />
              Commencer
            </Button>
          </Link>
          <Link href="/dashboard">
            <Button variant="outline" className="border-orange-primary text-orange-primary hover:bg-orange-primary hover:text-white px-8 py-6 text-lg flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              Dashboard
            </Button>
          </Link>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20">
        <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
          Nos fonctionnalités
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Feature 1 */}
          <Card className="border-t-4 border-t-orange-primary">
            <CardHeader>
              <div className="w-12 h-12 bg-orange-primary rounded-lg flex items-center justify-center mb-4">
                <Upload className="w-6 h-6 text-white" />
              </div>
              <CardTitle>Upload facile</CardTitle>
              <CardDescription>Téléchargez vos documents en quelques clics</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600">
                Supportez les formats courants : PDF, JPG, PNG. Analyse instantanée avec feedback en temps réel.
              </p>
            </CardContent>
          </Card>

          {/* Feature 2 */}
          <Card className="border-t-4 border-t-orange-primary">
            <CardHeader>
              <div className="w-12 h-12 bg-orange-primary rounded-lg flex items-center justify-center mb-4">
                <Zap className="w-6 h-6 text-white" />
              </div>
              <CardTitle>Analyse IA</CardTitle>
              <CardDescription>Détection automatique des anomalies</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600">
                Utilisez l'IA pour détecter les fraudes, les documents falsifiés et les anomalies.
              </p>
            </CardContent>
          </Card>

          {/* Feature 3 */}
          <Card className="border-t-4 border-t-orange-primary">
            <CardHeader>
              <div className="w-12 h-12 bg-orange-primary rounded-lg flex items-center justify-center mb-4">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <CardTitle>Sécurité</CardTitle>
              <CardDescription>Vos données sont protégées</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600">
                Chiffrement end-to-end et conformité RGPD pour protéger vos informations sensibles.
              </p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-orange-primary rounded-lg text-white text-center">
        <h2 className="text-3xl font-bold mb-4">Prêt à commencer ?</h2>
        <p className="text-lg mb-8 opacity-90">
          Analysez vos premiers documents dès maintenant
        </p>
        <Link href="/upload">
          <Button className="bg-white text-orange-primary hover:bg-gray-100 px-8 py-6 text-lg font-semibold">
            Télécharger un document
          </Button>
        </Link>
      </section>
    </Layout>
  );
}