from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(slots=True)
class ProbeSignal:
    """Raw probe signal consumed by discovery agents."""

    target: str
    open_ports: list[int]
    process_names: list[str]
    dependencies: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Asset:
    """Normalized infrastructure asset model."""

    asset_id: str
    hostname: str
    ip: str
    category: str
    services: list[str]
    tags: dict[str, str] = field(default_factory=dict)
    discovered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class TopologyEdge:
    """Directional relation between two assets."""

    source: str
    target: str
    relation: str


@dataclass(slots=True)
class TopologySnapshot:
    """Topology view for the latest discovery batch."""

    generated_at: datetime
    nodes: list[str]
    edges: list[TopologyEdge]
