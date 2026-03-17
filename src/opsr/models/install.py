from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(slots=True)
class InstallTemplate:
    """Install template for a database or middleware component."""

    component: str
    kind: str
    supported_versions: list[str]
    required_config_keys: list[str]
    default_config: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class InstallRequest:
    """User request to install a component on a target host."""

    component: str
    target_host: str
    config: dict[str, object] = field(default_factory=dict)
    requested_by: str = "system"
    requested_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class InstallStepResult:
    """Execution status of a single install step."""

    step: str
    status: str
    message: str
    started_at: datetime
    finished_at: datetime


@dataclass(slots=True)
class InstallResult:
    """Aggregated result of an install orchestration run."""

    request: InstallRequest
    status: str
    steps: list[InstallStepResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    completed_at: datetime | None = None
