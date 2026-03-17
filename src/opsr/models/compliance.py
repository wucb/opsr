from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(slots=True)
class BaselineCheck:
    check_id: str
    description: str
    expected: dict[str, object]
    severity: str = "medium"


@dataclass(slots=True)
class CheckResult:
    check_id: str
    status: str
    message: str
    severity: str
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class DriftResult:
    resource_id: str
    status: str
    differences: dict[str, object]
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
