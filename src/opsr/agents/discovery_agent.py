from __future__ import annotations

import hashlib
from concurrent.futures import ThreadPoolExecutor
from ipaddress import ip_address, ip_network

from opsr.agents.probe_adapters import ProbeAdapter, SimulatedProbeAdapter
from opsr.models.asset import Asset, ProbeSignal, TopologyEdge

DB_PORTS = {3306: "mysql", 5432: "postgres", 6379: "redis", 27017: "mongodb"}
MIDDLEWARE_PORTS = {9092: "kafka", 5672: "rabbitmq", 80: "nginx", 443: "nginx"}


class DiscoveryAgent:
    """Agent responsible for subnet/IP sniffing, classification, and topology."""

    def __init__(self, probe_adapter: ProbeAdapter | None = None) -> None:
        self.probe_adapter = probe_adapter or SimulatedProbeAdapter()

    @staticmethod
    def _asset_id(hostname: str, ip: str) -> str:
        digest = hashlib.sha1(f"{hostname}-{ip}".encode("utf-8")).hexdigest()
        return digest[:12]

    @staticmethod
    def _classify(open_ports: list[int]) -> str:
        if any(port in DB_PORTS for port in open_ports):
            return "database"
        if any(port in MIDDLEWARE_PORTS for port in open_ports):
            return "middleware"
        return "server"

    @staticmethod
    def _service_names(signal: ProbeSignal) -> list[str]:
        names: list[str] = []
        for port in signal.open_ports:
            if port in DB_PORTS:
                names.append(DB_PORTS[port])
            elif port in MIDDLEWARE_PORTS:
                names.append(MIDDLEWARE_PORTS[port])
        names.extend(signal.process_names)
        return list(dict.fromkeys(names))

    def expand_targets(self, targets: list[str]) -> list[str]:
        """Accept single IPs and CIDRs, then return deduplicated host IP list."""
        expanded: list[str] = []
        for target in targets:
            value = target.strip()
            if not value:
                continue
            if "/" in value:
                net = ip_network(value, strict=False)
                expanded.extend(str(host) for host in net.hosts())
            else:
                expanded.append(str(ip_address(value)))
        return list(dict.fromkeys(expanded))

    def sniff_targets(self, targets: list[str], max_workers: int = 10) -> list[ProbeSignal]:
        """Use thread pool to sniff input IPs/CIDRs."""
        ips = self.expand_targets(targets)
        workers = max(1, min(max_workers, len(ips) or 1))
        with ThreadPoolExecutor(max_workers=workers) as executor:
            signals = list(executor.map(self.probe_adapter.probe_host, ips))
        return signals

    def discover_assets(self, signals: list[ProbeSignal]) -> list[Asset]:
        assets: list[Asset] = []
        for signal in signals:
            ip = str(ip_address(signal.target))
            hostname = f"host-{ip.replace('.', '-')}"
            assets.append(
                Asset(
                    asset_id=self._asset_id(hostname, ip),
                    hostname=hostname,
                    ip=ip,
                    category=self._classify(signal.open_ports),
                    services=self._service_names(signal),
                )
            )
        return assets

    def build_edges(self, assets: list[Asset], signals: list[ProbeSignal]) -> list[TopologyEdge]:
        indexed = {asset.ip: asset for asset in assets}
        edges: list[TopologyEdge] = []
        for signal in signals:
            source = indexed.get(signal.target)
            if source is None:
                continue
            for dependency in signal.dependencies:
                target = indexed.get(dependency)
                if target is None:
                    continue
                edges.append(
                    TopologyEdge(source=source.asset_id, target=target.asset_id, relation="depends_on")
                )
        return edges
