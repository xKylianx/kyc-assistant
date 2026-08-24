from typing import Any, Dict, Optional
from pydantic import BaseModel


class ApiError(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ApiResponse(BaseModel):
    status: str  # "ok" | "error"
    data: Optional[Dict[str, Any]] = None
    meta: Optional[Dict[str, Any]] = None
    error: Optional[ApiError] = None