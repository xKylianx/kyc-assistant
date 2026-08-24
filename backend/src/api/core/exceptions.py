from __future__ import annotations
from typing import Any, Dict, Optional


class AppError(Exception):
    code = "APP_ERROR"
    message = "Application error"

    def __init__(self, message: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message or self.message)
        self.message = message or self.message
        self.details = details or {}


class NotFoundError(AppError):
    code = "NOT_FOUND"
    message = "Resource not found"


class ValidationError(AppError):
    code = "VALIDATION_ERROR"
    message = "Invalid input"


class ProcessingError(AppError):
    code = "PROCESSING_ERROR"
    message = "Processing failed"