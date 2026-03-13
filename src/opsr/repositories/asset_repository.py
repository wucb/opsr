from __future__ import annotations

from dataclasses import replace

from opsr.models.asset import Asset


class InMemoryAssetRepository:
    """In-memory repository for milestone-1 asset inventory."""

    def __init__(self) -> None:
        self._assets: dict[str, Asset] = {}

    def upsert(self, asset: Asset) -> None:
        self._assets[asset.asset_id] = replace(asset)

    def bulk_upsert(self, assets: list[Asset]) -> None:
        for asset in assets:
            self.upsert(asset)

    def list_assets(self) -> list[Asset]:
        return [replace(asset) for asset in self._assets.values()]

    def update_tags(self, asset_id: str, tags: dict[str, str]) -> Asset:
        current = self._assets[asset_id]
        current.tags.update(tags)
        self._assets[asset_id] = current
        return replace(current)
