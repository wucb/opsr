from __future__ import annotations

from dataclasses import dataclass

from opsr.models.monitoring import AlertEvent


class Notifier:
    def notify(self, event: AlertEvent) -> None:  # pragma: no cover - interface
        raise NotImplementedError


@dataclass(slots=True)
class LogNotifier(Notifier):
    """Log notifier placeholder."""

    def notify(self, event: AlertEvent) -> None:
        print(f"[ALERT] {event.severity} {event.metric_name}={event.metric_value} {event.message}")


@dataclass(slots=True)
class EmailNotifier(Notifier):
    """Email notifier placeholder."""

    recipient: str

    def notify(self, event: AlertEvent) -> None:
        print(f"[EMAIL] to {self.recipient}: {event.message}")
