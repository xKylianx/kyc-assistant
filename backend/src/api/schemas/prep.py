# schemas/prep.py
from __future__ import annotations

from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator


class PrepStateIn(BaseModel):
    thread_id: str = Field(..., min_length=1, description="Identifiant du thread")
    user_id: str = Field(..., min_length=1, description="Identifiant utilisateur")
    file_id: str = Field(..., min_length=1, description="Identifiant du fichier")
    file_name: str = Field(..., min_length=1, description="Nom du fichier")
    file_path: str = Field(..., min_length=1, description="Chemin absolu/local du fichier")
    prep_status: Literal["uploaded", "success", "error"] = Field(
        ..., description="Statut de préparation"
    )
    prep_error: Optional[str] = Field(None, description="Message d'erreur éventuel")

    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, v: str) -> str:
        # Validation légère (non bloquante OS)
        # On évite juste les chaînes vides ou absurdes
        v = v.strip()
        if not v:
            raise ValueError("file_path cannot be empty")
        return v


class PrepRequest(BaseModel):
    prep_state: PrepStateIn = Field(..., description="État d'entrée pour l'agent de préparation")
