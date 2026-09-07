/**
 * Page d'accueil
 */

import Link from "next/link";
import { Layout } from "@/src/components/common";
import { Button } from "@/src/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/src/components/ui/card";
import { Upload, BarChart3, Shield, Zap, Sparkles } from "lucide-react";

export default function Home() {
  return (
    <Layout>
            {/* Hero Section — fond noir, dans l'esprit Dinootoo */}
      <section className="-mx-6 -mt-8 mb-16 bg-black text-white px-6 py-24">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center gap-3 mb-4">
            <h1 className="text-5xl font-bold tracking-tight">
              Bienvenue sur KYC Assistant
            </h1>
            <Sparkles className="w-8 h-8 text-orange" />
          </div>
          <p className="text-xl text-white/70 mb-10 max-w-2xl leading-relaxed">
            Analyser vos bases de données KYC en toute confiance : détection
            des anomalies, contrôle de conformité et rapports détaillés,
            générés automatiquement par IA.
          </p>
          <div className="flex gap-4">
            <Link href="/upload">
              <Button className="bg-orange hover:bg-orange-600 text-black font-semibold px-6 py-6 text-base rounded-md flex items-center gap-2 w-fit">
                <Upload className="w-5 h-5" />
                Accéder à l'analyse KYC
              </Button>
            </Link>
            <Link href="/dashboard">
              <Button
                variant="outline"
                className="border-white/30 text-white hover:bg-white/10 hover:text-white px-6 py-6 text-base rounded-md flex items-center gap-2 w-fit"
              >
                <BarChart3 className="w-5 h-5" />
                Dashboard
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-8 mb-8">
        <h2 className="text-3xl font-bold text-black mb-12">
          Nos fonctionnalités
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <Card className="border-t-4 border-t-orange">
            <CardHeader>
              <div className="w-12 h-12 bg-orange rounded-lg flex items-center justify-center mb-4">
                <Upload className="w-6 h-6 text-black" />
              </div>
              <CardTitle>Upload facile</CardTitle>
              <CardDescription>Téléchargez vos bases de données en quelques clics</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600">
                Formats CSV et Excel, fichiers volumineux jusqu'à plusieurs
                giga-octets. Détection automatique du schéma Orange Money.
              </p>
            </CardContent>
          </Card>

          <Card className="border-t-4 border-t-orange">
            <CardHeader>
              <div className="w-12 h-12 bg-orange rounded-lg flex items-center justify-center mb-4">
                <Zap className="w-6 h-6 text-black" />
              </div>
              <CardTitle>Analyse IA multi-agents</CardTitle>
              <CardDescription>Contrôles KYC automatisés champ par champ</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600">
                Détection du pays, validation des identités, dates de
                naissance, doublons et formats, avec des règles adaptées à
                chaque marché.
              </p>
            </CardContent>
          </Card>

          <Card className="border-t-4 border-t-orange">
            <CardHeader>
              <div className="w-12 h-12 bg-orange rounded-lg flex items-center justify-center mb-4">
                <Shield className="w-6 h-6 text-black" />
              </div>
              <CardTitle>Rapports détaillés</CardTitle>
              <CardDescription>Suivez la conformité dans le temps</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600">
                Score de conformité, anomalies critiques et historique par
                pays pour piloter l'amélioration continue de vos données.
              </p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 px-8 bg-black rounded-lg text-white text-center mb-8">
        <h2 className="text-3xl font-bold mb-4">Prêt à commencer ?</h2>
        <p className="text-lg mb-8 text-white/70">
          Analysez votre première base de données dès maintenant
        </p>
        <Link href="/upload">
          <Button className="bg-orange hover:bg-orange-600 text-black font-semibold px-8 py-6 text-lg rounded-md">
            Analyser un fichier
          </Button>
        </Link>
      </section>
    </Layout>
  );
}