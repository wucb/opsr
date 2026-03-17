from __future__ import annotations

from opsr.models.monitoring import AlertEvent, AlertRule, MetricSample
from opsr.notifications.notifiers import LogNotifier, Notifier
from opsr.repositories.monitoring_repository import (
    InMemoryAlertEventRepository,
    InMemoryAlertRuleRepository,
    InMemoryMetricRepository,
)


class MonitoringService:
    """Milestone 2.3: metrics ingestion + alert rules + notification."""

    def __init__(
        self,
        metric_repository: InMemoryMetricRepository | None = None,
        rule_repository: InMemoryAlertRuleRepository | None = None,
        event_repository: InMemoryAlertEventRepository | None = None,
        notifiers: list[Notifier] | None = None,
    ) -> None:
        self.metric_repository = metric_repository or InMemoryMetricRepository()
        self.rule_repository = rule_repository or InMemoryAlertRuleRepository()
        self.event_repository = event_repository or InMemoryAlertEventRepository()
        self.notifiers = notifiers or [LogNotifier()]

    def add_rule(self, rule: AlertRule) -> None:
        self.rule_repository.add(rule)

    def list_rules(self) -> list[AlertRule]:
        return self.rule_repository.list_rules()

    def ingest_sample(self, sample: MetricSample) -> list[AlertEvent]:
        self.metric_repository.add(sample)
        events = self._evaluate_rules(sample)
        for event in events:
            self.event_repository.add(event)
            for notifier in self.notifiers:
                notifier.notify(event)
        return events

    def list_events(self, limit: int = 200) -> list[AlertEvent]:
        return self.event_repository.list_events(limit)

    def _evaluate_rules(self, sample: MetricSample) -> list[AlertEvent]:
        events: list[AlertEvent] = []
        for rule in self.rule_repository.list_rules():
            if not rule.enabled or rule.metric_name != sample.name:
                continue
            if not self._compare(sample.value, rule.comparator, rule.threshold):
                continue
            message = rule.description or f"{rule.metric_name} {rule.comparator} {rule.threshold}"
            events.append(
                AlertEvent(
                    rule_id=rule.rule_id,
                    metric_name=sample.name,
                    metric_value=sample.value,
                    status="triggered",
                    severity=rule.severity,
                    labels={**rule.labels, **sample.labels},
                    message=message,
                )
            )
        return events

    @staticmethod
    def _compare(value: float, comparator: str, threshold: float) -> bool:
        if comparator == ">":
            return value > threshold
        if comparator == ">=":
            return value >= threshold
        if comparator == "<":
            return value < threshold
        if comparator == "<=":
            return value <= threshold
        if comparator == "==":
            return value == threshold
        return False
