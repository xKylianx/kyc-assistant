from __future__ import annotations
from typing import Dict, Any
from sqlalchemy.orm import Session

from src.agents.prep_agent import prep_agent
from src.repositories.uploaded_files_repo import upsert_prep_metadata


class OrchestratorService:
    def run_prep(self, db: Session, prep_state: Dict[str, Any]) -> Dict[str, Any]:
        result = prep_agent.run(prep_state)

        file_id = result.get("file_id") or prep_state.get("file_id")
        if not file_id:
            return result

        prep_meta = result.get("prep_meta", {}) or {}

        repo_result = upsert_prep_metadata(
            db=db,
            file_id=file_id,
            user_id=result.get("user_id") or prep_state.get("user_id"),
            thread_id=result.get("thread_id") or prep_state.get("thread_id"),
            original_filename=result.get("file_name") or prep_state.get("file_name"),
            file_path=result.get("file_path") or prep_state.get("file_path"),
            detected_delimiter=prep_meta.get("csv_delimiter_used"),
            prep_engine=prep_meta.get("engine_used", "unknown"),
            status=(result.get("prep_status") or prep_state.get("prep_status") or "uploaded"),
        )

        result["persisted"] = repo_result
        return result


orchestrator_service = OrchestratorService()
