import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from opsr.agents.discovery_agent import DiscoveryAgent
from opsr.agents.probe_adapters import ProbeAdapter
from opsr.models.asset import ProbeSignal


class FakeProbeAdapter(ProbeAdapter):
    def __init__(self) -> None:
        self.calls: list[str] = []

    def probe_host(self, ip: str) -> ProbeSignal:
        self.calls.append(ip)
        return ProbeSignal(target=ip, open_ports=[22], process_names=["systemd"])


class MilestoneTwoProbeTests(unittest.TestCase):
    def test_discovery_uses_probe_adapter(self) -> None:
        adapter = FakeProbeAdapter()
        agent = DiscoveryAgent(probe_adapter=adapter)
        signals = agent.sniff_targets(["10.0.0.1", "10.0.0.2"], max_workers=2)

        self.assertEqual(len(adapter.calls), 2)
        self.assertEqual(len(signals), 2)
        self.assertEqual(signals[0].open_ports, [22])


if __name__ == "__main__":
    unittest.main()
