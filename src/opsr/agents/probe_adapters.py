from __future__ import annotations

import socket
from dataclasses import dataclass

from opsr.models.asset import ProbeSignal

DEFAULT_PORTS = [22, 80, 443, 3306, 5432, 6379, 27017, 5672, 9092]

PORT_PROCESS_MAP = {
    22: "sshd",
    80: "nginx",
    443: "nginx",
    3306: "mysql",
    5432: "postgres",
    6379: "redis",
    27017: "mongodb",
    5672: "rabbitmq",
    9092: "kafka",
}


class ProbeAdapter:
    """Abstract probe adapter."""

    def probe_host(self, ip: str) -> ProbeSignal:  # pragma: no cover - interface
        raise NotImplementedError


@dataclass(slots=True)
class TcpPortProbeAdapter(ProbeAdapter):
    """TCP connect scan for common ports."""

    ports: list[int] = None
    timeout_seconds: float = 0.3

    def __post_init__(self) -> None:
        if self.ports is None:
            self.ports = list(DEFAULT_PORTS)

    def probe_host(self, ip: str) -> ProbeSignal:
        open_ports: list[int] = []
        process_names: list[str] = []
        for port in self.ports:
            if self._is_port_open(ip, port):
                open_ports.append(port)
                process = PORT_PROCESS_MAP.get(port)
                if process:
                    process_names.append(process)
        return ProbeSignal(
            target=ip,
            open_ports=open_ports,
            process_names=list(dict.fromkeys(process_names)),
            dependencies=[],
        )

    def _is_port_open(self, ip: str, port: int) -> bool:
        try:
            with socket.create_connection((ip, port), timeout=self.timeout_seconds):
                return True
        except (OSError, TimeoutError):
            return False


class SimulatedProbeAdapter(ProbeAdapter):
    """Demo probe adapter used for milestone-1 mock sniffing."""

    def probe_host(self, ip: str) -> ProbeSignal:
        last = int(ip.split(".")[-1])
        open_ports = [22]
        process_names = ["systemd"]
        dependencies: list[str] = []

        if last % 3 == 0:
            open_ports.append(5432)
            process_names.append("postgres")
        elif last % 3 == 1:
            open_ports.append(80)
            process_names.append("nginx")
        else:
            open_ports.append(6379)
            process_names.append("redis")

        if last > 1:
            dependencies = [".".join(ip.split(".")[:-1] + [str(last - 1)])]

        return ProbeSignal(
            target=ip,
            open_ports=open_ports,
            process_names=process_names,
            dependencies=dependencies,
        )
