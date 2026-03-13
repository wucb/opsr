import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from opsr.agents.discovery_agent import DiscoveryAgent
from opsr.models.asset import ProbeSignal
from opsr.services.asset_inventory_service import AssetInventoryService


class MilestoneOneTests(unittest.TestCase):
    def test_discovery_generates_assets_with_classification(self) -> None:
        service = AssetInventoryService()
        assets = service.run_discovery(
            [
                ProbeSignal(target="10.0.0.10", open_ports=[22, 5432], process_names=["postgres"]),
                ProbeSignal(target="10.0.0.11", open_ports=[22, 80], process_names=["nginx"]),
            ]
        )

        categories = {asset.ip: asset.category for asset in assets}
        self.assertEqual(categories["10.0.0.10"], "database")
        self.assertEqual(categories["10.0.0.11"], "middleware")

    def test_asset_tagging_persists_in_repository(self) -> None:
        service = AssetInventoryService()
        assets = service.run_discovery(
            [ProbeSignal(target="10.0.0.12", open_ports=[22], process_names=["python-app"])]
        )

        updated = service.tag_asset(assets[0].asset_id, {"env": "prod", "team": "payments"})
        self.assertEqual(updated.tags["env"], "prod")
        self.assertEqual(updated.tags["team"], "payments")

    def test_topology_tracks_dependencies(self) -> None:
        service = AssetInventoryService()
        assets = service.run_discovery(
            [
                ProbeSignal(
                    target="10.0.0.21",
                    open_ports=[22, 8080],
                    process_names=["api"],
                    dependencies=["10.0.0.22"],
                ),
                ProbeSignal(target="10.0.0.22", open_ports=[22, 3306], process_names=["mysql"]),
            ]
        )

        topology = service.topology()
        expected_source = assets[0].asset_id
        expected_target = assets[1].asset_id
        self.assertEqual(len(topology.nodes), 2)
        self.assertEqual(len(topology.edges), 1)
        self.assertEqual(topology.edges[0].source, expected_source)
        self.assertEqual(topology.edges[0].target, expected_target)
        self.assertEqual(topology.edges[0].relation, "depends_on")

    def test_expand_targets_supports_ip_and_cidr(self) -> None:
        agent = DiscoveryAgent()
        expanded = agent.expand_targets(["10.0.0.5", "10.0.1.0/30"])
        self.assertEqual(expanded, ["10.0.0.5", "10.0.1.1", "10.0.1.2"])

    def test_run_discovery_by_targets_uses_multithread_sniff(self) -> None:
        service = AssetInventoryService()
        assets = service.run_discovery_by_targets(["10.0.2.0/30"], max_workers=4)
        ips = sorted(asset.ip for asset in assets)
        self.assertEqual(ips, ["10.0.2.1", "10.0.2.2"])


if __name__ == "__main__":
    unittest.main()
