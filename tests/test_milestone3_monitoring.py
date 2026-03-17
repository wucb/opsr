import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from opsr.models.monitoring import AlertRule, MetricSample
from opsr.services.monitoring_service import MonitoringService


class MilestoneThreeMonitoringTests(unittest.TestCase):
    def test_threshold_rule_triggers(self) -> None:
        service = MonitoringService()
        service.add_rule(
            AlertRule(
                rule_id="cpu_high",
                metric_name="cpu_usage",
                comparator=">",
                threshold=80,
                severity="critical",
                description="cpu usage high",
            )
        )

        events = service.ingest_sample(MetricSample(name="cpu_usage", value=92))
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].rule_id, "cpu_high")


if __name__ == "__main__":
    unittest.main()
