import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from opsr.services.runbook_service import RunbookService


class MilestoneFourRunbookTests(unittest.TestCase):
    def test_suggest_and_execute(self) -> None:
        service = RunbookService()
        runbook = service.suggest_runbook("please restart redis")
        self.assertIsNotNone(runbook)

        approval = service.request_approval(runbook.runbook_id, "tester")
        decided = service.decide_approval(approval.approval_id, approved=True, decided_by="lead")
        self.assertEqual(decided.status, "approved")

        execution = service.execute_runbook(runbook.runbook_id, "tester", approved_by="lead")
        self.assertEqual(execution.status, "success")
        self.assertTrue(execution.logs)


if __name__ == "__main__":
    unittest.main()
