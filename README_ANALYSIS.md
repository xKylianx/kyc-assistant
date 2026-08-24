# KYC Analysis Agent

## 📊 Vue d'ensemble

Agent d'analyse KYC utilisant LangGraph pour orchestrer l'analyse complète des données clients.

## 🎯 Fonctionnalités

- ✅ Analyse MSISDN (format, longueur, validité)
- ✅ Analyse Prénom (caractères, longueur)
- ✅ Analyse Nom (caractères, longueur)
- ✅ Analyse Type d'ID (validité par pays)
- ✅ Analyse Numéro d'ID (duplicatas, patterns)
- ✅ Analyse Date de Naissance (format, âge)
- ✅ Analyse Ville (caractères, validité)
- ✅ Analyse Adresse (longueur, caractères)

## 📈 Résultats

- **Overall Compliance Rate** : Taux de conformité global (0-100%)
- **Overall Risk Score** : Score de risque (0-1)
- **Overall Risk Level** : LOW, MEDIUM, HIGH, CRITICAL
- **Anomalies** : Détection automatique des problèmes
- **Executive Summary** : Recommandations

## ⚡ Performance

- 10,000 enregistrements : 0.67s
- **15,026 records/sec**

## 🧪 Tests

```bash
pytest tests/test_analysis_agent.py -v