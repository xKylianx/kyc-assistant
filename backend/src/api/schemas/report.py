from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ReportSummary(BaseModel):
    overall_compliance_rate: float = 0.0
    overall_risk_score: float = 0.0
    overall_risk_level: str = "UNKNOWN"
    total_anomalies: int = 0
    active_rows_count: int = 0
    fields_analyzed: Dict[str, Any] = Field(default_factory=dict)


class ReportResponse(BaseModel):
    file_id: str
    file_name: str
    file_size_bytes: int
    extension: str
    delimiter: Optional[str] = None
    row_count: int = 0
    column_count: int = 0
    columns: List[str] = Field(default_factory=list)

    schema: Dict[str, Any] = Field(default_factory=dict)
    country: Dict[str, Any] = Field(default_factory=dict)
    active_lines: Dict[str, Any] = Field(default_factory=dict)
    summary: ReportSummary = Field(default_factory=ReportSummary)
    detailed_results: Dict[str, Any] = Field(default_factory=dict)
    anomalies: Any = Field(default_factory=list)
    executive_summary: Dict[str, Any] = Field(default_factory=dict)
