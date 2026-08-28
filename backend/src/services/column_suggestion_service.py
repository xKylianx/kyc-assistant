from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

import duckdb
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("LLM_PROXY_MODEL"),
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("BASE_URL"),
)

REQUIRED_KYC_FIELDS = [
    ("nom_column", "Nom (last name)"),
    ("prenom_column", "Prénom (first name)"),
    ("msisdn_column", "MSISDN (phone number)"),
    ("id_type_column", "Type d'ID"),
    ("id_number_column", "Numéro d'ID"),
    ("dob_column", "Date de naissance"),
    ("address_column", "Adresse"),
    ("city_column", "Ville"),
    ("status_column", "Statut du compte"),
]


def suggest_column_mapping(
    file_path: str,
    delimiter: str,
    available_columns: List[str],
) -> Dict[str, Optional[str]]:
    """
    Propose un mapping colonne CSV -> champ KYC via LLM, à partir d'un
    échantillon du fichier. Retourne un dict {champ_kyc: colonne_csv|None}.
    En cas d'échec LLM, retourne un dict entièrement vide (fallback : mapping manuel).
    """
    con = duckdb.connect()
    try:
        query = f"""
            SELECT * FROM read_csv_auto('{file_path}', delim='{delimiter}', sample_size=20000)
            LIMIT 10
        """
        sample_df = con.execute(query).fetchdf().astype(str)
        sample_rows = sample_df.to_dict(orient="records")
    except Exception:
        sample_rows = []
    finally:
        con.close()

    fields_description = "\n".join(f"- {key}: {label}" for key, label in REQUIRED_KYC_FIELDS)

    prompt = f"""Tu es un analyste de données KYC. Associe chaque champ requis à la colonne CSV la plus pertinente.

Champs KYC requis :
{fields_description}

Colonnes disponibles dans le fichier :
{json.dumps(available_columns, indent=2)}

Échantillon de données (10 premières lignes) :
{json.dumps(sample_rows, indent=2)}

Réponds UNIQUEMENT en JSON valide, sans texte autour, au format :
{{"nom_column": "nom_exact_colonne_ou_null", "prenom_column": "...", "msisdn_column": "...", "id_type_column": "...", "id_number_column": "...", "dob_column": "...", "address_column": "...", "city_column": "...", "status_column": "..."}}

Utilise null si aucune colonne ne correspond clairement à un champ."""

    try:
        response = model.invoke(prompt)
        text = response.content.strip()
        json_start = text.find("{")
        json_end = text.rfind("}") + 1
        parsed = json.loads(text[json_start:json_end])
        # Ne garde que les colonnes qui existent réellement dans le fichier
        return {
            key: (parsed.get(key) if parsed.get(key) in available_columns else None)
            for key, _ in REQUIRED_KYC_FIELDS
        }
    except Exception:
        return {key: None for key, _ in REQUIRED_KYC_FIELDS}