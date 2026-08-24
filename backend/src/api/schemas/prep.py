from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class PrepStateIn(BaseModel):
    """
    Minimal state required to launch the preparation agent.

    user_id/thread_id are optional because the upload endpoint can create
    them when the client does not provide them.
    """

    thread_id: Optional[str] = Field(default=None, min_length=1)
    user_id: Optional[str] = Field(default=None, min_length=1)
    file_id: str = Field(..., min_length=1)
    file_name: str = Field(..., min_length=1)
    file_path: str = Field(..., min_length=1)
    prep_status: Literal["uploaded", "success", "error"] = "uploaded"
    prep_error: Optional[str] = None

    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("file_path cannot be empty")
        return value


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
