from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class PrepStateIn(BaseModel):
    thread_id: Optional[str] = Field(None, description="Identifiant du thread")
    user_id: Optional[str] = Field(None, description="Identifiant utilisateur")
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
        v = v.strip()
        if not v:
            raise ValueError("file_path cannot be empty")
        return v

class PrepRequest(BaseModel):
    prep_state: PrepStateIn


class PrepDatasetProfile(BaseModel):
    row_count: int = 0
    column_count: int = 0
    columns: List[str] = Field(default_factory=list)
    dtypes: Dict[str, str] = Field(default_factory=dict)
    missing_ratio_by_column: Dict[str, float] = Field(default_factory=dict)
    sample_rows: List[Dict[str, Any]] = Field(default_factory=list)


class PrepResponse(BaseModel):
    status: str
    data: Dict[str, Any]
    meta: Dict[str, Any] = Field(default_factory=dict)
