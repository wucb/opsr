from __future__ import annotations

from opsr.models.monitoring import AlertEvent, AlertRule, MetricSample


class InMemoryMetricRepository:
    def __init__(self) -> None:
        self._samples: list[MetricSample] = []

    def add(self, sample: MetricSample) -> None:
        self._samples.append(sample)

    def list_recent(self, limit: int = 200) -> list[MetricSample]:
        return list(self._samples[-limit:])


class InMemoryAlertRuleRepository:
    def __init__(self) -> None:
        self._rules: dict[str, AlertRule] = {}

    def add(self, rule: AlertRule) -> None:
        self._rules[rule.rule_id] = rule

    def list_rules(self) -> list[AlertRule]:
        return list(self._rules.values())

    def get(self, rule_id: str) -> AlertRule | None:
        return self._rules.get(rule_id)


class InMemoryAlertEventRepository:
    def __init__(self) -> None:
        self._events: list[AlertEvent] = []

    def add(self, event: AlertEvent) -> None:
        self._events.append(event)

    def list_events(self, limit: int = 200) -> list[AlertEvent]:
        return list(self._events[-limit:])
