from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(slots=True)
class RunbookStep:
    step_id: str
    description: str
    command: str


@dataclass(slots=True)
class Runbook:
    runbook_id: str
    name: str
    description: str
    steps: list[RunbookStep] = field(default_factory=list)
    requires_approval: bool = True


@dataclass(slots=True)
class ApprovalRequest:
    approval_id: str
    runbook_id: str
    requested_by: str
    status: str
    requested_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    decided_at: datetime | None = None
    decided_by: str | None = None


@dataclass(slots=True)
class RunbookExecution:
    execution_id: str
    runbook_id: str
    status: str
    requested_by: str
    approved_by: str | None = None
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = None
    logs: list[str] = field(default_factory=list)
