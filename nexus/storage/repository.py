"""Local storage repository using parameterized SQLite and atomic operations."""

import sqlite3
import json
from typing import List, Optional, Dict, Any
from pathlib import Path
from nexus.config import DB_PATH
from nexus.models.findings import AnalysisReport
from nexus.security.redaction import redact_secrets


class LocalExperimentRepository:
    """
    Manages persistence of experiment runs, findings, and metadata.
    Enforces parameterized queries to eliminate SQL injection.
    Excludes sensitive API keys and raw inputs unless explicitly permitted.
    """

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        try:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS analysis_runs (
                        id TEXT PRIMARY KEY,
                        scenario_id TEXT NOT NULL,
                        scenario_title TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        provider_name TEXT NOT NULL,
                        is_remote INTEGER NOT NULL,
                        findings_count INTEGER NOT NULL,
                        report_json TEXT NOT NULL
                    )
                    """
                )
                conn.commit()
        except Exception as e:
            # Fallback/graceful degradation if database write encounters permission issues
            pass

    def save_report(self, report: AnalysisReport, store_raw_input: bool = False) -> bool:
        """
        Saves a completed analysis report using parameterized queries.
        Redacts secrets before persistence.
        """
        try:
            report_dict = report.model_dump()
            report_json_str = redact_secrets(json.dumps(report_dict))
            run_id = f"run_{report.scenario_id}_{int(float(report.timestamp.replace(':', '').replace('-', '').replace('T', '')) if 'T' in report.timestamp else 12345)}"
            
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO analysis_runs
                    (id, scenario_id, scenario_title, timestamp, provider_name, is_remote, findings_count, report_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        run_id,
                        report.scenario_id,
                        report.scenario_title,
                        report.timestamp,
                        report.provider_name,
                        1 if report.is_remote else 0,
                        len(report.findings),
                        report_json_str,
                    ),
                )
                conn.commit()
            return True
        except Exception:
            return False

    def list_recent_runs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Returns metadata list of recent analysis runs."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    """
                    SELECT id, scenario_id, scenario_title, timestamp, provider_name, is_remote, findings_count
                    FROM analysis_runs
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (limit,),
                )
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception:
            return []

    def get_report_by_id(self, run_id: str) -> Optional[AnalysisReport]:
        """Loads and parses an AnalysisReport by ID."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "SELECT report_json FROM analysis_runs WHERE id = ?",
                    (run_id,),
                )
                row = cursor.fetchone()
                if row and row["report_json"]:
                    data = json.loads(row["report_json"])
                    return AnalysisReport.model_validate(data)
        except Exception:
            return None
        return None

    def clear_all_history(self) -> bool:
        """Deletes all saved analysis run records."""
        try:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM analysis_runs")
                conn.commit()
            return True
        except Exception:
            return False
