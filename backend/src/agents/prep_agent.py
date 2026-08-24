from __future__ import annotations

from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

import csv
import duckdb
import pandas as pd


class PrepAgent:
    SUPPORTED_EXT = {".csv", ".xlsx", ".json", ".parquet"}
    PANDAS_THRESHOLD_MB = 200  # <= pandas ; > duckdb (sauf xlsx)

    def run(self, prep_state: Dict[str, Any]) -> Dict[str, Any]:
        state = dict(prep_state)

        try:
            file_path = state.get("file_path")
            if not file_path:
                raise ValueError("file_path manquant dans prep_state.")

            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"Fichier introuvable: {file_path}")

            ext = path.suffix.lower()
            if ext not in self.SUPPORTED_EXT:
                raise ValueError(f"Extension non supportée: {ext}")

            size_mb = path.stat().st_size / (1024 * 1024)

            # 1) Délimiteur CSV : user > duckdb sniff > csv.Sniffer > ','
            csv_delimiter_used: Optional[str] = None
            if ext == ".csv":
                user_delim = state.get("csv_delimiter")
                if user_delim:
                    csv_delimiter_used = user_delim
                else:
                    csv_delimiter_used = self._detect_csv_delimiter_duckdb(path) or ","

            # 2) Choix moteur
            if ext == ".xlsx":
                engine_used = "pandas"
            else:
                engine_used = "pandas" if size_mb <= self.PANDAS_THRESHOLD_MB else "duckdb"

            # 3) Profiling
            if engine_used == "pandas":
                profile = self._profile_with_pandas(path, ext, csv_delimiter_used)
            else:
                profile = self._profile_with_duckdb(path, ext, csv_delimiter_used)

            state["dataset_profile"] = profile
            state["prep_meta"] = {
                "engine_used": engine_used,
                "file_size_mb": round(size_mb, 2),
                "threshold_mb": self.PANDAS_THRESHOLD_MB,
                "csv_delimiter_used": csv_delimiter_used if ext == ".csv" else None,
            }
            state["prep_status"] = "success"
            state["prep_error"] = None
            state["prepared_at"] = datetime.utcnow().isoformat()
            return state

        except Exception as e:
            state["prep_status"] = "error"
            state["prep_error"] = str(e)
            state["prepared_at"] = datetime.utcnow().isoformat()
            return state

    # -------------------------------------------------
    # Détection délimiteur CSV
    # -------------------------------------------------
    def _detect_csv_delimiter_duckdb(self, path: Path) -> Optional[str]:
        p = str(path).replace("'", "''")
        con = duckdb.connect(database=":memory:")
        try:
            sniff = con.execute(
                f"SELECT * FROM sniff_csv('{p}', sample_size=20000)"
            ).fetchdf().to_dict(orient="records")[0]

            # clés possibles selon versions DuckDB
            delim = sniff.get("Delimiter") or sniff.get("delim")
            if delim:
                return str(delim)
            return None

        except Exception:
            # fallback Python csv.Sniffer
            try:
                with open(path, "r", encoding="utf-8", newline="") as f:
                    sample = f.read(8192)
                dialect = csv.Sniffer().sniff(sample, delimiters=[",", ";", "\t", "|"])
                return dialect.delimiter
            except Exception:
                return None
        finally:
            con.close()

    # -------------------------------------------------
    # Profiling pandas
    # -------------------------------------------------
    def _profile_with_pandas(self, path: Path, ext: str, delimiter: Optional[str]) -> Dict[str, Any]:
        if ext == ".csv":
            df = pd.read_csv(path,
                            sep=delimiter or ",",
                            engine="python",
                            on_bad_lines="skip",
                            encoding="utf-8",
                            encoding_errors="ignore")
        elif ext == ".xlsx":
            df = pd.read_excel(path)
        elif ext == ".json":
            df = pd.read_json(path)
        elif ext == ".parquet":
            df = pd.read_parquet(path)
        else:
            raise ValueError(f"Extension non gérée par pandas: {ext}")

        row_count = int(len(df))
        columns = [str(c) for c in df.columns.tolist()]
        dtypes = {str(col): str(dtype) for col, dtype in df.dtypes.items()}
        missing_ratio = {
            str(col): (float(df[col].isna().mean()) if row_count > 0 else 0.0)
            for col in df.columns
        }
        sample_rows = df.head(5).where(pd.notna(df), None).to_dict(orient="records")

        return {
            "row_count": row_count,
            "column_count": len(columns),
            "columns": columns,
            "dtypes": dtypes,
            "missing_ratio_by_column": missing_ratio,
            "sample_rows": sample_rows,
        }

    # -------------------------------------------------
    # Profiling duckdb
    # -------------------------------------------------
    def _profile_with_duckdb(self, path: Path, ext: str, delimiter: Optional[str]) -> Dict[str, Any]:
        con = duckdb.connect(database=":memory:")
        try:
            self._create_relation(con, path, ext, delimiter)

            row_count = int(con.execute("SELECT COUNT(*) FROM relation").fetchone()[0])
            schema_rows = con.execute("DESCRIBE relation").fetchall()
            columns: List[str] = [r[0] for r in schema_rows]
            dtypes = {r[0]: r[1] for r in schema_rows}

            sample_df = con.execute("SELECT * FROM relation LIMIT 5").fetchdf()
            sample_rows = sample_df.where(pd.notna(sample_df), None).to_dict(orient="records")

            missing_ratio: Dict[str, float] = {}
            if row_count > 0:
                for col in columns:
                    q = f'''
                        SELECT SUM(CASE WHEN "{col}" IS NULL THEN 1 ELSE 0 END) * 1.0 / COUNT(*)
                        FROM relation
                    '''
                    val = con.execute(q).fetchone()[0]
                    missing_ratio[col] = float(val) if val is not None else 0.0
            else:
                for col in columns:
                    missing_ratio[col] = 0.0

            return {
                "row_count": row_count,
                "column_count": len(columns),
                "columns": columns,
                "dtypes": dtypes,
                "missing_ratio_by_column": missing_ratio,
                "sample_rows": sample_rows,
            }
        finally:
            con.close()

    def _create_relation(
        self,
        con: duckdb.DuckDBPyConnection,
        path: Path,
        ext: str,
        delimiter: Optional[str],
    ) -> None:
        p = str(path).replace("'", "''")

        if ext == ".csv":
            d = (delimiter or ",").replace("'", "''")
            con.execute(
                f"CREATE VIEW relation AS "
                f"SELECT * FROM read_csv_auto('{p}', HEADER=TRUE, delim='{d}')"
            )
        elif ext == ".parquet":
            con.execute(f"CREATE VIEW relation AS SELECT * FROM read_parquet('{p}')")
        elif ext == ".json":
            con.execute(f"CREATE VIEW relation AS SELECT * FROM read_json_auto('{p}')")
        else:
            raise ValueError(f"Extension non gérée par duckdb: {ext}")


prep_agent = PrepAgent()
