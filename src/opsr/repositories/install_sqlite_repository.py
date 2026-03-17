from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

from opsr.models.install import InstallRequest, InstallResult, InstallStepResult


class SqliteInstallResultRepository:
    """SQLite-backed storage for install runs."""

    def __init__(self, db_path: str = "opsr.db") -> None:
        self.db_path = db_path
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS install_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    status TEXT NOT NULL,
                    request_json TEXT NOT NULL,
                    steps_json TEXT NOT NULL,
                    errors_json TEXT NOT NULL,
                    completed_at TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def add(self, result: InstallResult) -> None:
        payload = {
            "request": self._serialize_request(result.request),
            "steps": [self._serialize_step(step) for step in result.steps],
            "errors": list(result.errors),
            "completed_at": (result.completed_at or datetime.now(timezone.utc)).isoformat(),
        }
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO install_results (status, request_json, steps_json, errors_json, completed_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    result.status,
                    json.dumps(payload["request"], ensure_ascii=False),
                    json.dumps(payload["steps"], ensure_ascii=False),
                    json.dumps(payload["errors"], ensure_ascii=False),
                    payload["completed_at"],
                    now,
                ),
            )
            conn.commit()

    def list_results(self) -> list[InstallResult]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT status, request_json, steps_json, errors_json, completed_at
                FROM install_results
                ORDER BY id DESC
                """
            ).fetchall()

        results: list[InstallResult] = []
        for status, request_json, steps_json, errors_json, completed_at in rows:
            request = self._deserialize_request(json.loads(request_json))
            steps = [self._deserialize_step(step) for step in json.loads(steps_json)]
            errors = json.loads(errors_json)
            results.append(
                InstallResult(
                    request=request,
                    status=status,
                    steps=steps,
                    errors=errors,
                    completed_at=datetime.fromisoformat(completed_at),
                )
            )
        return results

    @staticmethod
    def _serialize_request(request: InstallRequest) -> dict[str, object]:
        return {
            "component": request.component,
            "target_host": request.target_host,
            "config": request.config,
            "requested_by": request.requested_by,
            "requested_at": request.requested_at.isoformat(),
        }

    @staticmethod
    def _serialize_step(step: InstallStepResult) -> dict[str, object]:
        return {
            "step": step.step,
            "status": step.status,
            "message": step.message,
            "started_at": step.started_at.isoformat(),
            "finished_at": step.finished_at.isoformat(),
        }

    @staticmethod
    def _deserialize_request(payload: dict[str, object]) -> InstallRequest:
        return InstallRequest(
            component=str(payload["component"]),
            target_host=str(payload["target_host"]),
            config=dict(payload.get("config", {})),
            requested_by=str(payload.get("requested_by", "system")),
            requested_at=datetime.fromisoformat(str(payload["requested_at"])),
        )

    @staticmethod
    def _deserialize_step(payload: dict[str, object]) -> InstallStepResult:
        return InstallStepResult(
            step=str(payload["step"]),
            status=str(payload["status"]),
            message=str(payload["message"]),
            started_at=datetime.fromisoformat(str(payload["started_at"])),
            finished_at=datetime.fromisoformat(str(payload["finished_at"])),
        )
