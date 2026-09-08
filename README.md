# KYC Assistant

Outil interne Orange d'analyse automatisée de bases de données KYC (Know Your
Customer). Détecte les anomalies, contrôle la conformité et génère des
rapports détaillés à partir de fichiers CSV ou Excel, via un système
multi-agents piloté par IA.

## Sommaire

- [Fonctionnalités](#fonctionnalités)
- [Architecture](#architecture)
- [Stack technique](#stack-technique)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Variables d'environnement](#variables-denvironnement)
- [Lancement](#lancement)
- [Utilisation](#utilisation)
- [Structure du projet](#structure-du-projet)
- [Limitations connues](#limitations-connues)
- [Charte graphique](#charte-graphique)

## Fonctionnalités

- Upload de fichiers CSV/Excel jusqu'à plusieurs dizaines de Go, en streaming
  (jamais chargés entièrement en mémoire)
- Détection automatique du schéma Orange Money, ou identification assistée
  par IA des colonnes KYC pour tout autre schéma, avec justification par champ
- Détection automatique du pays d'origine des données, avec validation
  manuelle par l'utilisateur
- Détection des lignes actives (statut de compte) avant analyse
- Contrôles KYC détaillés par champ : MSISDN, nom, prénom, type et numéro
  d'ID, date de naissance, adresse, ville
- Validation des numéros d'identité par pays, avec repli automatique sur une
  validation multi-formats quand le type d'ID est absent ou peu fiable
- Rapport détaillé interactif (jauge de conformité, heatmap par champ,
  historique par pays) et export PDF
- Tableau de bord listant l'historique des analyses, filtrable par pays

## Architecture

Le cœur du traitement repose sur trois agents orchestrés séquentiellement :

```
Upload fichier
     │
     ▼
┌─────────────────┐   Profiling du fichier (délimiteur, colonnes,
│   Prep Agent     │   nombre de lignes, échantillon de données)
└─────────────────┘
     │
     ▼
Détection de schéma (Orange Money ou mapping assisté par IA)
     │
     ▼
Détection et validation du pays
     │
     ▼
Détection des lignes actives
     │
     ▼
┌─────────────────┐   Contrôles KYC par champ (conformité, anomalies,
│  Analysis Agent  │   doublons, formats, âges) — lecture en streaming
└─────────────────┘   via DuckDB, jamais chargé en mémoire complète
     │
     ▼
┌─────────────────┐   Construction du rapport détaillé et export PDF
│   Plot Agent     │
└─────────────────┘
```

Chaque étape est exposée via une route API dédiée, orchestrée côté backend
par LangGraph. Le frontend consomme ces routes séquentiellement et affiche à
chaque étape un écran permettant à l'utilisateur de valider ou corriger la
donnée avant de poursuivre (schéma, pays).

## Stack technique

**Backend**
- FastAPI (routes API, validation Pydantic)
- LangGraph (orchestration des agents)
- DuckDB (lecture et analyse des fichiers CSV en streaming, sans les charger
  intégralement en mémoire)
- SQLAlchemy + SQLite (persistance des métadonnées, résultats d'analyse,
  historique)
- ReportLab (export PDF des rapports)
- LangChain / modèle LLM (détection de schéma, de pays, suggestion de
  colonnes, justifications)

**Frontend**
- Next.js (App Router)
- TypeScript
- Tailwind CSS v4
- Composants UI basés sur base-ui / class-variance-authority

## Prérequis

- Python 3.11 ou 3.12 (éviter les versions plus récentes non testées avec
  la stack SQLAlchemy/DuckDB actuelle)
- Node.js 18+ et npm
- Un espace disque suffisant pour stocker les fichiers uploadés
  (`backend/data/uploads/`)

## Installation

### Backend

```bash
cd backend
python -m venv venv
# Windows (PowerShell)
.\venv\Scripts\Activate.ps1
# macOS/Linux
source venv/bin/activate

pip install -r ../requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

## Variables d'environnement

### Backend — `backend/.env`

| Variable          | Description                                         | Exemple                          |
|--------------------|------------------------------------------------------|-----------------------------------|
| `DATABASE_URL`     | URL de connexion à la base SQLite                     | `sqlite:///./app.db`             |
| `OPENAI_API_KEY`   | Clé API du proxy LLM utilisé                          | `sk-...`                          |
| `BASE_URL`         | URL de base du proxy LLM (compatible OpenAI)          | `https://...`                     |
| `LLM_PROXY_MODEL`  | Nom du modèle utilisé par les agents                  | `openai/gpt-5-chat`              |
| `MAX_FILE_SIZE_MB` | Taille maximale de fichier acceptée (en Mo)           | `20000` (20 Go)                   |

### Frontend — `frontend/.env.local`

| Variable                | Description                                  | Exemple                     |
|--------------------------|-----------------------------------------------|-------------------------------|
| `NEXT_PUBLIC_API_URL`   | URL du backend FastAPI                        | `http://localhost:8000`      |
| `NEXT_PUBLIC_USE_MOCK`  | Active les données mockées (sans backend)     | `false`                       |

## Lancement

### Backend

```bash
cd backend
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

L'API est alors disponible sur `http://localhost:8000`, avec documentation
interactive Swagger sur `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm run dev
```

L'application est disponible sur `http://localhost:3000`.

## Utilisation

1. **Accueil** : point d'entrée vers l'analyse ou le tableau de bord.
2. **Upload** : glisser-déposer ou sélectionner un fichier CSV/Excel.
3. **Préparation** : profiling automatique du fichier (délimiteur, colonnes,
   échantillon) — aucune action requise.
4. **Schéma** :
   - si le fichier correspond au schéma Orange Money, cette étape est
     automatiquement validée et signalée par un bandeau ;
   - sinon, les colonnes KYC sont pré-suggérées par IA avec justification,
     à valider ou corriger manuellement.
5. **Pays** : confirmation du pays détecté (ou correction manuelle) avant
   d'appliquer les règles de validation spécifiques (âge, format des
   identifiants).
6. **Analyse** : résultats agrégés par champ KYC, anomalies détectées,
   niveau de risque global.
7. **Rapport** : synthèse visuelle complète (jauge de conformité, heatmap,
   détail par champ en accordéon, tendance par pays) et export PDF.

Le **tableau de bord** (`/dashboard`) liste l'historique des analyses,
filtrable par pays et triable par date, pour suivre l'évolution du niveau de
KYC dans le temps. Chaque ligne renvoie vers le rapport détaillé de
l'analyse correspondante.

## Structure du projet

```
kyc-assistant/
├── backend/
│   ├── src/
│   │   ├── agents/          # Agents LangGraph (prep, analysis)
│   │   ├── api/
│   │   │   ├── routes/      # Endpoints FastAPI (orchestrator, files)
│   │   │   └── schemas/     # Schémas Pydantic
│   │   ├── config/          # Règles de validation par pays/type d'ID
│   │   ├── db/               # Modèles SQLAlchemy, session, init
│   │   ├── nodes/            # Nodes d'analyse par champ KYC
│   │   ├── repositories/     # Accès aux données (upsert/get par table)
│   │   └── services/         # Services transverses (storage, rapport,
│   │                          suggestion de colonnes)
│   └── data/uploads/         # Fichiers uploadés (stockage local)
├── frontend/
│   ├── src/
│   │   ├── app/               # Pages Next.js (accueil, upload, dashboard)
│   │   ├── components/
│   │   │   ├── analysis/      # Visualisations (jauge, heatmap, radar...)
│   │   │   ├── common/        # Layout, Header, Footer
│   │   │   ├── upload/        # Écrans du flux d'analyse
│   │   │   └── ui/             # Composants UI de base
│   │   ├── hooks/              # useKYCAnalysis (orchestration du flux)
│   │   ├── lib/                 # Utilitaires (libellés, couleurs)
│   │   ├── services/            # Client API (ApiService)
│   │   └── types/                # Types TypeScript partagés
│   └── public/                   # Assets statiques (logo Orange, etc.)
└── requirements.txt
```

## Limitations connues

- **Analyse séquentielle** : chaque champ KYC déclenche un scan complet du
  fichier via DuckDB (8 scans pour 8 champs). Sur des fichiers de plusieurs
  Go, l'analyse peut prendre plusieurs minutes. Aucune barre de progression
  précise n'est disponible côté frontend pendant cette étape (temps écoulé
  affiché à la place).
- **Requête HTTP synchrone bloquante** : `/orchestrator/analyze` ne renvoie
  sa réponse qu'à la fin du traitement complet — pas de suivi en temps réel
  par champ. Une évolution possible serait de faire de cette étape une tâche
  de fond avec polling de statut.
- **Estimation des enregistrements affectés** : en l'absence d'identifiant de
  ligne partagé entre les contrôles de chaque champ, le nombre
  d'enregistrements affectés total est une estimation (maximum des anomalies
  par champ), pas un compte exact de lignes distinctes.
- **Historique par pays** : la liste des pays proposée dans le filtre du
  tableau de bord est déduite de la page actuellement affichée, pas d'une
  liste exhaustive de tous les pays en base.
- **Format de fichier** : seul le CSV est actuellement supporté côté
  détection de schéma et analyse (l'upload accepte aussi Excel, mais le
  pipeline d'analyse est optimisé pour CSV).

## Charte graphique

L'interface suit la charte graphique Orange (couleurs officielles, header
et typographie). Les règles de design (palette, composants, tokens Tailwind)
sont documentées et réutilisables via la skill `charte-orange`.
