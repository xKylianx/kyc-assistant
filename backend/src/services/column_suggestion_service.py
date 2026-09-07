from __future__ import annotations

import json
import os
from typing import Dict, List, Optional, TypedDict

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


class ColumnSuggestionResult(TypedDict):
    columns: Dict[str, Optional[str]]
    reasoning: Dict[str, str]


def suggest_column_mapping(
    file_path: str,
    delimiter: str,
    available_columns: List[str],
) -> ColumnSuggestionResult:
    """
    Propose un mapping colonne CSV -> champ KYC via LLM, avec une
    justification par champ pour que l'utilisateur puisse valider en
    connaissance de cause plutôt que de faire confiance à une boîte noire.
    """
    con = duckdb.connect()
    try:
        query = (
            f"SELECT * FROM read_csv_auto('{file_path}', delim='{delimiter}', "
            f"header=True, ignore_errors=True) LIMIT 10"
        )
        sample_df = con.execute(query).fetchdf().astype(str)
        sample_rows = sample_df.to_dict(orient="records")
    except Exception:
        sample_rows = []
    finally:
        con.close()

    fields_description = "\n".join(f"- {key}: {label}" for key, label in REQUIRED_KYC_FIELDS)

    prompt = f"""Tu es un analyste de données KYC. Associe chaque champ requis à la colonne CSV la plus pertinente, et justifie brièvement chaque choix.

Champs KYC requis :
{fields_description}

Colonnes disponibles dans le fichier :
{json.dumps(available_columns, indent=2)}

Échantillon de données (10 premières lignes) :
{json.dumps(sample_rows, indent=2)}

Réponds UNIQUEMENT en JSON valide, sans texte autour, au format exact :
{{
  "nom_column": {{"column": "nom_exact_colonne_ou_null", "reasoning": "Justification en une phrase courte"}},
  "prenom_column": {{"column": "...", "reasoning": "..."}},
  "msisdn_column": {{"column": "...", "reasoning": "..."}},
  "id_type_column": {{"column": "...", "reasoning": "..."}},
  "id_number_column": {{"column": "...", "reasoning": "..."}},
  "dob_column": {{"column": "...", "reasoning": "..."}},
  "address_column": {{"column": "...", "reasoning": "..."}},
  "city_column": {{"column": "...", "reasoning": "..."}},
  "status_column": {{"column": "...", "reasoning": "..."}}
}}

Si une seule colonne combine nom ET prénom (ex: "nom_prenom_in"), utilise cette même colonne pour nom_column ET prenom_column, en l'expliquant dans le reasoning.
Utilise column: null avec une reasoning expliquant pourquoi, si aucune colonne ne correspond clairement à un champ."""

    empty_result: ColumnSuggestionResult = {
        "columns": {key: None for key, _ in REQUIRED_KYC_FIELDS},
        "reasoning": {key: "Aucune suggestion disponible" for key, _ in REQUIRED_KYC_FIELDS},
    }

    try:
        response = model.invoke(prompt)
        text = response.content.strip()
        json_start = text.find("{")
        json_end = text.rfind("}") + 1
        parsed = json.loads(text[json_start:json_end])

        columns: Dict[str, Optional[str]] = {}
        reasoning: Dict[str, str] = {}
        for key, _ in REQUIRED_KYC_FIELDS:
            entry = parsed.get(key) or {}
            suggested_column = entry.get("column")
            columns[key] = suggested_column if suggested_column in available_columns else None
            reasoning[key] = entry.get("reasoning") or "Aucune justification fournie"

        return {"columns": columns, "reasoning": reasoning}
    except Exception as e:
        print(f"⚠️ Column suggestion LLM error: {e}")
        return empty_result