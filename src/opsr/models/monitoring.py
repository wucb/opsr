from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(slots=True)
class MetricSample:
    name: str
    value: float
    labels: dict[str, str] = field(default_factory=dict)
    recorded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class AlertRule:
    rule_id: str
    metric_name: str
    comparator: str
    threshold: float
    severity: str
    description: str = ""
    labels: dict[str, str] = field(default_factory=dict)
    enabled: bool = True


@dataclass(slots=True)
class AlertEvent:
    rule_id: str
    metric_name: str
    metric_value: float
    status: str
    severity: str
    labels: dict[str, str] = field(default_factory=dict)
    message: str = ""
    triggered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
