import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from opsr.services.compliance_service import ComplianceService


class MilestoneFiveComplianceTests(unittest.TestCase):
    def test_baseline_checks_and_drift(self) -> None:
        service = ComplianceService()
        results = service.run_checks(
            {
                "ssh_enabled": True,
                "backup_enabled": False,
                "patch_level": "0.9.0",
            }
        )
        self.assertEqual(len(results), 3)
        self.assertTrue(any(r.status == "fail" for r in results))

        drift = service.detect_drift(
            resource_id="host-1",
            desired={"ntp": True},
            current={"ntp": False},
        )
        self.assertEqual(drift.status, "drift")


if __name__ == "__main__":
    unittest.main()
