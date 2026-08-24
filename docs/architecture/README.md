# Architecture KYC Assistant

Diagramme du flux complet de traitement :

![Architecture KYC Assistant](./kyc-assistant-flow.svg)

Le pipeline couvre l'upload streaming, le profiling DuckDB, la lecture par chunks, l'analyse multi-agent des champs KYC et la génération/persistance du rapport.
