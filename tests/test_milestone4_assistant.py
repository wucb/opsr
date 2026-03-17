import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from opsr.services.assistant_service import AssistantService


class MilestoneFourAssistantTests(unittest.TestCase):
    def test_triage_suggests_runbook(self) -> None:
        service = AssistantService()
        response = service.triage("请帮我重启 redis", "tester")
        intents = {suggestion.intent for suggestion in response.suggestions}
        self.assertIn("runbook", intents)


if __name__ == "__main__":
    unittest.main()
