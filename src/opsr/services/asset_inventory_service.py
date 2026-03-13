from __future__ import annotations

from datetime import datetime, timezone

from opsr.agents.discovery_agent import DiscoveryAgent
from opsr.models.asset import Asset, ProbeSignal, TopologySnapshot
from opsr.repositories.asset_repository import InMemoryAssetRepository


class AssetInventoryService:
    """Milestone 1 orchestration service for discovery + inventory."""

    def __init__(
        self,
        repository: InMemoryAssetRepository | None = None,
        discovery_agent: DiscoveryAgent | None = None,
    ) -> None:
        self.repository = repository or InMemoryAssetRepository()
        self.discovery_agent = discovery_agent or DiscoveryAgent()
        self._last_signals: list[ProbeSignal] = []

    def run_discovery(self, signals: list[ProbeSignal]) -> list[Asset]:
        assets = self.discovery_agent.discover_assets(signals)
        self.repository.bulk_upsert(assets)
        self._last_signals = signals
        return assets

    def run_discovery_by_targets(self, targets: list[str], max_workers: int = 10) -> list[Asset]:
        signals = self.discovery_agent.sniff_targets(targets=targets, max_workers=max_workers)
        return self.run_discovery(signals)

    def list_assets(self) -> list[Asset]:
        return self.repository.list_assets()

    def tag_asset(self, asset_id: str, tags: dict[str, str]) -> Asset:
        return self.repository.update_tags(asset_id, tags)

    def topology(self) -> TopologySnapshot:
        assets = self.repository.list_assets()
        edges = self.discovery_agent.build_edges(assets, self._last_signals)
        return TopologySnapshot(
            generated_at=datetime.now(timezone.utc),
            nodes=[asset.asset_id for asset in assets],
            edges=edges,
        )
